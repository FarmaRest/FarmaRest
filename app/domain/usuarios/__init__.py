import importlib.util, pathlib, sys

_KEY = "usuarios_domain"
if _KEY not in sys.modules:
    _path = pathlib.Path(__file__).parent / "usuarios.domain.py"
    _spec = importlib.util.spec_from_file_location(_KEY, _path)
    _mod  = importlib.util.module_from_spec(_spec)
    sys.modules[_KEY] = _mod
    _spec.loader.exec_module(_mod)

Usuario             = sys.modules[_KEY].Usuario
Direccion           = sys.modules[_KEY].Direccion
HistorialCorreo     = sys.modules[_KEY].HistorialCorreo
HistorialContrasena = sys.modules[_KEY].HistorialContrasena
