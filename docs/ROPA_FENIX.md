# Registro de Actividades de Tratamiento — Fenix

Documento técnico inicial. El responsable debe validar identidad, bases
jurídicas, contratos, ubicaciones y plazos antes de aprobarlo formalmente.

| Actividad | Interesados y datos | Finalidad/base | Destinatarios | Conservación |
|---|---|---|---|---|
| Cuentas y pedidos B2B | Identidad, contacto, empresa, NIF/CIF, entrega, pedidos y documentos | Contrato, medidas precontractuales y obligaciones legales | Google Cloud, base de datos, correo y personal autorizado | Relación contractual y plazos fiscales/mercantiles |
| Contacto y CRM | Nombre, email, teléfono, empresa, mensajes, canal y seguimiento | Consentimiento, medidas precontractuales o interés legítimo documentado | CRM interno, correo, Meta cuando se usa WhatsApp | Revisión a 2 años de inactividad |
| Asistente inteligente | Contacto verificado, consultas, respuestas y cuota | Consentimiento | Google Gemini y CRM interno | Revisión a 2 años; OTP no verificado 30 días |
| Seguridad y acceso | IP, dispositivo, sesiones, intentos y acciones | Interés legítimo en proteger el servicio | Google Cloud Logging y administradores autorizados | 1 año seguridad; 2 años auditoría |
| Comunicaciones comerciales | Datos de contacto y evidencia de consentimiento | Consentimiento | Proveedor de correo | Hasta retirada o fin de finalidad |

## Controles y responsabilidades

- Responsable: completar `LEGAL_COMPANY_NAME`, `LEGAL_TAX_ID`, `LEGAL_ADDRESS`
  y `PRIVACY_EMAIL`.
- Encargados: conservar DPA, región, subencargados y mecanismo de transferencia
  de Google Cloud/Gemini, proveedor PostgreSQL, Meta/WhatsApp y correo.
- Acceso: administradores y personal comercial según RBAC; revisiones
  trimestrales de permisos.
- Supresión: ejecución mensual del comando de retención y gestión de
  `PrivacyRequest` desde administración.
- Incidentes: preservar evidencias, contener credenciales, valorar riesgo y
  escalar al responsable para decidir notificación a AEPD/interesados.
- Revisión: anual y ante cambios de proveedor, finalidad, datos o arquitectura.
