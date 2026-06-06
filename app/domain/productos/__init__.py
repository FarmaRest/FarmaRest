import importlib.util, pathlib, sys

_KEY = "productos_domain"
if _KEY not in sys.modules:
    _path = pathlib.Path(__file__).parent / "productos.domain.py"
    _spec = importlib.util.spec_from_file_location(_KEY, _path)
    _mod  = importlib.util.module_from_spec(_spec)
    sys.modules[_KEY] = _mod
    _spec.loader.exec_module(_mod)

Categoria    = sys.modules[_KEY].Categoria
Laboratorio  = sys.modules[_KEY].Laboratorio
Producto     = sys.modules[_KEY].Producto
Lote         = sys.modules[_KEY].Lote
Presentacion = sys.modules[_KEY].Presentacion
