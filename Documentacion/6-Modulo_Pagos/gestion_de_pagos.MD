## Historia de usuario:
# Gestión de pagos

Como cliente de la plataforma FarmaRest,
quiero realizar y registrar el pago de mis pedidos mediante una pasarela de pago externa (Wompi),
para completar la compra de forma segura y permitir la continuidad del proceso (preparación y envío del pedido).

**¿QUÉ?**
Permitir el registro, procesamiento y gestión de los pagos asociados a los pedidos dentro del sistema.

**¿CÓMO?**
Mediante la integración con la pasarela de pago Wompi, donde el sistema envía la información de la transacción, valida que el pago se realice dentro del tiempo permitido, registra los datos en la base de datos (monto, referencia, estado), recibe la confirmación a través de notificaciones automáticas (webhook) y actualiza el estado del pago (pendiente, aprobado o rechazado).

**¿PARA QUÉ?**
Para asegurar que los pedidos sean pagados de manera segura, validar las transacciones realizadas por los usuarios y permitir que el proceso de compra continúe, como la preparación y envío del pedido.
