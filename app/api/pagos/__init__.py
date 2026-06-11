import importlib.util, pathlib

_path = pathlib.Path(__file__).parent / "pagos.api.py"
_spec = importlib.util.spec_from_file_location("pagos_api", _path)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

router = _mod.router
