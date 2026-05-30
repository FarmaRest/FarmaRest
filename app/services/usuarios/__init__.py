import importlib.util, pathlib

_path = pathlib.Path(__file__).parent / "usuarios.services.py"
_spec = importlib.util.spec_from_file_location("usuarios_services", _path)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

UsuarioService      = _mod.UsuarioService
DireccionService    = _mod.DireccionService
InactivacionService = _mod.InactivacionService
