# Configuración de Google Drive OAuth 2.0

## Descripción
Los scripts de VANTAGE ahora usan OAuth 2.0 Desktop para autenticación con Google Drive en lugar de Service Accounts. Esto permite una autenticación más flexible con tu cuenta personal de Google.

## Requisitos previos

### 1. Instalar librerías necesarias
```bash
pip install google-api-python-client google-auth-oauthlib
```

### 2. Crear credenciales OAuth en Google Cloud Console

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un nuevo proyecto o seleccionar uno existente
3. Habilitar la API de Google Drive:
   - Navegar a "APIs & Services" > "Library"
   - Buscar "Google Drive API" y habilitarla
4. Configurar pantalla de consentimiento OAuth:
   - Navegar a "APIs & Services" > "OAuth consent screen"
   - Seleccionar "External" (para cuentas personales)
   - Completar el formulario básico
5. Crear credenciales OAuth 2.0:
   - Navegar a "APIs & Services" > "Credentials"
   - Click en "Create Credentials" > "OAuth client ID"
   - Tipo de aplicación: "Desktop app"
   - Nombre: "VANTAGE Scripts"
   - Descargar el archivo JSON (se llamará `client_secret_...json`)

## Configuración

### Variables de entorno
```bash
# Para update_triggers_json.py (SKILLS MANIFEST)
export GOOGLE_OAUTH_CREDENTIALS_PATH='/ruta/a/client_secret_...json'

# Para export_bootloader_pages.py (páginas Notion)
export GOOGLE_OAUTH_CREDENTIALS_PATH='/ruta/a/client_secret_...json'
```

### Archivo de token
El script creará automáticamente un archivo `token_drive.json` la primera vez que se autentique. Este archivo contiene el token de acceso y refresh token para futuras autenticaciones sin necesidad de interacción del usuario.

## Uso

### Primera ejecución (autenticación interactiva)
```bash
cd "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts"
python3 update_triggers_json.py
```

El script abrirá una ventana del navegador para que autorices el acceso a Google Drive. Después de autorizar, el script guardará el token automáticamente.

### Ejecuciones posteriores (automático)
```bash
python3 update_triggers_json.py
```

El script usará el token guardado en `token_drive.json` sin necesidad de interacción.

## Permisos necesarios

Los scripts usan el scope `https://www.googleapis.com/auth/drive.file` que permite:
- Crear archivos en Google Drive
- Editar archivos creados por la aplicación
- No permite acceso a todos los archivos de Drive (solo los creados por la app)

## Carpetas en Google Drive

- **VANTAGE_Skills_Manifest**: Para `update_triggers_json.py` (SKILLS MANIFEST)
- **VANTAGE_Bootloader_Exports**: Para `export_bootloader_pages.py` (páginas Notion)

## Solución de problemas

### Error: "Google Drive OAuth no configurado"
Asegúrate de haber configurado la variable de entorno:
```bash
export GOOGLE_OAUTH_CREDENTIALS_PATH='/ruta/a/client_secret_...json'
```

### Error: "Librerías de Google Drive no instaladas"
Instala las librerías necesarias:
```bash
pip install google-api-python-client google-auth-oauthlib
```

### Token expirado
El script debería refrescar automáticamente el token si está expirado. Si hay problemas, borra el archivo `token_drive.json` y vuelve a autenticarte.

### Error de autenticación
1. Verifica que el archivo `client_secret_...json` sea correcto
2. Asegúrate de que la API de Google Drive esté habilitada en Google Cloud Console
3. Verifica que la pantalla de consentimiento OAuth esté configurada correctamente

## Seguridad

- **Mantén seguro el archivo `client_secret_...json`**: No lo compartas ni lo subas a repositorios públicos
- **Token file**: El archivo `token_drive.json` contiene credenciales sensibles, añádelo a `.gitignore`
- **Permisos mínimos**: El script usa solo el scope necesario (`drive.file`) para minimizar riesgos