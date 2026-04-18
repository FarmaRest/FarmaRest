# Eliminar Cuenta

## Historia de Usuarios

**Como**  administrador elimina de forma permanente un usuario del sistema,        siempre y cuando dicho usuario no tenga pedidos activos o históricos            asociados, garantizando la integridad de los registros de la plataforma.

**Quiero** Enviar una solicitud DELETE con el ID del usuario en la URL. El sistema verifica primero que el usuario no tenga pedidos asociados en ningún estado.  Si tiene pedidos, retorna error 409 indicando que no puede eliminarse. Si no tiene pedidos, procede con la eliminación permanente del registro y            retorna confirmación de la operación.

**Para**  que los administradores puedan gestionar y depurar correctamente la      base de usuarios, retirando cuentas duplicadas, fraudulentas o inactivas que ya no deben existir en el sistema, manteniendo la base de datos limpia sin comprometer la trazabilidad de las transacciones históricas.