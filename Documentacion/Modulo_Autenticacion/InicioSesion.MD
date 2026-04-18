# Inicio de Sesión

## Historia de Usuarios

**Como** usuario ingresa sus credenciales al sistema para autenticarse y obtener acceso a las funcionalidades de la plataforma.   

**Quiero** llenar el formualrio de login que envía correo electrónico y contraseña         mediante una solicitud POST. El sistema verifica las credenciales, y si son            correctas, genera y retorna un access token JWT de corta duración y un refresh token de larga duración. Si las credenciales son incorrectas o la cuenta no existe, retorna un error 401 con mensaje descriptivo. 

**Para** Para garantizar que solo usuarios registrados y autorizados puedan acceder a la plataforma, protegiendo la información personal, el historial de pedidos            y las funciones administrativas. El token JWT generado es requerido en todas las solicitudes posteriores que accedan a recursos protegidos del sistema
**Para** garantizar que solo usuarios registrados y autorizados puedan acceder a la plataforma, protegiendo la información personal, el historial de pedidos  y las funciones administrativas. El token JWT generado es requerido en todas las solicitudes posteriores que accedan a recursos protegidos del sistema