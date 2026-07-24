# Plan detallado de implementación técnica RGPD — Fenix

**Fecha:** 24 de julio de 2026  
**Punto de partida:** commit `9d20b61`  
**Estado:** propuesta previa a cambios estructurales  
**Principio rector:** cero cambios directos en producción, cero datos reales en pruebas y cero purgas hasta aprobación expresa.

## 1. Objetivo y límites

El objetivo es proporcionar a Fenix controles técnicos, procedimientos y evidencias que soporten la responsabilidad proactiva. El resultado no será una certificación ni sustituirá las decisiones del responsable del tratamiento o su asesor legal.

Todos los datos empresariales o jurídicos desconocidos usarán:

- `PENDIENTE_CLIENTE`;
- `PENDIENTE_VALIDACION_LEGAL`;
- estados técnicos `pending_client_input` o `pending_legal_review`.

## 2. Arquitectura propuesta

### 2.1 Nueva app `privacy_compliance`

Se propone aislar la funcionalidad transversal en una app Django sin acoplarla al CRM:

```text
privacy_compliance/
├── models/
│   ├── tenancy.py
│   ├── legal.py
│   ├── ropa.py
│   ├── risks.py
│   ├── providers.py
│   ├── rights.py
│   ├── retention.py
│   ├── incidents.py
│   └── audit.py
├── services/
│   ├── tenant_context.py
│   ├── export.py
│   ├── erasure.py
│   ├── retention.py
│   ├── providers.py
│   └── evidence.py
├── management/commands/
├── migrations/
├── tests/
├── admin.py
├── permissions.py
├── urls.py
└── views.py
```

Los dominios se separarán en servicios para evitar que vistas o señales borren datos directamente.

### 2.2 Fenix single-tenant con organizaciones cliente aisladas

Fenix continuará siendo el único tenant. Las empresas registradas se modelarán como organizaciones cliente:

1. Crear `CustomerOrganization` y `CustomerOrganizationMembership`.
2. Crear una organización cliente por cada cuenta empresarial existente mediante migración idempotente.
3. Añadir `customer_organization` inicialmente nullable a cada modelo con datos de cliente.
4. Hacer backfill por lotes, sin locks prolongados.
5. Añadir índices compuestos y restricciones por tenant.
6. Introducir un `CustomerOrganizationContextMiddleware` y managers `for_organization()`.
7. Ejecutar pruebas de aislamiento a nivel aplicación.
8. Establecer `SET LOCAL app.customer_organization_id` dentro de transacciones PostgreSQL.
9. Crear políticas RLS inicialmente sin forzar y validarlas en staging.
10. Activar `FORCE ROW LEVEL SECURITY` tabla a tabla, nunca en un único despliegue.
11. Convertir columnas a `NOT NULL` sólo después del backfill y métricas a cero.

Los administradores internos de Fenix podrán operar transversalmente mediante un contexto privilegiado explícito, de duración limitada y siempre auditado.

### 2.3 Modelo de permisos

Roles funcionales nuevos, limitados a organización cliente salvo los roles internos de Fenix:

- `privacy_viewer`;
- `privacy_operator`;
- `privacy_reviewer`;
- `privacy_officer`;
- `tenant_admin`;
- `security_incident_manager`.

Las aprobaciones jurídicas y la ejecución técnica serán permisos distintos. Ningún rol comercial podrá aprobar ROPA, políticas o purgas por defecto.

## 3. Modelos previstos

### 3.1 Organización cliente

- `CustomerOrganization`: UUID, nombre legal/comercial, identificador fiscal opcional, estado y fechas.
- `CustomerOrganizationMembership`: organización, usuario, rol, estado y vigencia.
- `CustomerOrganizationInvitation`: invitaciones de nuevos usuarios cuando se habilite.

### 3.2 Configuración legal

- `LegalConfiguration`: ámbito Fenix u organización, razón social, NIF/CIF, domicilio, privacidad, responsable, DPO, autoridad y estados.
- `LegalDocumentVersion`: tipo de documento, URL/contenido, versión, hash, aprobación, aprobador y vigencia.
- `LegalBasisDecision`: tratamiento, base propuesta, estado y evidencia.

Las versiones aprobadas serán inmutables; cualquier cambio creará una nueva versión.

### 3.3 ROPA

- `ProcessingActivity`
- `ProcessingActivityVersion`
- relaciones normalizadas con categorías de interesados, datos, finalidades, destinatarios, proveedores, transferencias, medidas y retención.

Funciones:

- borrador, revisión, aprobación, superseded;
- clonación de versión;
- historial;
- exportación HTML/PDF;
- bloqueo de versiones aprobadas.

### 3.4 Riesgos, EIPD y DPO

- `RiskAssessment`, `RiskItem`, `RiskControl`, `RiskEvidence`;
- `DPIADecision`;
- `DPODecision`;
- matrices de probabilidad e impacto configurables para Fenix.

