# ─────────────────────────────────────────────────────────────────────────────
# CAPA: DOMAIN — Módulo de Productos
# Responsabilidad: Define los modelos ORM que SQLAlchemy mapea a las tablas
# de la base de datos. Aquí viven las entidades del catálogo y sus relaciones.
# Ninguna otra capa escribe SQL — solo describe la forma de los datos.
# ─────────────────────────────────────────────────────────────────────────────

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Numeric, Date, Text,
    ForeignKey, CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.base import Base


class Categoria(Base):
    """
    Tabla de categorías de productos (analgésicos, antibióticos, insumos, etc.).
    El campo 'codigo' es un identificador corto pensado para uso interno y
    reportes — por eso es UNIQUE: no debe haber dos categorías con el mismo
    código aunque sus nombres puedan parecerse.
    """
    __tablename__ = "categorias"

    # Identificador único universal, se genera automáticamente al crear el registro
    id     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Nombre visible de la categoría (ej: "Analgésicos")
    nombre = Column(String(100), nullable=False)

    # Código corto único (ej: "ANALG"). UNIQUE evita categorías duplicadas
    codigo = Column(String(20),  nullable=False, unique=True)

    # Relación 1 a N con Producto: una categoría agrupa muchos productos.
    # NO se usa cascade delete: la categoría no debe borrarse si tiene productos
    productos = relationship("Producto", back_populates="categoria")


class Laboratorio(Base):
    """
    Tabla de laboratorios fabricantes (Bayer, Genfar, Tecnoquímicas, etc.).
    El nombre es UNIQUE porque no debe haber dos laboratorios con el mismo
    nombre en el catálogo. El país queda obligatorio para reportes regulatorios.
    """
    __tablename__ = "laboratorios"

    id     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Nombre del laboratorio. UNIQUE para evitar duplicados
    nombre = Column(String(100), nullable=False, unique=True)

    # País de origen del laboratorio (requerido para trazabilidad)
    pais   = Column(String(100), nullable=False)

    # Relación 1 a N: un laboratorio fabrica muchos productos
    productos = relationship("Producto", back_populates="laboratorio")


class Producto(Base):
    """
    Tabla principal del catálogo. Representa cada medicamento o insumo médico.
    El precio almacenado es SIEMPRE el precio base sin IVA — el IVA se calcula
    al momento de agregar el producto al carrito o pedido y se guarda allí
    como snapshot (ver nota técnica de la HU sobre IVA).
    Un producto solo aparece como disponible cuando 'activo = TRUE', lo cual
    requiere que tenga stock > 0 y al menos un lote con vencimiento válido.
    Las CheckConstraint protegen la integridad directo desde la BD.
    """
    __tablename__ = "productos"
    __table_args__ = (
        # Precio no puede ser cero o negativo
        CheckConstraint("precio > 0",  name="ck_productos_precio"),
        # Stock no puede ser negativo (sí puede ser 0 cuando se agota)
        CheckConstraint("stock >= 0", name="ck_productos_stock"),
    )

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Nombre comercial del producto (ej: "Acetaminofén 500mg")
    nombre         = Column(String(200), nullable=False)

    # Descripción larga opcional. TEXT permite contenido extenso sin límite fijo
    descripcion    = Column(Text, nullable=True)

    # Precio base sin IVA. NUMERIC(10,2) admite hasta 99,999,999.99
    precio         = Column(Numeric(10, 2), nullable=False)

    # IVA del 19% aplicable solo a insumos/cosméticos. Los medicamentos de uso
    # humano están exentos en Colombia, por eso el default es FALSE
    aplica_iva     = Column(Boolean, nullable=False, default=False)

    # Cantidad disponible en inventario. Se actualiza al ingresar/vender lotes
    stock          = Column(Integer, nullable=False, default=0)

    # Bandera de disponibilidad en el catálogo. FALSE por defecto:
    # el producto solo se activa cuando tiene stock > 0 y vencimiento válido.
    # Esa lógica se aplica en HU-PROD-03 (control FEFO)
    activo         = Column(Boolean, nullable=False, default=False)

    # FK obligatoria a categorías. Cada producto pertenece a una categoría
    categoria_id   = Column(UUID(as_uuid=True), ForeignKey("categorias.id"),
                            nullable=False)

    # FK obligatoria a laboratorios. Cada producto tiene un fabricante
    laboratorio_id = Column(UUID(as_uuid=True), ForeignKey("laboratorios.id"),
                            nullable=False)

    # Fecha de registro en el sistema. Se establece automáticamente al insertar
    fecha_registro = Column(DateTime(timezone=True), nullable=False,
                            default=lambda: datetime.now(timezone.utc))

    # ── Relaciones ───────────────────────────────────────────────────────
    # Muchos a uno con sus atributos descriptivos
    categoria      = relationship("Categoria",   back_populates="productos")
    laboratorio    = relationship("Laboratorio", back_populates="productos")

    # Uno a muchos con lotes y presentaciones.
    # IMPORTANTE: NO se usa cascade="all, delete-orphan" — al desactivar
    # (no eliminar) un producto, sus lotes y presentaciones se conservan
    # para mantener trazabilidad e historial conforme a requerimientos ISO
    lotes          = relationship("Lote",         back_populates="producto")
    presentaciones = relationship("Presentacion", back_populates="producto")


