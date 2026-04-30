# Cerrar Sesión

## Historia de Usuarios

**Como** usuario finalizo de forma explícita y segura su sesión activa dentro  del sistema, invalidando los tokens asociados para que no puedan volver a ser utilizados, incluso si alguien los interceptó previamente.


**Quiero** Enviar una solicitud POST con el token de acceso en el encabezado de        autorización. El sistema localiza la sesión activa asociada al token, elimina o invalida el refresh token en la base de datos y retorna una confirmación de cierre de sesión exitoso.


**Para** proteger la cuenta del usuario cuando termina de usar la plataforma,         especialmente en dispositivos compartidos o públicos. Garantiza que los tokens emitidos no puedan reutilizarse una vez que el usuario decide salir del sistema, previniendo accesos no autorizados.