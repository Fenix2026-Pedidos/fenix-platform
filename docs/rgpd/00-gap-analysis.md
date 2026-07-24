# Análisis GAP técnico de seguridad, privacidad y RGPD — Fenix

**Fecha de revisión:** 24 de julio de 2026  
**Versión revisada:** commit `9d20b61`  
**Estado:** auditoría inicial; no constituye certificación ni dictamen jurídico  
**Alcance:** revisión estática del repositorio y pruebas locales aisladas, sin acceso ni cambios en producción y sin consultar datos personales reales.

## 1. Resumen ejecutivo

Fenix ya dispone de controles útiles: autenticación con doble puerta de acceso, 2FA TOTP cifrado, RBAC, sesiones trazadas, rate limiting, secretos en Google Secret Manager, archivos privados, verificación HMAC del webhook de Meta, consentimiento en el formulario de contacto y un primer comando de retención en modo `dry-run`.

La plataforma **no está todavía técnicamente preparada para afirmar una adecuación RGPD integral**. Los principales bloqueos son:

1. Fenix puede seguir siendo **single-tenant**, pero no existe una entidad de organización cliente ni una capa uniforme que aísle los datos de cada empresa usuaria;
2. la exportación de datos personales tiene un error funcional y una consulta que podría mezclar registros de terceros;
3. las solicitudes de derechos, la retención, los incidentes, el ROPA, los riesgos y los proveedores no tienen flujos versionados y auditables;
4. existen eliminaciones físicas inmediatas sin bloqueo legal, evidencia ni coordinación con copias o proveedores;
5. algunos logs y envíos a servicios externos contienen más datos personales de los necesarios;
6. faltan decisiones y datos que debe aprobar el responsable o su asesor legal.

No se ha ejecutado ninguna eliminación ni migración y no se ha modificado producción.

## 2. Arquitectura observada

| Componente | Estado observado |
|---|---|
| Aplicación | Monolito Django 6, Python 3.12 en App Engine |
| Base de datos | PostgreSQL/Supabase en producción; SQLite opcional en desarrollo |
| Identidad | Modelo `accounts.User`, correo como identificador, estados de aprobación, RBAC |
| Archivos | Google Cloud Storage; avatares y documentos de pedidos usan almacenamiento privado |
| Secretos | Google Secret Manager mediante `fenix/secrets.py` |
| Correo | Resend o SMTP |
| Mensajería | Meta/WhatsApp Cloud API |
| IA | Google Gemini/GenAI y base vectorial `pgvector` |
| CRM auxiliar | CRM interno y webhook de Google Sheets descrito como respaldo |
| Hosting/logs | Google App Engine y salida de logs por consola |
| Tenancy | Un único tenant operativo: Fenix. Es coherente con una plataforma exclusiva |
| Organizaciones cliente | Cada empresa está implícitamente representada por un `User`; no existe `CustomerOrganization` ni membresía para varios usuarios de una empresa |
| RLS | No se encontraron políticas por organización cliente ni establecimiento de contexto PostgreSQL |

### Decisión de arquitectura aclarada

Fenix es una plataforma exclusiva de una sola entidad operadora y puede continuar como **single-tenant**. Las empresas que se registran son organizaciones cliente dentro de Fenix, no tenants SaaS independientes.

El límite de seguridad debe establecerse mediante `CustomerOrganization`:

- una organización cliente puede tener uno o varios usuarios;
- pedidos, documentos, notificaciones, leads y demás datos comerciales pertenecen a esa organización;
- un usuario sólo puede acceder a su organización;
- los administradores de Fenix conservan acceso transversal expresamente auditado;
- las políticas RLS, si se activan, se aplicarán por `customer_organization_id`.

## 3. Inventario preliminar de datos personales

Este inventario es suficiente para el GAP, pero se ampliará en `01-data-inventory.md`.

