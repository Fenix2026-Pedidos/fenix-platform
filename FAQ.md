# ❓ PREGUNTAS FRECUENTES (FAQ) - FENIX

## Respuestas a las preguntas más comunes

---

## 🔐 SEGURIDAD Y AUTENTICACIÓN

### P: ¿Por qué necesito verificar mi email y esperar aprobación?

**R:** Por dos razones importantes:

1. **Verificación de Email**: Confirma que el email es tuyo y funciona
2. **Aprobación de Admin**: Evita que bots, spam y usuarios no autorizados accedan

Esto protege a todo el ecosistema Fenix de:
- Registros automáticos masivos (bots)
- Cuentas spam
- Abuso de plataforma
- Actividad maliciosa

Es parte de nuestro sistema de **doble puerta de seguridad**.

---

### P: ¿Cuánto tiempo tarda la aprobación?

**R:** Típicamente **24-48 horas**.

**Desglose:**
- Lunes a viernes: Usualmente < 24 horas
- Fines de semana/festivos: Puede tomar más tiempo
- Picos de registros: Ocasionalmente hasta 48 horas

Si pasaron 3 días sin respuesta, contacta: **soporte@plataformafenix.com**

---

### P: ¿Qué significa cada estado de mi cuenta?

**R:** Tu cuenta puede estar en estos estados:

| Estado | Qué significa | Puedo loguearme? |
|--------|---------------|-----------------|
| 🟡 **pending** | Esperando aprobación del admin | ❌ No |
| 🟢 **active** | Aprobado y listo | ✅ Sí |
| 🔴 **rejected** | Tu solicitud fue rechazada | ❌ No |
| ⛔ **disabled** | Tu cuenta fue deshabilitada | ❌ No |

---

### P: Mi cuenta fue rechazada. ¿Qué puedo hacer?

**R:** Si tu cuenta fue rechazada:

1. **Revisa tu email**: Debería tener instrucciones
2. **Contacta soporte**: Explica tu caso a **soporte@plataformafenix.com**
3. **Verifica datos**: Quizá tu email parecía sospechoso
4. **Intenta registrarte de nuevo**: Con información más clara

**Razones comunes de rechazo:**
- Email abusivo o temporal
- Nombre genérico (Bot-like)
- Dominio sospechoso
- Múltiples registros de la misma dirección
- Captcha mal respondido

Si crees que fue un error, por favor contacta soporte.

---

### P: ¿Mi contraseña está segura?

**R:** Sí, aplicamos:

✅ **Encriptación**: Passwords nunca se almacenan en texto plano
✅ **Hashing**: Usamos algoritmo PBKDF2 con salt
✅ **Requisitos**: Mínimo 8 caracteres, mayús/minús/números
✅ **Rate limiting**: Solo 10 intentos fallidos por hora
✅ **HTTPS**: Toda comunicación cifrada (producción)
✅ **Expiración**: Sesiones expiran tras 30 días de inactividad

---

### P: ¿Qué hacer si olvido mi contraseña?

**R:** Usa el link "¿Olvidaste tu contraseña?" en login:

1. Haz clic en el link
2. Escribe tu email
3. Recibirás email con instrucciones
4. Crea nueva contraseña
5. Intenta loguear con la nueva

Si no recibes el email:
- Revisa carpeta de spam
- Espera 5 minutos
- Intenta de nuevo
- Contacta soporte si persiste

---

### P: ¿Cómo cambio mi contraseña después de loguearme?

**R:** Una vez logueado:

1. Ve a tu perfil
2. Busca "Cambiar contraseña"
3. Ingresa tu contraseña actual
4. Ingresa la nueva contraseña (2 veces)
5. Haz clic "Guardar"

Tip: Las nuevas contraseñas deben ser diferentes de las últimas 5.

---

## 📧 EMAIL Y VERIFICACIÓN

### P: No llega el email de verificación

**R:** Sigue estos pasos:

1. **Revisa spam**: A veces llegan a "Promotional" o "Updates"
2. **Espera 5 minutos**: A veces hay delay
3. **Revisa el email**: ¿Es el correcto?
4. **Intenta reenviar**: Usa botón "Reenviar email"

Si aún no llega:
- Verifica que tu email sea **válido y único**
- Intenta con un email diferente

**Nota**: Solo puedes reenviar **3 veces por hora**.

---

### P: Hice clic en el link de verificación. ¿Qué sigue?

**R:** Después de verificar tu email:

