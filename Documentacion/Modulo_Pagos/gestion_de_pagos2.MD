## Historia de usuario:
# Gestión de pagos

Como cliente de la plataforma FarmaRest,
quiero realizar el pago de mi pedido dentro de un tiempo límite establecido,
para asegurar que mi compra sea procesada correctamente y no sea cancelada.

**¿QUÉ?**
Permitir la ejecución de pagos electrónicos asociados a los pedidos dentro de un tiempo determinado.

**¿CÓMO?**
Mediante la integración con la pasarela de pago Wompi, el sistema procesa la transacción, valida que se realice dentro del tiempo máximo permitido, registra la información del pago y actualiza su estado según la respuesta recibida (aprobado, rechazado o pendiente).

**¿PARA QUÉ?**
Para garantizar la validez de las transacciones, evitar pedidos sin pago y asegurar la continuidad del proceso de compra.