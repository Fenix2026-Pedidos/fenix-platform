# Preparación PostgreSQL y RLS

## Estado

Se ha configurado un job de CI aislado con PostgreSQL 16 y `pgvector`. El job:

1. crea una base efímera sin credenciales reales;
2. instala dependencias;
3. aplica todas las migraciones desde cero;
4. ejecuta `audit_organization_isolation --json --strict`;
5. ejecuta la suite completa sobre PostgreSQL.

Esta configuración todavía debe ejecutarse satisfactoriamente en GitHub
Actions. No se ha conectado a producción ni se ha activado RLS.

## Condiciones obligatorias antes de RLS

No se activará Row Level Security hasta cumplir conjuntamente:

- job PostgreSQL verde de forma repetida;
- staging restaurado desde un backup anonimizado o sintético;
- `critical_total = 0` en el auditor;
- ausencia verificada de pedidos con `organization_id` nulo;
- campos convertidos a `NOT NULL` mediante migración separada;
- inventario de cada lectura, escritura, tarea y webhook que accede a pedidos;
- contexto de organización establecido con `SET LOCAL` dentro de transacción;
- rol de aplicación sin privilegios `BYPASSRLS` ni propiedad de las tablas;
- pruebas negativas directas SQL y de aplicación;
- backup y restauración probados antes de activar políticas.

## Diseño previsto

La conexión de aplicación establecerá, dentro de cada transacción:

```sql
SET LOCAL app.customer_organization_id = '<uuid>';
```

Las políticas de `orders_order` y `recurring_recurringorder` compararán su
organización con ese valor. Los procesos internos que legítimamente requieran
acceso transversal usarán un rol operativo separado, restringido y auditado;
no se reutilizará la sesión de un cliente.

## Activación gradual

1. crear funciones/políticas sin habilitar RLS;
2. ejecutar pruebas SQL bajo el rol real de aplicación;
3. habilitar RLS sólo en staging;
4. probar cliente A, cliente B, empresa suspendida y tareas internas;
5. observar errores y métricas;
6. habilitar una tabla piloto;
7. ampliar a la segunda tabla sólo después de aceptación;
8. considerar `FORCE ROW LEVEL SECURITY` tras verificar propietarios y jobs.

## Rollback

El rollback operativo deberá poder:

```sql
ALTER TABLE orders_order DISABLE ROW LEVEL SECURITY;
ALTER TABLE recurring_recurringorder DISABLE ROW LEVEL SECURITY;
```

Además:

- revertir la versión de aplicación;
- conservar las columnas y el backfill para evitar pérdida de datos;
- no borrar organizaciones ni membresías;
- registrar quién autorizó el rollback y por qué;
- repetir el auditor antes de un nuevo intento.

La desactivación de RLS es sólo una salida de emergencia. El scoping de
aplicación seguirá activo durante el rollback.
