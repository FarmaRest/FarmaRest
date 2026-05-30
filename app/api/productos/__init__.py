import importlib.util, pathlib

_path = pathlib.Path(__file__).parent / "productos.api.py"
_spec = importlib.util.spec_from_file_location("productos_api", _path)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

router                = _mod.router
router_categorias     = _mod.router_categorias
router_laboratorios   = _mod.router_laboratorios
router_lotes          = _mod.router_lotes
router_presentaciones = _mod.router_presentaciones
