import importlib.util, os

_path = os.path.join(os.path.dirname(__file__), "carritos.api.py")
_spec = importlib.util.spec_from_file_location("carritos_api", _path)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

router = _mod.router