Toda recomendación automática mostrará: **“Requiere validación del responsable o asesor legal”**.

### 3.5 Proveedores y transferencias

- `Provider`
- `ProviderService`
- `ProviderReview`
- `ProviderDocumentReference`
- `InternationalTransfer`
- `Subprocessor`

Se precargarán únicamente nombres técnicos detectados —GCP, Supabase, Gemini, Meta/WhatsApp, Resend/SMTP y Google Sheets— con estado `pending_client_input`; no se asumirán países, regiones, DPA o certificaciones.

### 3.6 Derechos

- `DataSubject`
- `DataSubjectRequest`
- `IdentityVerification`
- `RequestAction`
- `AffectedSystem`
- `ProviderAction`
- `RequestCommunication`
- `RequestEvidence`

Tipos: acceso, rectificación, supresión, oposición, limitación, portabilidad, retirada de consentimiento y decisiones automatizadas.

Estados:

```text
received → pending_verification → under_review → executing
         → pending_third_party → completed | rejected | cancelled
```

### 3.7 Retención

- `RetentionPolicy`
- `RetentionPolicyVersion`
- `LegalHold`
- `PurgePlan`
- `PurgeRun`
- `PurgeItem`
- `ProviderDeletionReceipt`

Las políticas aprobadas serán inmutables. Toda ejecución destructiva requerirá una corrida previa `dry-run` persistida y un feature flag.

### 3.8 Incidentes y brechas

- `SecurityIncident`
- `IncidentTenant`
- `IncidentDataCategory`
- `IncidentTimeline`
- `IncidentEvidence`
- `BreachRiskDecision`
- `AuthorityNotification`
- `DataSubjectCommunication`
- `CorrectiveAction`

El phishing existente se registrará sólo con referencias o copias forenses autorizadas, hashes y cadena de custodia. No se moverá, borrará ni reescribirá evidencia durante esta implementación.

### 3.9 Auditoría

Evolucionar `AuditLog` a evento append-only con:

- tenant;
- actor usuario/servicio;
- acción;
- tipo e ID opaco del recurso;
- resultado;
- fecha UTC;
- IP cuando proceda;
- correlación;
- motivo;
- metadatos mínimos redaccionados;
- hash encadenado o exportación a almacenamiento inmutable.

No guardar payloads, tokens, mensajes completos, direcciones completas ni valores anterior/nuevo sin justificación.

## 4. Migraciones previstas

Cada migración tendrá `RunPython` reversible o una estrategia compensatoria documentada.

| Paso | Migración | Comportamiento | Rollback |
|---|---|---|---|
| M1 | Crear tablas de organización cliente | Sólo expansión; sin cambiar consultas | Eliminar tablas si están vacías |
| M2 | Crear organizaciones desde cuentas existentes | Idempotente por UUID/clave estable | Borrar sólo si no tienen referencias |
| M3 | Añadir `customer_organization_id` nullable e índices | Sin bloqueo funcional | Quitar índices/columnas |
| M4 | Backfill por lotes | Sin datos reales de prueba; checkpoint | Revertir únicamente asignaciones creadas |
| M5 | Añadir configuración legal/ROPA/riesgos/proveedores | Tablas nuevas | Eliminar tablas si no hay aprobaciones |
| M6 | Añadir derechos/evidencias | Convive con `PrivacyRequest` legacy | Mantener legacy y retirar nuevas rutas |
| M7 | Añadir retención/legal hold/incidentes | Sin purga activa | Desactivar flags y conservar evidencia |
| M8 | Auditoría v2 y outbox | Doble escritura temporal | Volver al log legacy |
| M9 | Restricciones e índices compuestos | Tras verificar nulos y duplicados | Retirar constraint/índice |
| M10 | Políticas RLS por organización | Inicialmente desactivadas | `DISABLE ROW LEVEL SECURITY` y rollback de versión |
| M11 | `customer_organization_id NOT NULL` | Sólo tras aprobación técnica | Rehacer nullable si fuera necesario |
| M12 | Retirar modelos legacy | Última fase, tras periodo de convivencia | No se ejecutará sin backup y aprobación |

No se cambiará una clave única global a compuesta sin un informe previo de duplicados.

## 5. Endpoints previstos

Todas las rutas usarán UUID, permisos por organización cliente, CSRF para navegador, rate limit y auditoría.

### Autoservicio

- `POST /api/privacy/requests/`
- `GET /api/privacy/requests/<uuid>/`
- `POST /api/privacy/requests/<uuid>/verify/`
- `GET /api/privacy/requests/<uuid>/export/`
- `POST /api/privacy/consents/<purpose>/withdraw/`

### Backoffice de privacidad

