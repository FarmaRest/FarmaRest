# ─────────────────────────────────────────────────────────────────────────────
# CAPA: REPOSITORY — Módulo de Productos
# Responsabilidad: Es el ÚNICO lugar de todo el proyecto donde se hacen
# consultas SQL a las tablas del módulo de productos (productos, lotes,
# presentaciones, categorias, laboratorios). Cada operación recibe la
# sesión de SQLAlchemy ya inyectada y delega la traducción a SQL al ORM.
# ─────────────────────────────────────────────────────────────────────────────

from datetime import date
from sqlalchemy.orm import Session, joinedload
from app.domain.productos import (
    Categoria, Laboratorio, Producto, Lote, Presentacion,
)


class CategoriaRepositorio:
    """
    Acceso a la tabla 'categorias'. En el contexto de la HU-PROD-02 se usa
    find-only (la categoría debe existir antes de crear un producto). Para
    poblar el catálogo de categorías se expone también un endpoint POST
    administrado por 'guardar'.
    """

    def __init__(self, db: Session):
        self.db = db

    def buscar_por_codigo(self, codigo: str):
        # Busca la categoría por su código corto único (ej: 'CAT-01').
        # Retorna None si no existe — el servicio decide qué hacer
        return self.db.query(Categoria).filter(Categoria.codigo == codigo).first()

    def listar_todas(self) -> list:
        return self.db.query(Categoria).order_by(Categoria.nombre).all()

    def guardar(self, categoria: Categoria) -> Categoria:
        # Inserta una nueva categoría. La BD garantiza unicidad de 'codigo'
        # vía constraint UNIQUE; el servicio valida antes para devolver 409 limpio
        self.db.add(categoria)
        self.db.commit()
        self.db.refresh(categoria)
        return categoria


class LaboratorioRepositorio:
    """
    Acceso a la tabla 'laboratorios'. En productos se usa find-only por
    'nombre' (UNIQUE en la BD). El endpoint POST de laboratorios usa
    'guardar' para poblar el catálogo.
    """

    def __init__(self, db: Session):
        self.db = db

    def buscar_por_nombre(self, nombre: str):
        # El nombre del laboratorio es UNIQUE en la BD, por eso es seguro
        # usarlo como criterio de búsqueda. Retorna None si no existe
        return self.db.query(Laboratorio).filter(Laboratorio.nombre == nombre).first()

    def listar_todos(self) -> list:
        return self.db.query(Laboratorio).order_by(Laboratorio.nombre).all()

    def guardar(self, laboratorio: Laboratorio) -> Laboratorio:
        # Inserta un nuevo laboratorio. UNIQUE en 'nombre' a nivel BD;
        # el servicio valida antes para devolver 409 con mensaje claro
        self.db.add(laboratorio)
        self.db.commit()
        self.db.refresh(laboratorio)
        return laboratorio


class ProductoRepositorio:
    """
    Acceso a la tabla 'productos'. Maneja el alta, consulta por id y
    actualización parcial. La actualización solo modifica los campos que
    se pasen en el diccionario — los demás quedan intactos.
    """

    def __init__(self, db: Session):
        self.db = db

    def buscar_por_id(self, producto_id: str):
        # Busca un producto por UUID. Retorna None si no existe.
        # Se usa antes de actualizar para devolver 404 limpio
        return self.db.query(Producto).filter(Producto.id == producto_id).first()

    def listar_activos(self, categoria_codigo: str = None, laboratorio_nombre: str = None) -> list:
        # joinedload carga categoria, laboratorio y presentaciones en una sola
        # query con LEFT OUTER JOIN, evitando el problema N+1 al serializar la lista
        query = (
            self.db.query(Producto)
            .options(
                joinedload(Producto.categoria),
                joinedload(Producto.laboratorio),
                joinedload(Producto.presentaciones),
            )
            .filter(Producto.activo == True)
        )
        if categoria_codigo:
            query = query.join(Categoria, Producto.categoria_id == Categoria.id).filter(
                Categoria.codigo == categoria_codigo
            )
        if laboratorio_nombre:
            query = query.join(Laboratorio, Producto.laboratorio_id == Laboratorio.id).filter(
                Laboratorio.nombre == laboratorio_nombre
            )
        return query.all()

    def guardar(self, producto: Producto) -> Producto:
        # Inserta el nuevo producto y refresca para obtener id y fecha_registro
        # que la BD genera automáticamente
        self.db.add(producto)
        self.db.commit()
        self.db.refresh(producto)
        return producto

    def actualizar(self, producto: Producto, campos: dict) -> Producto:
        # Aplica setattr a cada campo del diccionario sobre el objeto en memoria
        # y persiste con un único commit. Refresca para devolver el estado real
        for campo, valor in campos.items():
            setattr(producto, campo, valor)
        self.db.commit()
        self.db.refresh(producto)
        return producto