| Sistema/modelo | Datos personales principales | Observaciones |
|---|---|---|
| `accounts.User` | identidad, correo, teléfonos, empresa, cargo, NIF/CIF, direcciones fiscal y de entrega, preferencias, IP de último acceso | Núcleo de cliente y operativa |
| `EmailVerificationToken` | relación con usuario y token UUID | Caducidad 24 h; falta purga explícita |
| `SecuritySettings` | 2FA cifrado, hash de token API, configuración de sesión | El TOTP se cifra con Fernet |
| `UserSession`, `LoginHistory` | IP, agente, dispositivo, navegador, SO, localización estimada, fechas | Datos de seguridad con retención parcial |
| `ProfileAuditLog`, `AuditLog` | usuario, IP, agente, acción, valores anterior/nuevo, descripción | Puede duplicar datos completos |
| `ContactLead` | nombre, empresa, email, teléfono, mensaje, IP, agente, consentimientos | Evidencia de privacidad y marketing |
| `AILead` | nombre, email, teléfono, hash OTP, IP de consentimiento, cuota | Se replica parcialmente en CRM |
| `CRMLead`, `CRMLeadMessage` | contacto, empresa, mensajes, notas, valor, zona, historial, metadatos | Datos flexibles y duplicados |
| `WhatsAppLead` | nombre, mensaje, URL de página, estado del envío | Se replica en CRM |
| `Order`, `OrderEvent`, `OrderDocument` | cliente, historial comercial, notas y documentos | Documentos privados; conservación legal pendiente |
| `RecurringOrder` | cliente y pauta de compra | Ligado a cuenta |
| `Notification` | mensajes operativos vinculados al usuario | Sin política específica |
| `KnowledgeBase` | texto, metadatos y embeddings | Parece contener catálogo, no conversaciones; debe impedirse incorporar PII |
| Google Sheets | copia de nombre, email, teléfono, empresa y mensaje de leads | Tercero y ciclo de eliminación no documentados |
| Gemini | consulta, historial enviado por cliente web y contexto de usuario autenticado | Se envían nombre, email, teléfono, empresa y rol |
| Resend/SMTP | destinatarios y contenido de emails | Contrato, región y retención pendientes |
| Meta/WhatsApp | teléfonos, nombres y mensajes | Contrato, subencargados y transferencias pendientes |
| GCP/GCS/Logging | archivos, metadatos técnicos y logs | Configuración efectiva debe verificarse en cloud |

No se detectaron grabaciones de llamadas, biometría, datos de salud, Stripe, Twilio, Telnyx, Vapi u OpenAI en el código revisado.

## 4. Controles existentes y positivos

- Registro, verificación de correo y aprobación administrativa antes de acceso.
- Roles `super_admin`, `admin` y `user` con controles de objeto en pedidos, documentos y perfiles.
- 2FA TOTP; secreto cifrado con una clave Fernet externa.
- Tokens API almacenados mediante hash y mostrados una sola vez.
- Cookies de sesión `HttpOnly`, `SameSite=Lax`, cookies seguras, HSTS y redirección HTTPS en configuración productiva.
- Protección CSRF en formularios propios; webhook externo de Meta protegido con firma HMAC.
- Rate limiting persistente para contacto, OTP, chat, 2FA y WhatsApp.
- Avatares y documentos de pedidos en almacenamiento privado, con descarga autenticada.
- Validación de tamaño, extensión y firma básica de documentos.
- Consentimiento de privacidad obligatorio y consentimiento comercial separado en contacto.
- OTP de IA almacenado como hash.
- Secretos excluidos del repositorio y puerta CI `scripts/security_gate.py`.
- CI incluye `pip-audit`, `manage.py check` y compilación de plantillas.
- Comando de retención con modo informativo por defecto.
- Documentos iniciales de seguridad y borrador ROPA, expresamente pendientes de validación.

## 5. Hallazgos

### GAP-CRIT-01 — No existe aislamiento estructural entre organizaciones cliente

- **Severidad:** crítica
- **Impacto:** el aislamiento depende de que cada vista recuerde filtrar por `request.user`. No permite que una empresa tenga varios usuarios y un filtro omitido podría exponer datos de otra empresa.
- **Evidencia:** `Order.customer` y otros datos se vinculan directamente a `User`; no existe `CustomerOrganization`, capa central de scoping ni SQL RLS.
- **Recomendación:** transición `expand/backfill/enforce`; crear organización cliente por cada cuenta empresarial existente, membresías, managers obligatorios, contexto transaccional y RLS por organización sólo después de validar staging.
- **Archivos afectados previstos:** `accounts`, modelos comerciales de `core`, `crm`, `orders`, `recurring`, `notifications`, `whatsapp` y `ai_assistant`; middleware, servicios y migraciones.
- **Prioridad:** P0
- **Dependencias:** reglas de pertenencia y administración de empresas, inventario completo y staging PostgreSQL.
- **Pendiente:** `PENDIENTE_CLIENTE` únicamente para definir si una empresa podrá tener varios usuarios y quién puede invitarlos.

### GAP-ALTA-01 — Exportación personal defectuosa y con riesgo de incluir terceros

