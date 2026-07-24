# Aislamiento de empresas cliente — Fase B

## Alcance implementado en local

Fenix sigue siendo una única aplicación. Dentro de ella, cada empresa usuaria
se representa mediante `CustomerOrganization` y sus personas mediante
`CustomerOrganizationMembership`.

La regla aplicada es:

- una empresa puede tener varios usuarios;
- cada usuario pertenece actualmente a una sola empresa;
- los roles empresariales son `owner`, `admin` y `member`;
- los administradores internos de Fenix conservan acceso transversal;
- los clientes sólo consultan pedidos y pedidos recurrentes de su empresa.

## Migración conservadora

La migración usa el patrón `expand/backfill`:

1. crea las tablas de organizaciones y membresías;
2. crea una organización distinta para cada usuario cliente existente;
3. no fusiona cuentas por nombre, dominio de email, CIF o teléfono;
4. añade `organization` nullable a pedidos y pedidos recurrentes;
5. rellena esos campos desde la membresía del cliente;
6. mantiene el campo nullable hasta auditar el backfill en staging.

Separar por defecto evita que una inferencia incorrecta mezcle datos de dos
empresas. Las fusiones futuras deberán ser explícitas, auditadas y aprobadas.

## Controles de aplicación

- las altas de clientes aprovisionan una organización aislada;
- el middleware resuelve el contexto empresarial una vez por petición;
- los querysets exigen `for_organization()` y rechazan ámbitos vacíos;
- una cuenta sin pertenencia activa no accede a pedidos;
- una empresa suspendida falla de forma cerrada;
- el modelo impide guardar un pedido con cliente y organización distintos;
- listado, detalle, cancelación y descarga documental usan la organización;
- los pedidos recurrentes usan el mismo límite organizativo.

## Mapa de titularidad aplicado

| Dominio | Ámbito actual | Motivo |
|---|---|---|
| Pedidos y documentos | Empresa cliente | Son generados y consultados por sus miembros |
| Pedidos recurrentes | Empresa cliente | Son instrucciones operativas compartidas de la empresa |
| Perfil, seguridad y sesiones | Usuario individual | No deben compartirse con compañeros |
| Notificaciones | Usuario individual | Cada entrega se dirige a una cuenta concreta |
| CRM, formularios públicos y WhatsApp | Fenix global | Sólo los administra el equipo interno de Fenix |
| Leads del asistente IA | Fenix global | Son captación comercial previa a ser cliente autenticado |

No se añadirá `organization_id` a un dominio global sólo por uniformidad. Si
alguno pasa a ser visible o editable por clientes, deberá reclasificarse antes
de exponerlo.

## Auditoría previa al despliegue

El comando siguiente es read-only:

```powershell
python manage.py audit_organization_isolation --json --strict
```

Comprueba usuarios sin membresía, pedidos sin organización, clientes sin
membresía y asociaciones cruzadas. Con `--strict` devuelve error cuando existe
alguna inconsistencia crítica y debe ejecutarse en staging antes de permitir
el despliegue.

## Evidencia

La suite completa local ejecuta 57 pruebas correctamente, incluidas once
pruebas de aislamiento, infraestructura y operación segura. Se usa SQLite temporal y datos
sintéticos; producción no se consulta ni modifica.

## Límites y trabajo pendiente

Esta fase todavía no equivale a aislamiento completo en profundidad:

- falta extender `organization_id` a CRM, notificaciones, WhatsApp, IA y
  cualquier otro dato que finalmente sea propiedad de una empresa cliente;
- falta llevar el contexto empresarial a PostgreSQL mediante variable
  transaccional para soportar RLS;
- falta probar y activar PostgreSQL Row Level Security en staging;
- falta verificar que el backfill no deja pedidos con organización nula;
- falta convertir los campos a `NOT NULL` después de esa verificación;
- falta diseñar invitaciones, cambios de empresa y fusiones con doble control;
- falta auditar esos cambios administrativos.

No debe desplegarse esta migración directamente en producción. Antes se
requiere backup, restauración probada, staging PostgreSQL, conteos pre/post,
plan de rollback y revisión explícita del propietario de Fenix.
