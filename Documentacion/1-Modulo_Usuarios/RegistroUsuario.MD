# Registro de Usuarios

## Historia de Usuarios

**Como** persona que desea comprar en FarmaRest crea su cuenta en la plataforma          proporcionando su información personal. El sistema valida que los datos sean correctos, que el correo no esté previamente registrado y que la  contraseña cumpla los requisitos de seguridad antes de crear la cuenta.


**Quiero**  Completar y enviar un formulario con nombre, correo electrónico,            contraseña, teléfono y dirección mediante una solicitud POST. El sistema            verifica que el correo no esté duplicado, cifra la contraseña con un            algoritmo de hashing seguro (bcrypt) y persiste el nuevo usuario con estado activo. Si el correo ya existe, retorna error 409.
**Para**  que cualquier persona pueda incorporarse como cliente de la drogueríade forma digital, accediendo a la compra de medicamentos e insumos médicos  desde cualquier lugar. El registro es el primer paso necesario para poder realizar pedidos, guardar direcciones de entrega y mantener un historial de compras en la plataforma.