- **Severidad:** alta
- **Impacto:** el endpoint puede fallar porque solicita `User.created_at`, campo inexistente. Además, `Q(phone=user.phone)` puede coincidir con múltiples leads cuando el teléfono está vacío y `.values()` exporta campos internos, notas y metadatos sin lista blanca.
- **Evidencia:** `accounts/profile_views.py:119-142`.
- **Recomendación:** servicio de exportación con esquema explícito por fuente, identificación robusta, exclusión de valores vacíos, serializadores con allowlist, snapshot, hash de evidencia y pruebas negativas de terceros/tenants.
- **Prioridad:** P0, antes de usar el endpoint como respuesta formal a un derecho.
- **Dependencias:** modelo de identidad y tenant.
- **Pendiente legal:** alcance exacto, excepciones y protección de derechos de terceros.

### GAP-ALTA-02 — Módulo de derechos incompleto

- **Severidad:** alta
- **Impacto:** sólo existen acceso/portabilidad combinados, supresión y rectificación; faltan oposición, limitación, retirada del consentimiento y decisiones automatizadas. No hay plazo, validación de identidad, responsable, sistemas, terceros, comunicaciones ni evidencias.
- **Evidencia:** `core/models.py:134-161`; `accounts/profile_views.py:149-163`.
- **Recomendación:** flujo integral versionado, UUID no enumerable, estados completos, tareas, vencimientos, acciones por sistema/proveedor y cierre con evidencia.
- **Prioridad:** P0/P1
- **Dependencias:** tenants, proveedores, auditoría y retención.
- **Pendiente legal:** reglas de rechazo, limitaciones y cómputo de plazos.

### GAP-ALTA-03 — Eliminaciones físicas inmediatas sin salvaguardas

- **Severidad:** alta
- **Impacto:** administradores pueden borrar usuarios o leads inmediatamente; no existe bloqueo legal, aprobación dual, inventario de dependencias, propagación a terceros, evidencia ni reversión.
- **Evidencia:** `accounts/views.py:551-576`; `crm/views.py:121-144`.
- **Recomendación:** desactivar el borrado físico como operación normal; introducir baja lógica, solicitud, análisis de dependencias, legal hold, anonimización y purga diferida.
- **Prioridad:** P0
- **Dependencias:** flujo de derechos y políticas aprobadas.
- **Pendiente legal:** datos que deben bloquearse por obligaciones fiscales/mercantiles.

### GAP-ALTA-04 — Retención no gobernada ni automatizada de forma segura

- **Severidad:** alta
- **Impacto:** el comando actual usa tres plazos globales, borra directamente, no contempla tenant, documentos, notificaciones, tokens, conversaciones, Google Sheets, objetos, cachés, vectores, réplicas o backups. No registra ejecución, elementos, métricas, alertas, reintentos ni legal holds. No se encontró programación mensual.
- **Evidencia:** `core/management/commands/purge_expired_personal_data.py`; `fenix/settings.py:94-96`.
- **Recomendación:** políticas versionadas, `dry-run` persistente, aprobación, lotes idempotentes, bloqueo legal, adaptadores por proveedor y recibo de ejecución.
- **Prioridad:** P0/P1
- **Dependencias:** aprobación de plazos y estrategia de backups.
- **Pendiente:** `PENDIENTE_VALIDACION_LEGAL`.

### GAP-ALTA-05 — Registro de incidentes y brechas inexistente

- **Severidad:** alta
- **Impacto:** el phishing sufrido no tiene en la aplicación un expediente estructurado, cronología, decisión documentada, evidencias, afectados, medidas ni control del plazo.
- **Evidencia:** no se encontraron modelos o flujos de incidentes; sólo recomendaciones textuales en documentación.
- **Recomendación:** registro de incidentes y procedimiento; conservar sin alterar emails, alertas, logs, cronología y evidencias ya existentes.
- **Prioridad:** P0
- **Dependencias:** responsable de incidente y asesor legal.
- **Pendiente legal:** valorar si hubo violación de datos personales, riesgo y necesidad de notificación. No se concluye automáticamente.

La AEPD indica que todas las brechas deben documentarse y que la notificación a la autoridad procede cuando sea probable un riesgo, normalmente dentro de 72 horas desde que el responsable tiene constancia: <https://www.aepd.es/derechos-y-deberes/cumple-tus-deberes/medidas-de-cumplimiento/brechas-de-datos-personales-notificacion>.

