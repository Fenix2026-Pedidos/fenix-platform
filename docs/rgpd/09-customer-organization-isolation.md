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
- una cuenta sin pertenencia activa no accede a pedidos;
- una empresa suspendida falla de forma cerrada;
- el modelo impide guardar un pedido con cliente y organización distintos;
- listado, detalle, cancelación y descarga documental usan la organización;
- los pedidos recurrentes usan el mismo límite organizativo.

## Evidencia

La suite completa local ejecuta 53 pruebas correctamente, incluidas siete
pruebas de aislamiento y operación segura. Se usa SQLite temporal y datos
sintéticos; producción no se consulta ni modifica.

## Límites y trabajo pendiente

Esta fase todavía no equivale a aislamiento completo en profundidad:

- falta extender `organization_id` a CRM, notificaciones, WhatsApp, IA y
  cualquier otro dato que finalmente sea propiedad de una empresa cliente;
- falta un manager obligatorio `for_organization()` y contexto transaccional;
- falta probar y activar PostgreSQL Row Level Security en staging;
- falta verificar que el backfill no deja pedidos con organización nula;
- falta convertir los campos a `NOT NULL` después de esa verificación;
- falta diseñar invitaciones, cambios de empresa y fusiones con doble control;
- falta auditar esos cambios administrativos.

No debe desplegarse esta migración directamente en producción. Antes se
requiere backup, restauración probada, staging PostgreSQL, conteos pre/post,
plan de rollback y revisión explícita del propietario de Fenix.
