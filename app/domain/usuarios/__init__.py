import importlib.util, pathlib
_path = pathlib.Path(__file__).parent / "usuarios.domain.py"
_spec = importlib.util.spec_from_file_location("usuarios_domain", _path)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
Usuario             = _mod.Usuario
Direccion           = _mod.Direccion
HistorialCorreo     = _mod.HistorialCorreo
HistorialContrasena = _mod.HistorialContrasena