### GAP-ALTA-06 — Auditoría fragmentada y con exceso de datos

- **Severidad:** alta
- **Impacto:** `AuditLog` carece de tenant, resultado, correlación, motivo y contexto estructurado; muchas operaciones relevantes no lo usan. `ProfileAuditLog` conserva valores completos anterior/nuevo. El middleware escribe IP, ruta y usuario, pero no es un registro inmutable. El detector de prompt injection registra la consulta completa.
- **Evidencia:** `core/audit.py`; `core/middleware.py:28-77`; `accounts/models.py:565-604`; `ai_assistant/services.py:42`.
- **Recomendación:** evento append-only con campos mínimos, redacción central, integridad, acceso restringido y retención propia; nunca registrar contenidos, secretos o valores personales completos.
- **Prioridad:** P0/P1
- **Dependencias:** tenant y clasificación de eventos.

### GAP-ALTA-07 — Duplicación y falta de linaje de leads

- **Severidad:** alta
- **Impacto:** un contacto puede existir en `ContactLead`, `AILead`, `WhatsAppLead`, `CRMLead`, `CRMLeadMessage` y Google Sheets. No hay identidad canónica, registro de copias ni propagación verificable de rectificación/supresión.
- **Evidencia:** `core/views.py:213-240`; `ai_assistant/views.py:84-122`; `whatsapp/views.py:38-53`; `crm/services.py:202-233`.
- **Recomendación:** sujeto canónico o tabla de enlaces, registro de sistemas afectados y adaptadores idempotentes.
- **Prioridad:** P1
- **Dependencias:** inventario, proveedores y derechos.

### GAP-ALTA-08 — Configuración legal global, incompleta y no versionada

- **Severidad:** alta
- **Impacto:** razón social predeterminada, CIF y domicilio vacíos, sin estado de aprobación, historial ni configuración por tenant.
- **Evidencia:** `fenix/settings.py:89-96`; `core/models.py:9-68`.
- **Recomendación:** configuración legal versionada y auditable con estados `pending_client_input`, `pending_legal_review`, `approved`, `rejected`, `superseded`.
- **Prioridad:** P1
- **Dependencias:** datos del responsable.
- **Pendiente:** `PENDIENTE_CLIENTE` y `PENDIENTE_VALIDACION_LEGAL`.

### GAP-ALTA-09 — ROPA, riesgos, EIPD y DPO sólo documentales

- **Severidad:** alta
- **Impacto:** `docs/ROPA_FENIX.md` es un borrador plano no versionable ni aprobable. No hay matriz de riesgos, evidencia, revisión ni decisiones independientes sobre EIPD/DPO.
- **Recomendación:** modelos versionados, bloqueo de versiones aprobadas, exportación imprimible y decisiones humanas explícitas.
- **Prioridad:** P1
- **Dependencias:** inventario y validación legal.

La necesidad de EIPD debe valorarse, no inferirse automáticamente. La AEPD describe como mínimos la actividad, necesidad/proporcionalidad, riesgos y medidas: <https://www.aepd.es/preguntas-frecuentes/2-tus-obligaciones-como-responsable-del-tratamiento/10-evaluacion-de-impacto/FAQ-0229-que-debe-incluir-una-evaluacion-de-impacto-de-proteccion-de-datos>.

### GAP-ALTA-10 — Registro de proveedores y transferencias inexistente

- **Severidad:** alta
- **Impacto:** no se pueden demostrar contratos, regiones, subencargados, DPA, garantías o fechas de revisión de GCP, Supabase, Gemini, Meta, Resend y Google Sheets.
- **Recomendación:** registro por tenant y tratamiento; toda certificación o región no verificada debe quedar pendiente.
- **Prioridad:** P1
- **Dependencias:** contratos y consolas de cada proveedor.
- **Pendiente:** `PENDIENTE_CLIENTE`.

La AEPD exige identificar la base aplicable para transferencias fuera del EEE, sin asumir garantías por el mero uso del proveedor: <https://www.aepd.es/derechos-y-deberes/cumple-tus-deberes/medidas-de-cumplimiento/garantias-transferencias-datos-personales>.

### GAP-MEDIA-01 — Envío de datos a Gemini no minimizado