class Lote(Base):
    """
    Tabla de lotes de producto. Cada lote es una entrada física de inventario
    con su propio código, cantidad y fecha de vencimiento. La política FEFO
    (First Expired, First Out) de HU-PROD-03 se apoya en 'fecha_vencimiento'
    para decidir qué lote vender primero.
    El código de lote es UNIQUE en todo el sistema: dos productos distintos
    no pueden compartir el mismo código de lote — viene impreso por el
    fabricante y es trazable.
    """
    __tablename__ = "lotes"
    __table_args__ = (
        # Cantidad por lote no puede ser negativa
        CheckConstraint("cantidad >= 0", name="ck_lotes_cantidad"),
    )

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # FK obligatoria a productos. Un lote siempre pertenece a un producto
    producto_id       = Column(UUID(as_uuid=True), ForeignKey("productos.id"),
                               nullable=False)

    # Código impreso por el fabricante. UNIQUE en todo el sistema
    codigo_lote       = Column(String(50), nullable=False, unique=True)

    # Stock disponible en este lote específico (no en el total del producto)
    cantidad          = Column(Integer, nullable=False, default=0)

    # Fecha de vencimiento del lote. Base de la política FEFO
    fecha_vencimiento = Column(Date, nullable=False)

    # Fecha de ingreso al inventario. Se establece automáticamente al insertar
    fecha_ingreso     = Column(DateTime(timezone=True), nullable=False,
                               default=lambda: datetime.now(timezone.utc))

    # Relación inversa hacia el producto al que pertenece este lote
    producto = relationship("Producto", back_populates="lotes")


class Presentacion(Base):
    """
    Tabla de presentaciones comerciales de un producto.
    Un mismo medicamento puede venderse en distintas presentaciones (caja x10,
    caja x20, frasco 60ml, etc.). Cada presentación se guarda como una fila
    independiente con su tipo, cantidad y unidad de medida.
    """
    __tablename__ = "presentaciones"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # FK obligatoria al producto al que pertenece la presentación
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"),
                         nullable=False)

    # Tipo de empaque (ej: "caja", "frasco", "blíster", "tubo")
    tipo        = Column(String(50), nullable=False)

    # Cantidad de unidades dentro del empaque (ej: 10, 20, 60)
    cantidad    = Column(Integer, nullable=False)

    # Unidad de medida (ej: "tabletas", "ml", "g")
    unidad      = Column(String(20), nullable=False)

    # Relación inversa hacia el producto
    producto = relationship("Producto", back_populates="presentaciones")
