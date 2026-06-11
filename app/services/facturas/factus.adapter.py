# ─────────────────────────────────────────────────────────────────────────────
# CAPA: SERVICE – Adaptador de Factus
# Responsabilidad: Encapsula la integración HTTP con la API de Factus para la
# emisión de facturas electrónicas ante la DIAN.
# ─────────────────────────────────────────────────────────────────────────────

import os
import requests

MUNICIPIO_DEFECTO = "11001"  # Bogotá D.C.


class FactusAdapter:
    BASE_URL           = os.getenv("FACTUS_BASE_URL", "https://api-sandbox.factus.com.co")
    EMAIL              = os.getenv("FACTUS_EMAIL", "")
    PASSWORD           = os.getenv("FACTUS_PASSWORD", "")
    CLIENT_ID          = os.getenv("FACTUS_CLIENT_ID", "")
    CLIENT_SECRET      = os.getenv("FACTUS_CLIENT_SECRET", "")
    NUMBERING_RANGE_ID = os.getenv("FACTUS_NUMBERING_RANGE_ID", "1")

    def _obtener_token(self) -> str:
        respuesta = requests.post(
            f"{self.BASE_URL}/oauth/token",
            data={
                "grant_type": "password",
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "username": self.EMAIL,
                "password": self.PASSWORD,
            },
            headers={"Accept": "application/json"},
            timeout=15,
        )
        respuesta.raise_for_status()
        return respuesta.json()["access_token"]

    def emitir(self, numero_factura: str, factura, pedido, items_pedido: list, usuario, productos_por_id: dict) -> dict:
        """
        Llama a la API de Factus (v2/bills/validate) para emitir la factura ante la DIAN.
        Retorna {"cufe", "factus_id", "url_pdf", "url_xml"} si Factus responde correctamente.
        Lanza una excepción si la llamada falla.
        """
        token = self._obtener_token()

        items = []
        for item in items_pedido:
            producto = productos_por_id.get(item.producto_id)
            items.append({
                "code_reference": str(item.producto_id),
                "name": producto.nombre if producto else "Producto",
                "quantity": f"{item.cantidad:.2f}",
                "discount_rate": "0.00",
                "price": f"{float(item.precio_unitario):.2f}",
                "unit_measure_code": "94",
                "standard_code": "999",
                "taxes": self._impuestos(item),
            })

        payload = {
            "reference_code": numero_factura,
            "document": "01",
            "numbering_range_id": int(self.NUMBERING_RANGE_ID),
            "operation_type": "10",
            "send_email": False,
            "customer": {
                "identification_document_code": "13",
                "identification": usuario.cedula,
                "names": f"{usuario.primer_nombre} {usuario.primer_apellido}".strip(),
                "address": pedido.direccion_entrega,
                "email": usuario.correo,
                "phone": usuario.telefono or "",
                "legal_organization_code": "2",
                "tribute_code": "ZZ",
                "municipality_code": MUNICIPIO_DEFECTO,
            },
            "items": items,
        }

        respuesta = requests.post(
            f"{self.BASE_URL}/v2/bills/validate",
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=30,
        )
        respuesta.raise_for_status()
        data = respuesta.json().get("data", {})
        bill = data.get("bill", {})

        return {
            "cufe": bill.get("cufe") or data.get("cufe"),
            "factus_id": str(bill.get("id")) if bill.get("id") is not None else None,
            "url_pdf": bill.get("public_url") or data.get("public_url"),
            "url_xml": bill.get("qr_image") or data.get("qr_image"),
        }

    def _impuestos(self, item) -> list:
        if item.precio_unitario and item.iva_unitario:
            tasa = round(float(item.iva_unitario) / float(item.precio_unitario) * 100, 2)
            return [{"code": "01", "rate": f"{tasa:.2f}"}]
        return [{"is_excluded": True}]