- **Severidad:** media
- **Impacto:** para usuarios autenticados se inyectan ID, nombre, email, teléfono, empresa, rol y estado de perfil aunque muchas consultas de catálogo no los necesitan; el historial aportado por el navegador también se reenvía.
- **Evidencia:** `ai_assistant/services.py:54-80`; `ai_assistant/views.py:178-223`.
- **Recomendación:** contexto por finalidad, seudónimo técnico, exclusión por defecto de email/teléfono, aviso y registro del tratamiento.
- **Prioridad:** P1
- **Pendiente legal:** base jurídica, información al interesado, región, retención y uso por proveedor.

### GAP-MEDIA-02 — Google Sheets usado como “backup” sin ciclo de vida

- **Severidad:** media
- **Impacto:** nombre, email, teléfono, empresa y mensaje salen de la base principal mediante un hilo no transaccional; no hay confirmación persistente, reintento fiable, borrado coordinado ni contrato documentado.
- **Evidencia:** `crm/services.py:93-97,202-233`; `core/crm_services.py`.
- **Recomendación:** decidir si es integración operativa o copia; sustituir hilos por cola transaccional y registrar propósito, estado y eliminación.
- **Prioridad:** P1
- **Pendiente legal:** necesidad, base y conservación.

### GAP-MEDIA-03 — Consentimiento incompleto entre canales

- **Severidad:** media
- **Impacto:** contacto y AI registran evidencia, pero el formulario web de WhatsApp guarda nombre y mensaje sin evidencia explícita de información/aceptación. `marketing_emails` es una preferencia mutable sin historial de consentimiento.
- **Evidencia:** `whatsapp/views.py:22-68`; `accounts/models.py:415-463`.
- **Recomendación:** ledger de consentimientos versionado, canal, texto, finalidad, otorgamiento/retirada; revisar si WhatsApp se basa en solicitud precontractual u otra base.
- **Prioridad:** P1
- **Pendiente:** `PENDIENTE_VALIDACION_LEGAL`.

### GAP-MEDIA-04 — CSP sólo en modo Report-Only

- **Severidad:** media
- **Impacto:** una inyección compatible no sería bloqueada por el navegador; se permiten scripts y estilos inline.
- **Evidencia:** `core/middleware.py:14-25`.
- **Recomendación:** eliminar inline progresivamente, introducir nonce/hash y pasar a CSP bloqueante tras observar informes.
- **Prioridad:** P2
- **Dependencias:** pruebas de interfaz.

### GAP-MEDIA-05 — Descubrimiento global de tests roto

- **Severidad:** media
- **Impacto:** `manage.py test` no puede importar de forma estable `accounts/tests.py` y el paquete `accounts/tests/` simultáneamente; CI tampoco ejecuta la suite completa.
- **Evidencia:** colisión entre `accounts/tests.py` y `accounts/tests/`; la ejecución global produjo `ImportError`.
- **Recomendación:** consolidar tests en paquete, añadir suite completa, PostgreSQL de CI y pruebas RLS/tenant.
- **Prioridad:** P1

### GAP-MEDIA-06 — Trabajos en hilos dentro del proceso web

- **Severidad:** media
- **Impacto:** notificaciones y Google Sheets pueden perderse al terminar la instancia y provocan bloqueos en SQLite. Las pruebas de seguridad pasaron, pero registraron errores `database table is locked` en dichos hilos.
- **Evidencia:** `crm/services.py:93-97`; ejecución local de tests.
- **Recomendación:** outbox transaccional y tarea gestionada con idempotencia, reintentos y observabilidad.
- **Prioridad:** P2

### GAP-MEDIA-07 — Historial declarado pero no aplicado

- **Severidad:** media
- **Impacto:** `django-simple-history` y su middleware están configurados, pero no se encontraron campos `HistoricalRecords` en modelos. La documentación afirma más cobertura que el código.
- **Evidencia:** `fenix/settings.py:72,116`; ausencia en modelos.
- **Recomendación:** retirar la afirmación o aplicar versionado selectivo; no duplicar PII indiscriminadamente.
- **Prioridad:** P2

### GAP-MEDIA-08 — Secretos locales y artefacto histórico

- **Severidad:** media
- **Impacto:** existen `.env`, credenciales, SQLite, logs y media en el equipo local. Están ignorados y no aparecen en el índice actual, pero requieren controles de estación de trabajo. El historial contiene referencia a un backup de SQLite previamente versionado.
- **Evidencia:** inventario local, `.gitignore`, puerta de secretos e historial Git.
- **Recomendación:** cifrado de disco, permisos, limpieza controlada sólo tras preservar evidencia, rotación y revisión histórica separada.
- **Prioridad:** P1/P2
- **Restricción:** no borrar evidencias del phishing.

