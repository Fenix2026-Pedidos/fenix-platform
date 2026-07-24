# Evidencias de pruebas RGPD y seguridad

## Ejecución Fase A — 24 de julio de 2026

**Entorno:** local aislado  
**Base de datos:** SQLite temporal creada y destruida por Django  
**Datos utilizados:** exclusivamente sintéticos (`example.test`)  
**Producción:** no consultada ni modificada  
**Versión base:** `dc26329`

### Controles añadidos

- exportación con lista blanca de campos;
- eliminación de la coincidencia CRM por teléfono vacío;
- exclusión de rutas internas de documentos;
- auditoría de exportaciones;
- desactivación reversible de usuarios;
- archivado reversible de leads;
- borrado físico deshabilitado por defecto;
- redacción del contenido detectado como prompt injection;
- efectos externos CRM desactivados durante tests;
- descubrimiento de tests reparado.

### Pruebas específicas

Comando:

```powershell
python manage.py test accounts.tests.test_privacy_controls --verbosity 2
```

Resultado:

```text
Ran 5 tests
OK
```

Casos:

1. la exportación responde correctamente y usa `date_joined`;
2. una cuenta con teléfono vacío no recibe leads de otra empresa;
3. la exportación genera un evento de auditoría;
4. el borrado administrativo de usuario desactiva y conserva el registro;
5. el borrado de lead archiva y conserva el registro.

### Suite completa

Primera ejecución tras reparar el descubrimiento:

```text
Found 46 test(s)
FAILED (failures=2, errors=1)
```

Los tres fallos correspondían a expectativas antiguas de `orders/tests.py`
respecto de una vista agregada que ya no existe y a un mes fijo distinto de la
fecha de creación sintética. Se actualizaron para validar el comportamiento
actual:

- el cliente ignora `client_id` ajeno y sólo ve sus pedidos;
- el administrador ve todos los pedidos;
- el filtro administrativo devuelve sólo el cliente elegido.

Ejecución final:

```powershell
python manage.py test --verbosity 1
```

Resultado:

```text
Found 46 test(s)
Ran 46 tests
OK
```

Los mensajes `Forbidden` de CSRF y firma WhatsApp son resultados esperados de
casos negativos.

### Otras verificaciones

```text
python manage.py check                         OK
python manage.py makemigrations --check        sin cambios no versionados
python scripts/security_gate.py                OK
python -m compileall                           OK
git diff --check                               OK
```

### Limitaciones

- Estas pruebas todavía no verifican organizaciones cliente ni RLS porque los
  modelos correspondientes aún no se han implementado.
- SQLite no sustituye las pruebas PostgreSQL de RLS y concurrencia.
- No se han probado contratos, regiones o borrado en proveedores externos.
- La activación de `ALLOW_HARD_DELETE=True` conserva el comportamiento físico
  antiguo únicamente como escape operacional; no deberá habilitarse en
  producción sin procedimiento aprobado.
