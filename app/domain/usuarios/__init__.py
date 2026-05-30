import importlib.util, pathlib, sys

_path = pathlib.Path(__file__).parent / "usuarios.domain.py"

if 'usuarios_domain_loaded' not in sys.modules:
    sys.modules['usuarios_domain_loaded'] = True
    _spec = importlib.util.spec_from_file_location("usuarios_domain", _path)
    _mod  = importlib.util.module_from_spec(_spec)
    sys.modules['usuarios_domain'] = _mod
    _spec.loader.exec_module(_mod)
else:
    _mod = sys.modules['usuarios_domain']

Usuario             = _mod.Usuario
Direccion           = _mod.Direccion
HistorialCorreo     = _mod.HistorialCorreo
HistorialContrasena = _mod.HistorialContrasena