### GAP-MEDIA-09 — Borrados y cambios administrativos sin auditoría uniforme

- **Severidad:** media
- **Impacto:** CRM registra algunos cambios como mensajes, pero los borrados de usuario/lead y muchos cambios de permisos/configuración no generan un evento uniforme con resultado y motivo.
- **Evidencia:** `accounts/views.py`, `crm/views.py`, `core/audit.py`.
- **Recomendación:** servicio obligatorio de comandos administrativos y auditoría atómica.
- **Prioridad:** P1

### GAP-BAJA-01 — Datos flexibles sin esquema

- **Severidad:** baja
- **Impacto:** campos `metadata` y notas pueden acumular información sin finalidad, validación o clasificación.
- **Evidencia:** `ContactLead.metadata`, `CRMLeadMessage.metadata`, `KnowledgeBase.metadata`.
- **Recomendación:** esquemas JSON, allowlists, límites, retención y prohibición de secretos/categorías especiales.
- **Prioridad:** P2

## 6. Endpoints y acceso

### Controles observados

- Pedidos y documentos aplican controles por propietario o rol.
- Pedidos recurrentes filtran por `request.user`.
- CRM exige usuario administrador.
- Perfil y avatar restringen el acceso al propio usuario o administradores.
- Webhook de Meta valida HMAC.

### Riesgos pendientes

- No hay scoping de tenant en ningún endpoint.
- Administradores ven globalmente todos los usuarios, pedidos y leads.
- La exportación personal requiere corrección inmediata antes de confiar en ella.
- Los endpoints de borrado administrativo son físicos y no trazables de forma suficiente.
- Los endpoints públicos de AI/WhatsApp dependen de consentimiento/canal y rate limit, pero no de una identidad de tenant.
- Faltan pruebas sistemáticas de IDOR, mass assignment y acceso cruzado.

## 7. Backups y recuperación

No se encontró definición versionada de:

- política de backups de PostgreSQL/Supabase;
- región, cifrado, frecuencia y responsables;
- pruebas de restauración;
- periodo de expiración;
- tratamiento de datos borrados durante la vida de una copia;
- backups de GCS y Google Sheets.

El uso de Google Sheets como “backup analítico” no sustituye una política de continuidad y aumenta las copias personales.

**Estado:** `PENDIENTE_CLIENTE`.

## 8. Resultado de verificaciones locales

| Verificación | Resultado |
|---|---|
| `manage.py check` | Correcto |
| `manage.py check --deploy` | Dos advertencias causadas por el entorno de auditoría: SSL desactivado y clave deliberadamente de prueba; `app.yaml` activa SSL y producción carga la clave desde Secret Manager |
| `makemigrations --check --dry-run` | Sin cambios pendientes |
| Puerta `scripts/security_gate.py` | Correcta |
| Tests `core.tests_security whatsapp.tests_security ai_assistant.tests_security` | 7/7 correctos |
| Efectos durante tests | errores de bloqueo SQLite en hilos secundarios de CRM; no fallaron la suite, pero confirman el GAP de tareas en segundo plano |
| Suite global | no ejecutable por colisión `accounts/tests.py` / `accounts/tests/` |
| Producción | no verificada ni modificada |

La base SQLite local tiene migraciones sin aplicar; esto sólo describe el entorno local ignorado y **no permite inferir** el estado de producción.

## 9. Riesgos de regresión

1. Añadir `customer_organization_id` de una vez rompería consultas, claves únicas y jobs.
2. Activar RLS por organización antes de establecer contexto transaccional podría bloquear toda la aplicación.
3. Cambiar hard delete por baja lógica afecta consultas, unicidad de email y procesos comerciales.
4. Reducir contexto enviado a IA puede modificar la calidad de respuestas.
5. Sustituir hilos por una cola cambia consistencia y tiempos de notificación.
6. Aplicar CSP bloqueante puede romper JavaScript inline.
7. Ejecutar purgas sin políticas aprobadas puede destruir evidencia u obligaciones legales.

## 10. Conclusión de Fase 0

La implementación debe comenzar por corregir la exportación y contener borrados/logs, y después establecer `CustomerOrganization` y auditoría antes de construir ROPA, derechos, retención e incidentes. RLS por organización y purga destructiva deben permanecer desactivados mediante feature flags hasta superar staging, pruebas PostgreSQL, revisión legal y rollback.

El plan técnico detallado está en `docs/rgpd/IMPLEMENTATION_PLAN.md`.
