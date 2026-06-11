# ─────────────────────────────────────────────────────────────────────────────
# CAPA: SERVICE – Adaptador de Wompi
# Responsabilidad: Encapsula la integración con la pasarela de pagos Wompi
# mediante el Web Checkout (widget hospedado), generando una URL de pago
# firmada con la llave de integridad para que el cliente complete la
# transacción directamente en Wompi.
# ─────────────────────────────────────────────────────────────────────────────

import hashlib
import os


class WompiAdapter:
    CHECKOUT_URL      = os.getenv("WOMPI_CHECKOUT_URL", "https://checkout.wompi.co/p/")
    PUBLIC_KEY        = os.getenv("WOMPI_PUBLIC_KEY", "")
    INTEGRITY_SECRET  = os.getenv("WOMPI_INTEGRITY_SECRET", "")

    def crear_transaccion(self, monto_en_centavos: int, moneda: str, referencia: str, correo_cliente: str) -> dict:
        """
        Genera la URL del Web Checkout de Wompi para la referencia indicada,
        firmada con la llave de integridad del comercio. La transacción real
        se crea en Wompi cuando el cliente completa el pago en esa URL, y el
        resultado llega al sistema vía webhook.
        """
        firma_integridad = self._firma_integridad(referencia, monto_en_centavos, moneda)

        params = (
            f"public-key={self.PUBLIC_KEY}"
            f"&currency={moneda}"
            f"&amount-in-cents={monto_en_centavos}"
            f"&reference={referencia}"
            f"&signature:integrity={firma_integridad}"
            f"&customer-data:email={correo_cliente}"
        )

        return {
            "urlCheckout": f"{self.CHECKOUT_URL}?{params}",
            "estado": "PENDING",
        }

    def _firma_integridad(self, referencia: str, monto_en_centavos: int, moneda: str) -> str:
        cadena = f"{referencia}{monto_en_centavos}{moneda}{self.INTEGRITY_SECRET}"
        return hashlib.sha256(cadena.encode("utf-8")).hexdigest()
