import importlib.util, pathlib, sys

_KEY = "autenticacion_domain"
if _KEY not in sys.modules:
    _path = pathlib.Path(__file__).parent / "autenticacion.domain.py"
    _spec = importlib.util.spec_from_file_location(_KEY, _path)
    _mod  = importlib.util.module_from_spec(_spec)
    sys.modules[_KEY] = _mod
    _spec.loader.exec_module(_mod)

Sesion = sys.modules[_KEY].Sesion