class LoteRepositorio:
    """
    Acceso a la tabla 'lotes'. En esta HU se usa para:
    - guardar el lote inicial al registrar un producto
    - consultar el lote vigente (FEFO: el de vencimiento más próximo que aún
      no se ha vencido) cuando se actualiza el stock en un PUT, para decidir
      si el producto puede volver a quedar 'activo = TRUE'
    """

    def __init__(self, db: Session):
        self.db = db

    def buscar_por_codigo(self, codigo_lote: str):
        return self.db.query(Lote).filter(Lote.codigo_lote == codigo_lote).first()

    def listar_por_producto(self, producto_id: str) -> list:
        return (
            self.db.query(Lote)
            .filter(Lote.producto_id == producto_id)
            .order_by(Lote.fecha_vencimiento.asc())
            .all()
        )

    def guardar(self, lote: Lote) -> Lote:
        # Inserta el lote y refresca para obtener id y fecha_ingreso
        self.db.add(lote)
        self.db.commit()
        self.db.refresh(lote)
        return lote

    def listar_con_stock_por_producto(self, producto_id: str) -> list:
        # HU-PROD-03: lotes con cantidad > 0 ordenados por vencimiento ASC (política FEFO).
        # El lote más próximo a vencer es el primero en descontarse.
        return (
            self.db.query(Lote)
            .filter(Lote.producto_id == producto_id, Lote.cantidad > 0)
            .order_by(Lote.fecha_vencimiento.asc())
            .all()
        )

    def actualizar_cantidad(self, lote: Lote, nueva_cantidad: int) -> Lote:
        # flush en lugar de commit: persiste el cambio dentro de la transacción
        # activa sin cerrarlo. El commit final lo hace descontar_stock_fefo
        # al actualizar el producto, garantizando atomicidad del proceso completo.
        lote.cantidad = nueva_cantidad
        self.db.flush()
        return lote

    def buscar_lote_vigente_por_producto(self, producto_id: str):
        # FEFO: retorna el lote del producto con la fecha_vencimiento más
        # próxima que aún esté en el futuro. Si no hay lotes vigentes,
        # retorna None y el servicio decide poner 'activo = FALSE'.
        # Esta es la consulta crítica del recálculo automático del PUT
        return (
            self.db.query(Lote)
            .filter(Lote.producto_id == producto_id)
            .filter(Lote.fecha_vencimiento >= date.today())
            .order_by(Lote.fecha_vencimiento.asc())
            .first()
        )


class PresentacionRepositorio:
    """
    Acceso a la tabla 'presentaciones'. En esta HU solo se usa al registrar
    un producto: las presentaciones llegan como lista en el body y se
    insertan todas juntas con un único commit (operación atómica).
    """

    def __init__(self, db: Session):
        self.db = db

    def listar_por_producto(self, producto_id: str) -> list:
        return (
            self.db.query(Presentacion)
            .filter(Presentacion.producto_id == producto_id)
            .all()
        )

    def buscar_por_id(self, presentacion_id: str):
        return self.db.query(Presentacion).filter(Presentacion.id == presentacion_id).first()

    def actualizar(self, presentacion: Presentacion, campos: dict) -> Presentacion:
        for campo, valor in campos.items():
            setattr(presentacion, campo, valor)
        self.db.commit()
        self.db.refresh(presentacion)
        return presentacion

    def guardar_todas(self, presentaciones: list[Presentacion]) -> list[Presentacion]:
        # Recorre la lista agregando cada presentación a la sesión.
        # Un solo commit al final mantiene la atomicidad del conjunto
        for presentacion in presentaciones:
            self.db.add(presentacion)
        self.db.commit()
        for presentacion in presentaciones:
            self.db.refresh(presentacion)
        return presentaciones
