# Consultar perfil

## Historia de Usuarios

**Como**  usuario o un administrador consulta la información detallada de un perfil específico, incluyendo datos personales, estado de la cuenta y direcciones registradas, para verificar o auditar la información.


**Quiero** Enviando una solicitud GET con el ID del usuario en la URL y el token JWT  en el encabezado de autorización. El sistema verifica que el solicitante tenga permiso para ver ese perfil (el propio usuario o un administrador),            localiza el registro en la base de datos y retorna los datos del usuariosin incluir la contraseña. Si el ID no existe, retorna error 404.

**Para** Para que el usuario pueda revisar y confirmar que su información personal   está correcta y actualizada, y para que los administradores puedan gestionar           y auditar cuentas cuando sea necesario, por ejemplo al resolver un reclamo o verificar un pedido asociado a ese cliente.