1. ✅ Tu email se marca como **verificado**
2. 🔄 Se te redirige a **"Aprobación Pendiente"**
3. ⏳ **Esperas** a que un admin revise tu solicitud
4. 📧 Recibirás email cuando seas aprobado
5. ✅ Luego podrás loguear normalmente

---

### P: ¿Puedo cambiar mi email registrado?

**R:** Sí, pero con restricciones:

1. Ve a tu perfil
2. Haz clic "Cambiar email"
3. Ingresa el nuevo email
4. Recibirás email de verificación
5. Verifica el nuevo email
6. El cambio se completa

**Restricciones:**
- No puedes usar un email ya registrado
- El email debe ser válido
- Email nuevo debe ser verificado

---

### P: ¿Por qué recibo múltiples emails de Fenix?

**R:** Podrías recibir:

1. **Email de verificación** - Después de registrarte
2. **Email de aprobación** - Cuando te aprueban
3. **Email de rechazo** - Si es rechazada tu solicitud
4. **Notificaciones** - Si tienes configuradas
5. **Password reset** - Si solicitaste

Puedes controlar notificaciones en Configuración → Preferencias.

---

### P: Espero aprobación pero no recibí email de confirmación

**R:** Si tu cuenta fue aprobada pero no recibiste email:

**Pasos:**
1. ✅ **Revisa spam** - Busca en "Correo no deseado"
2. ✅ **Intenta loguear** - Si estás aprobado, puedes acceder
3. ✅ **Contacta soporte** - Si pasaron 24h sin confirmar
   - Email: soporte@plataformafenix.com
   - Teléfono: +34-XXX-XXXXX

**Nota técnica**: A veces el email de aprobación tarda más si hay characters especiales (ó, á, é). Sistema se auto-reenvía cada 24h.

---

## 👤 PERFIL Y DATOS PERSONALES

### P: ¿Cómo actualizo mi perfil?

**R:** Una vez logueado:

1. Haz clic en tu nombre (esquina superior derecha)
2. Selecciona "Mi Perfil"
3. Edita los campos que necesites
4. Haz clic "Guardar cambios"

Campos editables:
- ✏️ Nombre completo
- ✏️ Teléfono (si aplica)
- ✏️ Foto de perfil
- ❌ Email (requiere verificación)
- ❌ Password (requiere link separado)

---

### P: ¿Cómo elimino mi cuenta?

**R:** Para eliminar tu cuenta:

1. Ve a "Configuración"
2. Busca "Peligro" o "Datos y privacidad"
3. Haz clic "Eliminar mi cuenta"
4. Confirma que estás seguro
5. Tu cuenta se elimina **permanentemente**

**Advertencia:**
- ❌ Tu datos se borran para siempre
- ❌ No se puede recuperar
- ❌ Pedidos anteriores quedan en historial

---

### P: ¿Qué datos Fenix recopila?

**R:** Solamente:

- 📧 Email (requerido para login)
- 👤 Nombre completo (para identificación)
- 📱 Teléfono (opcional, si proporcionas)
- 🏢 Empresa (si aplica)
- 🗺️ Ubicación (si proporcionas)

**No recopilamos:**
- ❌ Historial de navegación
- ❌ Datos bancarios (procesados por pasarela)
- ❌ Ubicación GPS (excepto si registras)

Lee más: [POLÍTICA DE PRIVACIDAD](POLITICA_PRIVACIDAD.md)

---

## 🛒 ÓRDENES Y COMPRAS

### P: ¿Debo esperar aprobación antes de comprar?

**R:** **Sí, obligatorio**.

Solo usuarios **Aprobados (status=active)** pueden:
- ✅ Ver catálogo completo
- ✅ Hacer órdenes
- ✅ Hacer pagos
- ✅ Ver historial

Usuarios pendientes:
- ❌ No ven catálogo
- ❌ No pueden comprar
- ❌ Se redirigen a "aprobación pendiente"

---

### P: ¿Puedo hacer múltiples órdenes?

**R:** Sí, sin límite.

Cada orden:
- Se crea con estado "nuevo"
- Recibe número de seguimiento
- Puedes verla en "Mis órdenes"

**Límites opcionales por empresa:**
- Monto máximo por pedido
- Límite de órdenes por mes
- Productos restringidos

Contacta tu manager si tienes limitaciones.

---

### P: ¿Cómo sigo mi orden?

**R:** En tu dashboard:

1. Ve a "Mis órdenes"
2. Selecciona la orden
3. Ve los estados:
   - 📋 Nuevea
   - ⚙️ En preparación
   - 📦 Enviada
   - ✅ Entregada

Recibirás emails en cada cambio de estado.

---

## 💳 PAGOS Y FACTURACIÓN

### P: ¿Qué métodos de pago aceptan?

**R:** Fenix acepta:

- 💳 Tarjeta de crédito (Visa, MasterCard, Amex)
- 💰 Transferencia bancaria
- 🏦 Depósito bancario
- 💸 Wallet digital

**Nota**: El método disponible depende de tu país/empresa.

---

### P: ¿Es seguro pagar en Fenix?

**R:** Sí, con estas medidas:

✅ **Encriptación SSL/TLS**: Datos cifrados
✅ **PCI DSS**: Fenix cumple estándares
✅ **Procesador certificado**: Stripe, PayPal, etc.
✅ **Nos nunca almacenamos** números de tarjeta
✅ **Fraude detection**: Monitoreo 24/7
✅ **Reembolso**: Si hay error, reembolsamos

---

### P: ¿Puedo pedir factura?

**R:** Sí, automáticamente:

- 📄 Se genera con cada orden
- 📧 Te llega por email
- 📥 La descargamos desde "Mis órdenes"

Puedes descargar en:
- PDF
- Excel
- Email a contabilidad

---

## 🏢 PARA EMPRESAS

### P: ¿Cómo registro a mis empleados?

**R:** Como empresa, puedes:

1. **Invitar empleados**: Los invitas vía bulk
2. **Ellos se registran**: Usan link de invitación
3. **Auto-aprobados**: Tu dominio está whitelisted
4. **Asignar roles**: Manager asigna permisos

O contacta a tu account manager para configuración más compleja.

---

### P: ¿Mi empresa puede tener multiples admins?

**R:** Sí, en estructura:

```
Empresa Acme
├── Admin 1 (Full access)
├── Admin 2 (Reports only)
├── Manager 1 (Team 1)
├── Manager 2 (Team 2)
└── Empleados (View only)
```

Contacta soporte para cambiar estructura.

---

### P: ¿Cómo se factura a nivel empresa?

**R:** Opciones:

1. **Por orden**: C/orden genera factura
2. **Mensual**: Consolidado mes
3. **Anual**: Paquete anual con descuento

Tu account manager configura el plan.

---

## 🆘 PROBLEMAS Y TROUBLESHOOTING

### P: No puedo loguearme

**R:** Revisa en orden:

1. ❓ ¿Recordas tu email?
2. ❓ ¿Recordas tu password?
3. ✅ Usa "¿Olvidaste password?" si es necesario
4. ✅ Verifica que tu cuenta esté **aprobada** (status=active)
5. ✅ Intenta en navegador limpio (sin cache)
6. ✅ Contacta soporte si persiste

---

### P: La página se ve rota o lenta

**R:** Intenta:

1. **Refresh**: F5 o Ctrl+R
2. **Hard refresh**: Ctrl+Shift+R (limpia cache)
3. **Otro navegador**: Chrome, Firefox, Safari
4. **Otro dispositivo**: Teléfono, tablet
5. **VPN**: Si estás en red corporativa

Si persiste, contacta: **soporte@fenix.com**

---

### P: Recibo un error 403 Forbidden

**R:** Usualmente significa:

- ❌ Tu cuenta no está aprobada
- ❌ Tu sesión expiró
- ❌ No tienes permisos

**Soluciones:**
1. Logout completo
2. Limpia cookies
3. Login nuevamente
4. Si error persiste, contacta soporte

---

### P: ¿Qué hacer si olvidé mi email de registro?

**R:** Lamentablemente, si no:
- 📧 Tienes acceso al email
- 📧 Tienes confirmación de registro
- 📧 Recuerdas el nombre exacto

Debes contactar soporte con:
- Tu nombre completo
- Aproximada fecha de registro
- Empresa (si aplica)
- Teléfono para verificación

Soporte te ayudará a recuperar.

---

## 📞 CONTACTO Y SOPORTE

### P: ¿Cómo contacto al soporte de Fenix?

**R:** Opciones de contacto:

1. **Email**: soporte@plataformafenix.com
2. **Chat**: En plataforma (si disponible)
3. **Teléfono**: +34-XXX-XXXXX
4. **Horario**: Lunes-Viernes 9-17h (Hora Madrid)
5. **Ticket**: Sistema de tickets en dashboard

**Respuesta típica**: Dentro de 24-48 horas