- `/privacy-compliance/dashboard/`
- `/privacy-compliance/legal/`
- `/privacy-compliance/ropa/`
- `/privacy-compliance/risks/`
- `/privacy-compliance/providers/`
- `/privacy-compliance/requests/`
- `/privacy-compliance/retention/`
- `/privacy-compliance/incidents/`
- `/privacy-compliance/audit/`

### Operaciones controladas

- `POST .../approve/`
- `POST .../new-version/`
- `POST .../dry-run/`
- `POST .../execute/`
- `POST .../place-hold/`
- `POST .../release-hold/`
- `GET .../evidence/`
- `GET .../export/`

Las operaciones destructivas no se expondrán como un `DELETE` directo.

## 6. Servicios y tareas

### Exportación

- registro de solicitud;
- snapshot por tenant e identidad;
- adaptador por sistema;
- allowlist de campos;
- detección de datos de terceros;
- ZIP/JSON estructurado cifrable;
- hash y caducidad de descarga;
- evidencia sin conservar una copia más tiempo del necesario.

### Rectificación/supresión/limitación

- plan de acciones por sistema;
- dependencias y obligaciones de bloqueo;
- adaptadores locales y externos;
- idempotencia;
- recibos;
- revisión humana;
- reconciliación posterior.

### Purga mensual

1. seleccionar organización/política;
2. excluir legal holds;
3. crear `PurgePlan`;
4. guardar conteos y IDs opacos;
5. revisar/aprobar;
6. procesar por lotes;
7. reintentar fallos;
8. reconciliar proveedores;
9. generar métricas/evidencia;
10. alertar y cerrar.

Cloud Scheduler invocará una tarea autenticada o un job; no se ejecutará una purga dentro de una petición web.

### Outbox

Las notificaciones y sincronizaciones con Google Sheets/Resend/Meta pasarán por una tabla outbox y un worker gestionado. Así se elimina el uso de `threading.Thread`, se habilitan reintentos y se evita perder operaciones al terminar una instancia.

## 7. Correcciones de contención antes de la arquitectura

Primer commit funcional, todavía reversible:

1. corregir `export_personal_data`;
2. excluir teléfono vacío y usar esquema explícito;
3. añadir pruebas de no divulgación entre usuarios;
4. registrar solicitudes y exportaciones;
5. poner borrados físicos administrativos tras feature flag;
6. redactar consulta completa en logs de prompt injection;
7. dejar CSP sin cambio hasta disponer de pruebas.

Estas correcciones no requieren purgar datos ni desplegar todavía.

## 8. Pruebas previstas

### Unitarias

- estados y versionado;
- permisos;
- matrices de riesgo;
- políticas y legal holds;
- redacción de logs;
- serializadores de exportación.

### Integración PostgreSQL

- contexto de tenant;
- RLS para `SELECT/INSERT/UPDATE/DELETE`;
- fallo cerrado sin contexto;
- jobs y cuentas de servicio;
- migraciones hacia delante y atrás;
- concurrencia e idempotencia.

### Negativas

- acceso por UUID de otro tenant;
- usuario sin rol;
- teléfono/email vacío o compartido;
- exportación que intenta incluir tercero;
- mass assignment;
- purga de dato bloqueado;
- solicitud duplicada;
- fallo parcial de proveedor;
- timeout y reintento;
- secreto o PII excesiva en log/respuesta.

### E2E

- solicitud completa de cada derecho;
- aprobación de ROPA;
- incidente y decisión;
- `dry-run`/purga;
- restauración;
- rollback de aplicación y RLS.

Los fixtures serán sintéticos y marcados como prueba.

## 9. Feature flags

- `PRIVACY_MODULE_ENABLED`
- `CUSTOMER_ORGANIZATION_ENFORCEMENT_ENABLED`
- `RLS_ENFORCEMENT_ENABLED`
- `RIGHTS_V2_ENABLED`
- `HARD_DELETE_DISABLED`
- `RETENTION_DRY_RUN_ENABLED`
- `RETENTION_APPLY_ENABLED`
- `COMPLIANCE_OUTBOX_ENABLED`
- `CSP_ENFORCEMENT_ENABLED`

Los flags de purga y RLS estarán desactivados por defecto.

## 10. Despliegue sin interrupción

1. backup y prueba de restauración en entorno autorizado;
2. staging con PostgreSQL equivalente;
3. migraciones de expansión;
4. backfill y verificación;
5. aplicación con lectura compatible;
6. doble escritura y métricas;
7. pruebas tenant/RLS;
8. activación por tabla y organización piloto;
9. smoke tests;
10. periodo de observación;
11. constraints finales;
12. retirada de legado en otro despliegue.

No se modificará la cuenta de facturación ni se compartirán recursos GCP con otros proyectos.

## 11. Rollback

### Aplicación

- mantener versión anterior desplegable;
- desactivar flags sin migración;
- no eliminar campos legacy durante convivencia.

