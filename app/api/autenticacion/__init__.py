import importlib.util
import os

path = os.path.join(os.path.dirname(__file__), "autenticacion.api.py")
spec = importlib.util.spec_from_file_location("autenticacion_api", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
router = mod.router