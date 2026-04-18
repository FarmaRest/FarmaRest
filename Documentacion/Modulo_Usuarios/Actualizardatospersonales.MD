# Actualizar Datos personales

## Historia de Usuarios

**Como**  El usuario actualiza uno o varios campos de su información personal en el   sistema, como número de teléfono, dirección de entrega o contraseña. El           sistema aplica las reglas de negocio correspondientes, como la restricción   de no cambiar el correo más de una vez cada 6 meses.

**Quiero** enviar una solicitud PUT con el ID del usuario en la URL y los campos   a modificar en el cuerpo de la solicitud. El sistema valida cada campo,            verifica reglas de negocio (historial de correos, contraseñas anteriores),      cifra la nueva contraseña si aplica, y persiste los cambios. Retorna el            perfil actualizado o el error correspondiente si alguna validación falla.


**Para** que el usuario pueda mantener su información vigente y correcta en  la plataforma, garantizando que las entregas lleguen a la dirección correcta,           que las comunicaciones lleguen al contacto adecuado y que su contraseña            permanezca segura y actualizada conforme a las políticas del sistema.
