import importlib.util, pathlib

# Cargar modelos ORM
_path = pathlib.Path(__file__).parent / "pedidos.domain.py"
_spec = importlib.util.spec_from_file_location("pedidos_domain", _path)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
Pedido     = _mod.Pedido
ItemPedido = _mod.ItemPedido

# Cargar schemas Pydantic
_path_sch = pathlib.Path(__file__).parent / "pedidos.schemas.py"
_spec_sch = importlib.util.spec_from_file_location("pedidos_schemas", _path_sch)
_mod_sch  = importlib.util.module_from_spec(_spec_sch)
_spec_sch.loader.exec_module(_mod_sch)
PedidoEntrada        = _mod_sch.PedidoEntrada
PedidoSalida         = _mod_sch.PedidoSalida
ItemPedidoSalida     = _mod_sch.ItemPedidoSalida
DireccionEntradaSchema = _mod_sch.DireccionEntradaSchema