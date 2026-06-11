# ─────────────────────────────────────────────────────────────────────────────
# CAPA: SERVICE – Adaptador de Wompi
# Responsabilidad: Encapsula la integración HTTP con la pasarela de pagos Wompi.
# Mientras no se cuente con credenciales reales, genera una URL de checkout
# simulada para no bloquear el flujo del módulo.
# ─────────────────────────────────────────────────────────────────────────────

import os


class WompiAdapter:
    BASE_CHECKOUT_URL = os.getenv("WOMPI_CHECKOUT_URL", "https://checkout.wompi.co/l/")

    def crear_transaccion(self, monto_en_centavos: int, moneda: str, referencia: str, correo_cliente: str) -> dict:
        """
        Inicia una transacción en Wompi. Retorna la urlCheckout y el estado inicial.
        """
        return {
            "urlCheckout": f"{self.BASE_CHECKOUT_URL}{referencia}",
            "estado": "PENDING",
        }
