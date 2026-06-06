from sqlalchemy.orm import Session
from decimal import Decimal
import uuid
import importlib.util, os

def _load(rel_path, name):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), rel_path))
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_repo_mod    = _load("../../repositories/carritos/carritos.repositori.py",  "carritos_repo")
_prod_mod    = _load("../../repositories/productos/productos.respositori.py", "productos_repo")
_domain_mod  = _load("../../domain/carritos/carritos.domain.py", "carritos_domain")

CarritoRepositorio     = _repo_mod.CarritoRepositorio
ItemCarritoRepositorio = _repo_mod.ItemCarritoRepositorio
ProductoRepositorio    = _prod_mod.ProductoRepositorio
Carrito                = _domain_mod.Carrito
ItemCarrito            = _domain_mod.ItemCarrito

MAX_UNIDADES_POR_PRODUCTO = 20
MIN_PRODUCTOS_DISTINTOS   = 2


class CarritoService:
    def __init__(self, db: Session):
        self.db            = db
        self.carritos      = CarritoRepositorio(db)
        self.items         = ItemCarritoRepositorio(db)
        self.productos     = ProductoRepositorio(db)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _recalcular_totales(self, carrito: Carrito) -> Carrito:
        subtotal_base = Decimal("0")
        total_iva     = Decimal("0")
        for item in carrito.items:
            subtotal_base += item.precio_unitario * item.cantidad
            total_iva     += item.iva_unitario    * item.cantidad
        total = subtotal_base + total_iva
        return self.carritos.actualizar_totales(carrito, subtotal_base, total_iva, total)

    def _serializar_carrito(self, carrito: Carrito) -> dict:
        return {
            "carritoId": str(carrito.id),
            "usuarioId": str(carrito.usuario_id),
            "items": [
                {
                    "itemId":         str(i.id),
                    "productoId":     str(i.producto_id),
                    "nombre":         i.producto.nombre if i.producto else None,
                    "cantidad":       i.cantidad,
                    "precioUnitario": float(i.precio_unitario),
                    "ivaUnitario":    float(i.iva_unitario),
                    "subtotal":       float(i.subtotal),
                }
                for i in carrito.items
            ],
            "subtotalBase": float(carrito.subtotal_base),
            "totalIva":     float(carrito.total_iva),
            "total":        float(carrito.total),
        }

    # ── Casos de uso ─────────────────────────────────────────────────────────

    def agregar_producto(self, usuario_id: str, producto_id: str, cantidad: int) -> dict:
        producto = self.productos.buscar_por_id(producto_id)
        if not producto or not producto.activo:
            raise LookupError("PRODUCT_NOT_FOUND|El producto solicitado no existe o no está disponible.")

        if producto.stock < cantidad:
            raise ValueError(f"INSUFFICIENT_STOCK|Solo hay {producto.stock} unidades disponibles del producto {producto.nombre}.")

        carrito = self.carritos.buscar_activo_por_usuario_id(usuario_id)
        if not carrito:
            carrito = Carrito(usuario_id=uuid.UUID(usuario_id))
            carrito = self.carritos.guardar(carrito)

        precio_unitario = Decimal(str(producto.precio))
        iva_unitario    = (precio_unitario * Decimal("0.19")).quantize(Decimal("0.01")) if producto.aplica_iva else Decimal("0")

        item_existente = self.items.buscar_por_carrito_y_producto(carrito.id, producto.id)
        if item_existente:
            nueva_cantidad = item_existente.cantidad + cantidad
            if nueva_cantidad > MAX_UNIDADES_POR_PRODUCTO:
                raise ValueError(
                    f"MAX_UNITS_EXCEEDED|No se pueden agregar más de {MAX_UNIDADES_POR_PRODUCTO} unidades del mismo producto por carrito. "
                    f"Actualmente tienes {item_existente.cantidad} unidades de {producto.nombre}."
                )
            if producto.stock < nueva_cantidad:
                raise ValueError(f"INSUFFICIENT_STOCK|Solo hay {producto.stock} unidades disponibles del producto {producto.nombre}.")
            nuevo_subtotal = Decimal(str(nueva_cantidad)) * (precio_unitario + iva_unitario)
            self.items.actualizar_cantidad(item_existente, nueva_cantidad, nuevo_subtotal)
        else:
            if cantidad > MAX_UNIDADES_POR_PRODUCTO:
                raise ValueError(
                    f"MAX_UNITS_EXCEEDED|No se pueden agregar más de {MAX_UNIDADES_POR_PRODUCTO} unidades del mismo producto por carrito. "
                    f"Actualmente tienes 0 unidades de {producto.nombre}."
                )
            subtotal = Decimal(str(cantidad)) * (precio_unitario + iva_unitario)
            nuevo_item = ItemCarrito(
                carrito_id      = carrito.id,
                producto_id     = producto.id,
                cantidad        = cantidad,
                precio_unitario = precio_unitario,
                iva_unitario    = iva_unitario,
                subtotal        = subtotal,
            )
            self.items.guardar(nuevo_item)

        self.db.refresh(carrito)
        carrito = self._recalcular_totales(carrito)
        return self._serializar_carrito(carrito)

    def consultar_carrito(self, usuario_id: str) -> dict | None:
        carrito = self.carritos.buscar_activo_por_usuario_id(usuario_id)
        if not carrito:
            return None
        return self._serializar_carrito(carrito)

    def actualizar_cantidad(self, usuario_id: str, item_id: str, cantidad: int) -> dict:
        item = self.items.buscar_por_id_y_usuario(item_id, usuario_id)
        if not item:
            raise LookupError("CART_ITEM_NOT_FOUND|No existe un ítem con el ID proporcionado en tu carrito activo.")

        producto = self.productos.buscar_por_id(str(item.producto_id))
        if cantidad > MAX_UNIDADES_POR_PRODUCTO:
            raise ValueError(
                f"MAX_UNITS_EXCEEDED|No se pueden agregar más de {MAX_UNIDADES_POR_PRODUCTO} unidades del mismo producto por carrito. "
                f"Actualmente tienes {item.cantidad} unidades de {producto.nombre}."
            )
        if producto.stock < cantidad:
            raise ValueError(f"INSUFFICIENT_STOCK|Solo hay {producto.stock} unidades disponibles del producto {producto.nombre}.")

        nuevo_subtotal = Decimal(str(cantidad)) * (item.precio_unitario + item.iva_unitario)
        self.items.actualizar_cantidad(item, cantidad, nuevo_subtotal)

        carrito = self.carritos.buscar_activo_por_usuario_id(usuario_id)
        self.db.refresh(carrito)
        carrito = self._recalcular_totales(carrito)
        return self._serializar_carrito(carrito)

    def validar_minimo_productos(self, usuario_id: str) -> None:
        carrito = self.carritos.buscar_activo_por_usuario_id(usuario_id)
        if not carrito:
            raise ValueError("MIN_PRODUCTS_NOT_MET|El carrito debe contener al menos 2 productos diferentes para poder crear un pedido. Actualmente tienes 0 productos diferentes.")
        total_distintos = self.items.contar_productos_distintos(carrito.id)
        if total_distintos < MIN_PRODUCTOS_DISTINTOS:
            raise ValueError(
                f"MIN_PRODUCTS_NOT_MET|El carrito debe contener al menos {MIN_PRODUCTOS_DISTINTOS} productos diferentes para poder crear un pedido. "
                f"Actualmente tienes {total_distintos} producto{'s diferentes' if total_distintos != 1 else ' diferente'}."
            )

    def eliminar_item(self, usuario_id: str, item_id: str) -> None:
        item = self.items.buscar_por_id_y_usuario(item_id, usuario_id)
        if not item:
            raise LookupError("CART_ITEM_NOT_FOUND|No existe un ítem con el ID proporcionado en tu carrito activo.")

        carrito = self.carritos.buscar_activo_por_usuario_id(usuario_id)
        self.items.eliminar(item)
        self.db.refresh(carrito)
        self._recalcular_totales(carrito)