---

### P: ¿Hay documentación técnica disponible?

**R:** Sí, tenemos:

📚 **Para Usuarios**: [GUIA_USUARIO.md](GUIA_USUARIO.md)
📚 **Para Admins**: [GUIA_ADMINISTRADOR.md](GUIA_ADMINISTRADOR.md)
📚 **Para Testers**: [GUIA_TESTING.md](GUIA_TESTING.md)
📚 **Para Developers**: [DOCUMENTACION_SEGURIDAD.md](DOCUMENTACION_SEGURIDAD.md)
📚 **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)

---

### P: ¿Cómo reporto un bug?

**R:** Usa el formulario en dashboard:

1. Ve a "Reportar problema"
2. Selecciona categoría (Bug, Feature, Otro)
3. Describe detalladamente:
   - Qué pasó
   - Qué esperabas
   - Pasos para reproducir
   - Navegador/dispositivo
   - Screenshots (si aplica)
4. Haz clic "Enviar"

Equipo revisa en 24-48h.

---

### P: ¿Hay un changelog o historial de updates?

**R:** Sí, en:
- 📜 [CHANGELOG.md](CHANGELOG.md) - Actualizaciones principales
- 🐞 [KNOWN_ISSUES.md](KNOWN_ISSUES.md) - Problemas conocidos
- 🗓️ Anuncios en dashboard - Cambios próximos

---

## 🎓 CAPACITACIÓN Y APRENDIZAJE

### P: ¿Hay videos de onboarding?

**R:** Tenemos:
- 🎥 Video: "Primeros pasos en Fenix" (5 min)
- 🎥 Video: "Cómo registrarse" (3 min)
- 🎥 Video: "Dashboard tour" (8 min)

En: [VIDEOS](https://recursos.fenix.com/videos/)

---

### P: ¿Cómo obtengo certificación?

**R:** Proceso:

1. Completa curso introductorio
2. Pasa evaluación (80% mínimo)
3. Recibes certificado digital
4. Puedes agregar a LinkedIn

Más info: [PROGRAMA_CERTIFICACION.md](PROGRAMA_CERTIFICACION.md)

---

## 📋 PREGUNTAS LEGALES

### P: ¿Cuáles son los términos de servicio?

**R:** Ver: [TERMINOS_DE_SERVICIO.md](TERMINOS_DE_SERVICIO.md)

Resumen:
- ✅ Usas Fenix según su propósito
- ✅ Respetas ley aplicable
- ✅ No haces spam/abuso
- ✅ Fenix no es responsable de terceros

---

### P: ¿Qué pasa con mis datos personales?

**R:** Ver: [POLITICA_PRIVACIDAD.md](POLITICA_PRIVACIDAD.md)

Resumen:
- 🔒 Tus datos están protegidos
- 🔒 Solo se usan para servicio
- 🔒 No se venden o comparten
- 🔒 Tienes derecho a accesarlos/borrarlos (GDPR)

---

### P: ¿Qué hacer si Fenix tiene una breach de seguridad?

**R:** En caso de brea:

1. 📧 Te notificaremos por email
2. 🔐 Te pediremos cambiar password
3. 📢 Se publicará anuncio público
4. 🛡️ Implementaremos medidas correctivas
5. 📋 Se documentará en INCIDENTES.md

---

## 🚀 ROADMAP Y FUTURO

### P: ¿Qué features vienen próximamente?

**R:** Planeado para Q1-Q2 2026:

- 🔐 Autenticación de dos factores (2FA)
- 📱 Aplicación móvil
- 🤖 Chatbot de soporte
- 📊 Reportes avanzados
- 🌐 Más idiomas

Ver: [ROADMAP.md](ROADMAP.md)

---

### P: ¿Cuándo se actualiza Fenix?

**R:** Ciclo de updates:

- 📅 **Mensuales**: Mejoras y bugfixes
- 📅 **Trimestrales**: Features nuevas
- 📅 **Announcement**: Email previo si es breaking change

---

## ✅ CONCLUSIÓN

¿No está tu pregunta? **Contacta soporte:**
- 📧 soporte@plataformafenix.com
- 💬 Chat en dashboard
- 📞 +34-XXX-XXXXX

---

**Última actualización**: 19 de febrero, 2026
**Versión**: 1.0
Para cualquier otro tema, consulta la [DOCUMENTACION_GENERAL.md](DOCUMENTACION_GENERAL.md)

¡Gracias por usar Fenix! 🚀
