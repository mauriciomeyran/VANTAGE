# Gmail Filters Setup - Instrucciones

## Requisitos previos

1. **Crear proyecto en Google Cloud Console:**
   - Ve a [console.cloud.google.com](https://console.cloud.google.com)
   - Crea un nuevo proyecto o selecciona uno existente
   - Habilita la Gmail API:
     - Navega a "APIs & Services" > "Library"
     - Busca "Gmail API" y haz clic en "Enable"

2. **Configurar OAuth 2.0:**
   - Ve a "APIs & Services" > "Credentials"
   - Haz clic en "Create Credentials" > "OAuth client ID"
   - Si es la primera vez, configura el "OAuth consent screen":
     - Selecciona "External" (para cuentas personales)
     - Completa el formulario con información básica
     - Agrega tu email como "Test user"
   - Selecciona "Desktop application" como tipo de aplicación
   - Dale un nombre (ej: "Gmail Filters Setup")
   - Haz clic en "Create"

3. **Descargar credentials.json:**
   - En la lista de credenciales, haz clic en el icono de descarga (↓) junto al OAuth client ID que creaste
   - Guarda el archivo como `credentials.json` en este directorio: `/Users/mauriciomeyran/`

## Ejecución

Una vez que tengas `credentials.json` en el directorio:

```bash
python gmail_filters_setup.py
```

El script:
1. Abrirá un navegador para que autentiques con tu cuenta de Gmail
2. Creará las 6 etiquetas si no existen: `.Jobs`, `.finance`, `.Social`, `.Alert`, `.Services`, `.Promos`
3. Creará los 6 filtros correspondientes
4. Aplicará las etiquetas retroactivamente a todos los correos existentes que coincidan con cada filtro
5. Guardará el token en `token.json` para futuras ejecuciones sin re-autenticación

## Archivos generados

- `token.json`: Token de autenticación persistente (no compartir)
- `credentials.json`: Archivo de credenciales OAuth (no compartir, provisto por ti)

## Cuentas

- Cuenta de Gmail: mauricio.meyran@gmail.com
- Gmail personal (no Workspace)
