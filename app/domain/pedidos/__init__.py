import importlib.util, pathlib, sys

_KEY = "pedidos_domain"
if _KEY not in sys.modules:
    _path = pathlib.Path(__file__).parent / "pedidos.domain.py"
    _spec = importlib.util.spec_from_file_location(_KEY, _path)
    _mod  = importlib.util.module_from_spec(_spec)
    sys.modules[_KEY] = _mod
    _spec.loader.exec_module(_mod)

Pedido     = sys.modules[_KEY].Pedido
ItemPedido = sys.modules[_KEY].ItemPedido

_KEY_SCH = "pedidos_schemas"
if _KEY_SCH not in sys.modules:
    _path_sch = pathlib.Path(__file__).parent / "pedidos.schemas.py"
    _spec_sch = importlib.util.spec_from_file_location(_KEY_SCH, _path_sch)
    _mod_sch  = importlib.util.module_from_spec(_spec_sch)
    sys.modules[_KEY_SCH] = _mod_sch
    _spec_sch.loader.exec_module(_mod_sch)

PedidoEntrada          = sys.modules[_KEY_SCH].PedidoEntrada
PedidoSalida           = sys.modules[_KEY_SCH].PedidoSalida
ItemPedidoSalida       = sys.modules[_KEY_SCH].ItemPedidoSalida
DireccionEntradaSchema = sys.modules[_KEY_SCH].DireccionEntradaSchema