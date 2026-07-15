# Despliegue seguro y compliance de Fenix

Este procedimiento es exclusivo del proyecto GCP de Fenix. No se deben crear
secretos, buckets, cuentas de servicio ni permisos en proyectos compartidos.

## Datos legales obligatorios

Antes de producción deben configurarse `LEGAL_COMPANY_NAME`, `LEGAL_TAX_ID`,
`LEGAL_ADDRESS` y `PRIVACY_EMAIL` con datos validados por el responsable.

## Rotación sin parada

1. Crear en Secret Manager del proyecto Fenix los secretos listados en
   `fenix/secrets.py`. Conceder `roles/secretmanager.secretAccessor` únicamente
   a la cuenta de servicio de App Engine de este proyecto.
2. Base de datos: crear credencial nueva, desplegar y validar; revocar la
   anterior sólo después.
3. SMTP/Resend, WhatsApp y Google: emitir tokens nuevos, desplegar, probar y
   revocar los antiguos.
4. Django: establecer la nueva `SECRET_KEY`. Si deben conservarse sesiones,
   desplegar temporalmente la clave anterior mediante `SECRET_KEY_FALLBACKS`,
   esperar el TTL de sesión y retirarla.
5. Invalidar las 67 sesiones, el token API y el TOTP que aparecieron en los
   volcados históricos. El usuario afectado por TOTP debe volver a enrolarse.
6. Tras la rotación, reescribir el historial Git para eliminar secretos y
   volcados; coordinar un reclonado del repositorio para todo el equipo.

## Almacenamiento privado

Crear `${GOOGLE_CLOUD_PROJECT}-fenix-private` con Public Access Prevention y
Uniform bucket-level access. Sólo la cuenta de servicio de Fenix tendrá acceso.
Los documentos nuevos usan este bucket y se descargan a través de una vista
autenticada. Migrar los documentos antiguos en segundo plano antes de retirar
el acceso anterior.

## Verificaciones previas al despliegue

- `python manage.py check --deploy`
- `python manage.py migrate --plan`
- `python manage.py test`
- Confirmar que `gcloud meta list-files-for-upload` no muestra `.env`, dumps,
  bases de datos, backups, logs ni credenciales.
- Probar login, 2FA, OTP, chat, webhook firmado, pedidos y descarga documental.
- Ejecutar `python manage.py purge_expired_personal_data` en modo dry-run.

## Operación RGPD

- Mantener un Registro de Actividades de Tratamiento para cuentas/pedidos,
  CRM/contacto, WhatsApp, asistente, seguridad y auditoría.
- Formalizar contratos de encargo y documentar localización/transferencias con
  Google, proveedor de base de datos, Meta y proveedor de correo.
- Registrar cada solicitud de derechos y aplicar acceso, rectificación o
  supresión de forma coordinada en cuentas, CRM, leads, IA, WhatsApp y backups.
- Programar mensualmente `purge_expired_personal_data --apply` tras revisar el
  dry-run y cualquier obligación de bloqueo legal.
- Revisar incidentes y accesos a secretos mediante Cloud Audit Logs.