### Base de datos

- migraciones de expansión reversibles;
- backfills con marca de procedencia;
- índices concurrentes cuando proceda;
- desactivar RLS antes de volver a una versión sin contexto de organización.

### Proveedores

- mantener integración anterior durante doble escritura;
- outbox sin borrar hasta confirmar recibo;
- adaptadores desactivables por proveedor.

### Purga

No existe rollback universal de una eliminación física. Por eso:

- `dry-run` obligatorio;
- aprobación;
- legal holds;
- lotes pequeños;
- snapshot/backup conforme a política;
- anonimización preferente cuando proceda;
- evidencia del resultado.

## 12. Fases y commits pequeños

### Fase A — Contención y base de pruebas

- A1 documentación GAP y plan;
- A2 reparar descubrimiento de tests;
- A3 asegurar exportación y borrados;
- A4 pruebas de regresión y evidencia.

**Estado local:** A1–A4 completados; pendiente de revisión y despliegue.

### Fase B — Organizaciones cliente

- B1 modelos de organización/membresía y feature flags;
- B2 columnas nullable e índices;
- B3 backfill;
- B4 managers/middleware de organización;
- B5 pruebas PostgreSQL;
- B6 RLS gradual.

**Estado local:** B1–B4 implementados para pedidos y pedidos recurrentes, con
once pruebas específicas y auditor read-only. B5–B6 permanecen pendientes.

### Fase C — Gobierno

- C1 configuración legal;
- C2 ROPA/versionado/exportación;
- C3 riesgos/EIPD/DPO;
- C4 proveedores/transferencias.

### Fase D — Operación RGPD

- D1 derechos y exportación v2;
- D2 rectificación/limitación;
- D3 supresión/anonimización;
- D4 consentimientos.

### Fase E — Retención, incidentes y auditoría

- E1 políticas/legal holds;
- E2 dry-run y outbox;
- E3 purga controlada;
- E4 incidentes/brechas;
- E5 auditoría v2.

### Fase F — Despliegue y mantenimiento

- F1 staging y carga;
- F2 rollback/restauración;
- F3 evidencias;
- F4 despliegue gradual;
- F5 mantenimiento anual.

Cada commit contendrá una sola capacidad, su migración, pruebas y actualización documental.

## 13. Estimación

Con el alcance completo y el requisito multi-tenant/RLS:

| Bloque | Estimación técnica |
|---|---:|
| Contención y base de pruebas | 3–5 días |
| Organizaciones cliente y RLS gradual | 2–3 semanas |
| Gobierno: legal, ROPA, riesgos y proveedores | 1,5–2 semanas |
| Derechos y consentimientos | 1,5–2 semanas |
| Retención, incidentes y auditoría | 1,5–2 semanas |
| Staging, rendimiento, evidencias y despliegue | 1 semana |
| **Total orientativo** | **7–10 semanas** |

Dos semanas sólo permitirían una primera entrega de contención y cimientos, no todo el alcance solicitado con pruebas, RLS, evidencias y rollback. Las validaciones del cliente/asesor legal pueden transcurrir en paralelo, pero condicionan aprobaciones y activación de purgas.

## 14. Archivos previstos

### Nuevos

- app `privacy_compliance/**`;
- migraciones por fase;
- tests unitarios/integración/E2E;
- comandos de inventario, dry-run, purga y evidencia;
- los once documentos `docs/rgpd/00...10`;
- `docs/rgpd/PENDIENTES_CLIENTE.md`;
- plantillas de exportación y procedimientos.

### A modificar

- `fenix/settings.py`, `fenix/urls.py`;
- modelos personales de todas las apps;
- middleware;
- vistas y servicios de exportación, CRM, AI y WhatsApp;
- CI;
- configuración de despliegue y scheduler.

No se modificarán secretos, credenciales ni identificadores de otros proyectos GCP.

## 15. Puertas de aprobación

No se avanzará a la siguiente puerta sin evidencia:

1. **P0 técnica:** corregir exportación y pruebas.
2. **Arquitectura:** aprobar reglas de organizaciones cliente, membresías y acceso administrativo transversal.
3. **Legal:** aprobar bases, plazos, textos y criterios de derechos.
4. **Proveedores:** contratos, regiones y transferencias.
5. **Staging:** migración, RLS, rendimiento, restauración y rollback.
6. **Producción no destructiva:** módulos y flags.
7. **Producción destructiva:** purga, sólo tras aprobación separada.

## 16. Criterio para comenzar implementación

La siguiente acción segura es la Fase A. Antes de iniciar B se necesita definir si cada empresa podrá tener varios usuarios, quién los invita y qué roles internos tendrá. Antes de cualquier purga se necesitan plazos y fundamentos `PENDIENTE_VALIDACION_LEGAL`.
