# iCloud Mail Organizer - Instrucciones

## Diferencias con Gmail

**Importante:** iCloud NO tiene filtros automáticos como Gmail. Este script:
- ✅ Organiza correos existentes en carpetas
- ❌ NO crea filtros automáticos para correos futuros
- ❌ NO tiene categorías (Primary, Social, Promotions)
- ❌ Solo funciona una vez (debes ejecutarlo periódicamente para nuevos correos)

## Requisitos previos

### 1. Generar App-Specific Password de iCloud

iCloud requiere una contraseña específica para aplicaciones (no usa tu contraseña normal):

1. Ve a [appleid.apple.com/account/manage](https://appleid.apple.com/account/manage)
2. Inicia sesión con tu Apple ID
3. Ve a "Security" > "App-Specific Passwords"
4. Haz clic en "Generate Password"
5. Dale un nombre (ej: "Mail Organizer")
6. Copia la contraseña generada (solo aparece una vez)

### 2. Requisitos de seguridad
- Tu Apple ID debe tener **autenticación de dos factores** activada
- Necesitas tu dispositivo iOS/Mac para aprobar el acceso inicial

## Ejecución

```bash
python3 icloud_mail_organizer.py
```

El script te pedirá:
1. Tu Apple ID (email de iCloud)
2. Tu App-Specific Password (generada en el paso anterior)

## Qué hace el script

1. **Conecta a iCloud via IMAP** (`imap.mail.me.com:993`)
2. **Crea 6 carpetas** si no existen:
   - Jobs
   - Finance
   - Social
   - Alert
   - Services
   - Promos

3. **Analiza todos los correos en INBOX** y los mueve según:
   - Remitente (dominio o email específico)
   - Asunto (palabras clave)
   - Reglas de exclusión para evitar falsos positivos

4. **Reporte en consola:**
   - Carpetas creadas
   - Mensajes procesados
   - Mensajes movidos a cada carpeta

## Limitaciones de IMAP vs Gmail API

| Gmail API | IMAP (iCloud) |
|-----------|---------------|
| Filtros automáticos permanentes | Solo organización manual |
| Labels múltiples | Una carpeta por mensaje |
| Categorías inteligentes | No tiene categorías |
| Queries complejas (OR, AND, NOT) | Búsqueda básica por campo |
| Batch updates eficientes | Procesamiento mensaje por mensaje |

## Para ejecutar periódicamente

Como iCloud no tiene filtros automáticos, debes ejecutar el script periódicamente:

### Opción 1: Manual
Ejecuta el script cada semana o mes según necesites

### Opción 2: Automatizado con cron (macOS/Linux)
```bash
# Editar crontab
crontab -e

# Agregar para ejecutar cada domingo a las 2am
0 2 * * 0 cd /Users/mauriciomeyran && /opt/homebrew/bin/python3 icloud_mail_organizer.py <<EOF
tu_apple_id@icloud.com
tu_app_specific_password
EOF
```

### Opción 3: Automatizado con launchd (macOS nativo)
Crear un archivo `.plist` en `~/Library/LaunchAgents/` para ejecución programada.

## Seguridad

- **Nunca** guardes tu App-Specific Password en el código
- El script solicita la contraseña en cada ejecución (interactivo)
- Las credenciales no se guardan en disco
- Usa conexión SSL/TLS para IMAP

## Troubleshooting

**Error: Authentication failed**
- Verifica que usaste App-Specific Password, no tu contraseña normal
- Confirma que 2FA está activada en tu Apple ID
- Regenera la App-Specific Password si es necesario

**Error: SSL/TLS connection failed**
- Verifica tu conexión a internet
- Confirma que iCloud Mail está disponible

**No se mueven mensajes**
- Revisa las reglas en el script (pueden necesitar ajuste)
- Verifica que los correos coinciden con los criterios esperados
- Ejecuta con logging adicional para debug
