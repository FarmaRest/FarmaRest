import importlib.util, pathlib

_path = pathlib.Path(__file__).parent / "pagos.domain.py"
_spec = importlib.util.spec_from_file_location("pagos_domain", _path)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

Pago    = _mod.Pago
Factura = _mod.Factura
