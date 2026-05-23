import importlib.util, os

_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "autenticacion.domain.py"))
_spec = importlib.util.spec_from_file_location("autenticacion_domain", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
Sesion = _mod.Sesion