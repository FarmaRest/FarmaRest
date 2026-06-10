# ─────────────────────────────────────────────────────────────────────────────
# CAPA: SERVICE — Módulo de Productos
# Responsabilidad: Contiene las reglas de negocio del catálogo. Coordina entre
# la API y los repositorios. Aquí viven las validaciones, el cálculo automático
# de 'activo' según stock + vencimiento, y el orden de persistencia
# (producto → lote → presentaciones). No escribe SQL ni responde HTTP.
# ─────────────────────────────────────────────────────────────────────────────

from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.repositories.productos import (
    CategoriaRepositorio, LaboratorioRepositorio,
    ProductoRepositorio, LoteRepositorio, PresentacionRepositorio,
)
from app.domain.productos import Categoria, Laboratorio, Producto, Lote, Presentacion


class ProductoService:
    """
    Servicio principal del módulo de productos.
    Cubre HU-PROD-02:
    - registrar_producto: crea producto + lote + presentaciones aplicando las
      reglas de vencimiento (>15 días) y de cálculo automático de 'activo'.
    - actualizar_producto: modifica campos del producto y recalcula 'activo'
      cuando cambia el stock, consultando el lote vigente.
    """

    # Regla de negocio: un producto solo puede publicarse si su lote vigente
    # tiene más de 15 días para vencerse. Si esta constante cambia en el
    # futuro (ej: 30 días), solo se ajusta aquí
    DIAS_MINIMOS_VENCIMIENTO = 15

    def __init__(self, db: Session):
        # Una sola sesión compartida entre todos los repos del módulo
        self.db = db
        self.producto_repo     = ProductoRepositorio(db)
        self.lote_repo         = LoteRepositorio(db)
        self.presentacion_repo = PresentacionRepositorio(db)
        self.categoria_repo    = CategoriaRepositorio(db)
        self.laboratorio_repo  = LaboratorioRepositorio(db)

    def _vencimiento_valido(self, fecha_vencimiento: date) -> bool:
        # True si la fecha está más de 15 días en el futuro desde hoy.
        # Es la regla clave de toda la HU: producto cerca de vencer no se publica
        limite = date.today() + timedelta(days=self.DIAS_MINIMOS_VENCIMIENTO)
        return fecha_vencimiento > limite

    # ── Registro ──────────────────────────────────────────────────────────

    def registrar_producto(self, datos: dict, solicitante_rol: str):
        """
        HU-PROD-02 caso 1: crea un producto con su lote inicial y presentaciones.
        Retorna una tupla (producto, lote, categoria, laboratorio) para que
        la capa API pueda armar la respuesta sin volver a consultar la BD.
        """

        # Regla: solo administradores pueden registrar productos
        if solicitante_rol != "administrador":
            raise PermissionError("FORBIDDEN")

        # Validación de precio antes de tocar la BD (falla rápido)
        if datos["precio"] <= 0:
            raise ValueError("INVALID_PRICE")

        # Validación de vencimiento del lote inicial (regla 15 días)
        lote_data = datos["lote"]
        if not self._vencimiento_valido(lote_data["fechaVencimiento"]):
            raise ValueError("PRODUCT_NEAR_EXPIRY")

        # Código de lote no puede estar duplicado en el sistema
        if self.lote_repo.buscar_por_codigo(lote_data["codigoLote"]):
            raise ValueError("LOTE_ALREADY_EXISTS")

        # Categoría y laboratorio deben existir: NO se crean automáticamente
        # (decisión tomada en el plan de la HU)
        categoria = self.categoria_repo.buscar_por_codigo(datos["categoria"]["codigo"])
        if not categoria:
            raise LookupError("CATEGORY_NOT_FOUND")

        laboratorio = self.laboratorio_repo.buscar_por_nombre(datos["laboratorio"]["nombre"])
        if not laboratorio:
            raise LookupError("LAB_NOT_FOUND")

        # Cálculo automático de 'activo': el sistema decide, no se confía
        # en el valor que mande el cliente. Si stock = 0 → siempre inactivo,
        # aunque el vencimiento esté OK. Si stock > 0 y vencimiento OK → activo
        stock = datos["stock"]
        activo = stock > 0  # vencimiento ya fue validado arriba

        # Construcción y persistencia del producto
        producto = Producto(
            nombre=datos["nombre"],
            descripcion=datos.get("descripcion"),
            precio=datos["precio"],
            aplica_iva=datos.get("aplica_iva", False),
            stock=stock,
            activo=activo,
            categoria_id=categoria.id,
            laboratorio_id=laboratorio.id,
        )
        producto_guardado = self.producto_repo.guardar(producto)

        # Lote inicial. Su id se obtiene tras el commit, dependiente del producto
        lote = Lote(
            producto_id=producto_guardado.id,
            codigo_lote=lote_data["codigoLote"],
            cantidad=lote_data["cantidad"],
            fecha_vencimiento=lote_data["fechaVencimiento"],
        )
        lote_guardado = self.lote_repo.guardar(lote)

        # Presentaciones (opcionales). Se guardan todas o ninguna en un solo commit
        if datos.get("presentaciones"):
            presentaciones = [
                Presentacion(
                    producto_id=producto_guardado.id,
                    tipo=p["tipo"],
                    cantidad=p["cantidad"],
                    unidad=p["unidad"],
                )
                for p in datos["presentaciones"]
            ]
            self.presentacion_repo.guardar_todas(presentaciones)

        return producto_guardado, lote_guardado, categoria, laboratorio

    # ── Actualización ─────────────────────────────────────────────────────

    def actualizar_producto(self, producto_id: str, datos: dict, solicitante_rol: str) -> Producto:
        """
        HU-PROD-02 caso 5: actualiza campos del producto.
        Solo modifica los campos enviados; el resto queda intacto.
        Si llega 'stock', recalcula 'activo' consultando el lote vigente.
        """

        # Regla: solo administradores pueden actualizar productos
        if solicitante_rol != "administrador":
            raise PermissionError("FORBIDDEN")

        producto = self.producto_repo.buscar_por_id(producto_id)
        if not producto:
            raise LookupError("PRODUCT_NOT_FOUND")

        # Se arma un diccionario solo con los campos enviados explícitamente
        campos = {}

        # Campos simples: solo se copian si vienen en el body
        for campo in ("nombre", "descripcion"):
            if datos.get(campo) is not None:
                campos[campo] = datos[campo]

        # Precio: si viene, se valida > 0 antes de aceptarlo
        if datos.get("precio") is not None:
            if datos["precio"] <= 0:
                raise ValueError("INVALID_PRICE")
            campos["precio"] = datos["precio"]

        # Stock: si viene, se valida >= 0 y se recalcula 'activo' automáticamente
        # Este bloque es la lógica clave de la regla de activación dinámica
        if datos.get("stock") is not None:
            nuevo_stock = datos["stock"]
            if nuevo_stock < 0:
                raise ValueError("INVALID_STOCK")
            campos["stock"] = nuevo_stock

            if nuevo_stock == 0:
                # Stock cero → producto siempre inactivo, sin importar lote
                campos["activo"] = False
            else:
                # Stock > 0 → activo solo si hay lote vigente con > 15 días
                lote_vigente = self.lote_repo.buscar_lote_vigente_por_producto(producto_id)
                if lote_vigente and self._vencimiento_valido(lote_vigente.fecha_vencimiento):
                    campos["activo"] = True
                else:
                    # Sin lote vigente o lote por vencer en menos de 15 días
                    campos["activo"] = False
        elif datos.get("activo") is not None:
            # Solo se respeta el 'activo' del body si NO se está tocando el stock,
            # porque cuando el stock cambia el sistema lo recalcula automáticamente
            campos["activo"] = datos["activo"]

        if datos.get("aplica_iva") is not None:
            campos["aplica_iva"] = datos["aplica_iva"]

        return self.producto_repo.actualizar(producto, campos)

    # ── Creación de maestros (categorías y laboratorios) ──────────────────
    # Fuera del alcance estricto de la HU-PROD-02, pero necesario para que
    # el admin pueda poblar los catálogos desde Swagger sin tocar SQL a mano

    def consultar_catalogo(self, categoria: str = None, laboratorio: str = None) -> list:
        return self.producto_repo.listar_activos(
            categoria_codigo=categoria, laboratorio_nombre=laboratorio
        )

    def consultar_por_id(self, producto_id: str, es_admin: bool = False):
        producto = self.producto_repo.buscar_por_id(producto_id)
        if not producto:
            raise LookupError("PRODUCT_NOT_FOUND")
        # Los clientes no pueden ver productos inactivos — ni saber que existen
        if not producto.activo and not es_admin:
            raise LookupError("PRODUCT_NOT_FOUND")
        return producto

    def listar_categorias(self) -> list:
        return self.categoria_repo.listar_todas()

    def listar_laboratorios(self) -> list:
        return self.laboratorio_repo.listar_todos()

    def agregar_lote(self, producto_id: str, datos: dict, solicitante_rol: str):
        """Agrega un nuevo lote a un producto existente y recalcula su stock y activo."""
        if solicitante_rol != "administrador":
            raise PermissionError("FORBIDDEN")

        producto = self.producto_repo.buscar_por_id(producto_id)
        if not producto:
            raise LookupError("PRODUCT_NOT_FOUND")

        if not self._vencimiento_valido(datos["fechaVencimiento"]):
            raise ValueError("PRODUCT_NEAR_EXPIRY")

        if self.lote_repo.buscar_por_codigo(datos["codigoLote"]):
            raise ValueError("LOTE_ALREADY_EXISTS")

        lote = Lote(
            producto_id=producto.id,
            codigo_lote=datos["codigoLote"],
            cantidad=datos["cantidad"],
            fecha_vencimiento=datos["fechaVencimiento"],
        )
        lote_guardado = self.lote_repo.guardar(lote)

        # El stock del producto aumenta con la cantidad del nuevo lote
        nuevo_stock = producto.stock + datos["cantidad"]
        lote_vigente = self.lote_repo.buscar_lote_vigente_por_producto(str(producto.id))
        activo = nuevo_stock > 0 and lote_vigente is not None and self._vencimiento_valido(lote_vigente.fecha_vencimiento)
        self.producto_repo.actualizar(producto, {"stock": nuevo_stock, "activo": activo})

        return lote_guardado, producto

    def listar_lotes(self, producto_id: str) -> list:
        producto = self.producto_repo.buscar_por_id(producto_id)
        if not producto:
            raise LookupError("PRODUCT_NOT_FOUND")
        return self.lote_repo.listar_por_producto(producto_id)

    def listar_presentaciones(self, producto_id: str) -> list:
        producto = self.producto_repo.buscar_por_id(producto_id)
        if not producto:
            raise LookupError("PRODUCT_NOT_FOUND")
        return self.presentacion_repo.listar_por_producto(producto_id)

    def actualizar_presentacion(self, presentacion_id: str, datos: dict, solicitante_rol: str):
        """Actualiza tipo, cantidad o unidad de una presentación existente."""
        if solicitante_rol != "administrador":
            raise PermissionError("FORBIDDEN")

        presentacion = self.presentacion_repo.buscar_por_id(presentacion_id)
        if not presentacion:
            raise LookupError("PRESENTACION_NOT_FOUND")

        campos = {k: v for k, v in datos.items() if v is not None}
        return self.presentacion_repo.actualizar(presentacion, campos)

    # ── HU-PROD-03: Inventario FEFO ───────────────────────────────────────

    def verificar_stock_disponible(self, producto_id: str, cantidad_solicitada: int) -> None:
        """
        Llamado por CarritoService antes de agregar un producto al carrito.
        Lanza ValueError con código INSUFFICIENT_STOCK si el stock no alcanza.
        El mensaje incluye el stock real y el nombre del producto para que
        CarritoService pueda armar la respuesta HTTP 400 con detalle.
        """
        producto = self.producto_repo.buscar_por_id(producto_id)
        if not producto:
            raise LookupError("PRODUCT_NOT_FOUND")
        if producto.stock < cantidad_solicitada:
            raise ValueError(f"INSUFFICIENT_STOCK|{producto.stock}|{producto.nombre}")

    def descontar_stock_fefo(self, producto_id: str, cantidad_a_descontar: int) -> None:
        """
        Llamado por PedidoService al confirmar un pedido, dentro de una
        transacción única que abarca todos los ítems del pedido.

        Descuenta 'cantidad_a_descontar' del producto comenzando por el lote
        con fecha_vencimiento más próxima (FEFO). Si ese lote no alcanza,
        continúa con el siguiente en orden de vencimiento.

        Tras el descuento recalcula el stock total del producto sumando las
        cantidades reales de todos sus lotes, y desactiva el producto si el
        stock llega a cero.

        Los updates de lotes usan flush() (sin commit) para que todo quede
        dentro de la misma transacción. El commit final lo hace el actualizar()
        del producto al terminar, garantizando atomicidad: si cualquier paso
        falla, ningún lote ni el producto quedan modificados.
        """
        producto = self.producto_repo.buscar_por_id(producto_id)
        if not producto:
            raise LookupError("PRODUCT_NOT_FOUND")

        if producto.stock < cantidad_a_descontar:
            raise ValueError(f"INSUFFICIENT_STOCK|{producto.stock}|{producto.nombre}")

        lotes = self.lote_repo.listar_con_stock_por_producto(str(producto.id))

        restante = cantidad_a_descontar
        for lote in lotes:
            if restante <= 0:
                break
            descontar = min(lote.cantidad, restante)
            self.lote_repo.actualizar_cantidad(lote, lote.cantidad - descontar)
            restante -= descontar

        # Recalcula el stock sumando las cantidades reales de todos los lotes
        # (incluyendo los que acaban de ser modificados vía flush)
        todos_los_lotes = self.lote_repo.listar_por_producto(str(producto.id))
        nuevo_stock = sum(l.cantidad for l in todos_los_lotes)
        activo = nuevo_stock > 0

        # actualizar() hace el commit final — cierra la transacción completa
        self.producto_repo.actualizar(producto, {"stock": nuevo_stock, "activo": activo})

    def crear_categoria(self, datos: dict, solicitante_rol: str) -> Categoria:
        """Crea una nueva categoría de productos. Solo admin."""

        if solicitante_rol != "administrador":
            raise PermissionError("FORBIDDEN")

        # Validación previa para devolver 409 con mensaje claro en vez del
        # error crudo de la BD si llegara a violar la constraint UNIQUE
        if self.categoria_repo.buscar_por_codigo(datos["codigo"]):
            raise ValueError("CATEGORY_ALREADY_EXISTS")

        nueva = Categoria(nombre=datos["nombre"], codigo=datos["codigo"])
        return self.categoria_repo.guardar(nueva)

    def crear_laboratorio(self, datos: dict, solicitante_rol: str) -> Laboratorio:
        """Crea un nuevo laboratorio fabricante. Solo admin."""

        if solicitante_rol != "administrador":
            raise PermissionError("FORBIDDEN")

        # Mismo criterio que categorías: chequeo previo para mensaje claro
        if self.laboratorio_repo.buscar_por_nombre(datos["nombre"]):
            raise ValueError("LAB_ALREADY_EXISTS")

        nuevo = Laboratorio(nombre=datos["nombre"], pais=datos["pais"])
        return self.laboratorio_repo.guardar(nuevo)
