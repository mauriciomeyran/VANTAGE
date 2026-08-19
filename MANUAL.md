# VANTAGE Scout — Manual para primer uso

Este manual está pensado para alguien que **nunca ha usado el sistema**. Sigue los pasos en orden; no necesitas conocimientos previos más allá de abrir una terminal.

---

## ¿Qué es VANTAGE Scout?

VANTAGE Scout es un **robot automatizado que busca trabajo por ti**. Imagina esto:

- **Tú normalmente**: Abres Google, entras a 20 páginas de empresas, ves qué ofertas hay, copias datos... 🥵
- **Scout**: Tú le dices "busca trabajos en páginas de carrera" y él solo hace todo eso automáticamente 🤖

**Scout hace esto:**
1. Abre un navegador (Chrome automatizado)
2. Va a sitios de empleo (LinkedIn, páginas de empresas, etc.)
3. Lee las ofertas de trabajo
4. Guarda todo en un archivo JSON organizado

### Cómo funciona Scout (visual)

```
Tú → Le das instrucciones → Scout → Navega internet → Encuentra ofertas → Te entrega JSON
         (wrappers/prompts)       (browser-use)            (Groq AI)            (archivo organizado)
```

### Formas de usar Scout

| Forma | Para quién | Qué hace |
|-------|------------|----------|
| **Interfaz web (UI)** | Primer contacto, pruebas visuales | Panel en el navegador para elegir qué buscar y ver resultados |
| **Línea de comandos (CLI)** | Uso repetido, automatización | Ejecuta el scout desde la terminal |

**Recomendación para tu primera vez:** empieza con un **dry run** (prueba sin abrir navegador) y luego usa la **interfaz web**.

---

## Tabla de contenidos

1. [Requisitos](#1-requisitos)
2. [Dónde está el proyecto](#2-dónde-está-el-proyecto)
3. [Instalación (solo la primera vez)](#3-instalación-solo-la-primera-vez)
4. [Configurar variables de entorno (.env)](#4-configurar-variables-de-entorno-env)
5. [Tu primera ejecución — paso a paso](#5-tu-primera-ejecución--paso-a-paso)
6. [Interfaz web (UI)](#6-interfaz-web-ui)
7. [Línea de comandos (CLI)](#7-línea-de-comandos-cli)
8. [Wrappers: qué puedes buscar](#8-wrappers-qué-puedes-buscar)
9. [Dónde quedan los resultados](#9-dónde-quedan-los-resultados)
10. [Configuración avanzada](#10-configuración-avanzada)
11. [Solución de problemas](#11-solución-de-problemas)
12. [Automatización (opcional)](#12-automatización-opcional)

---

## 1. Requisitos

Antes de empezar, verifica que tienes:

- **macOS, Linux o Windows** con terminal disponible
- **Python 3.11 o superior** — comprueba con:
  ```bash
  python3 --version
  ```
- **Conexión a internet** (para instalar dependencias y, en ejecuciones reales, navegar sitios web)
- **API Key de Groq** (para el motor de IA)
  - Consíguela en: https://console.groq.com/keys
  - Es gratis y tiene límites generosos

---

## 2. Dónde está el proyecto

El proyecto vive en una carpeta llamada `vantage_scout`. En esta instalación:

```
/Users/miguelpalacios/Downloads/
└── vantage_scout/          ← carpeta del proyecto
    ├── .env                ← tus claves y configuración (no compartir)
    ├── .env.example        ← plantilla de referencia
    ├── .venv/              ← entorno virtual de Python (se crea al instalar)
    ├── main.py             ← programa principal (CLI)
    ├── web_ui.py           ← interfaz web
    ├── prompts/            ← instrucciones que usa el agente
    │   ├── Prompt_Career_Sites.md
    │   ├── Prompt_LinkedIn.md
    │   └── Prompt_Aggregators.md
    ├── output/             ← aquí aparecen los JSON con resultados
    └── src/                ← código interno
```

**Importante:** los comandos CLI se ejecutan desde la **carpeta padre** (`Downloads/`), no desde dentro de `vantage_scout/`. Esto es necesario por cómo está organizado el código Python. La interfaz web sí se lanza desde dentro de `vantage_scout/`.

---

## 3. Instalación (solo la primera vez)

Abre la terminal y ejecuta estos comandos **en orden**. Solo necesitas hacerlo una vez.

### Paso 3.1 — Ir a la carpeta del proyecto

```bash
cd /Users/miguelpalacios/Downloads/vantage_scout
```

### Paso 3.2 — Crear entorno virtual

Un entorno virtual aísla las dependencias del proyecto para no mezclarlas con el resto de tu sistema.

```bash
python3 -m venv .venv
```

### Paso 3.3 — Activar el entorno virtual

Cada vez que abras una terminal nueva para usar Scout, debes activarlo:

```bash
source .venv/bin/activate
```

Verás `(.venv)` al inicio de la línea de tu terminal. Eso significa que está activo.

> **Windows (PowerShell):** usa `.venv\Scripts\Activate.ps1` en lugar de `source .venv/bin/activate`.

### Paso 3.4 — Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

### Paso 3.5 — Instalar el navegador Chromium (Playwright)

Scout usa un navegador automatizado. Este comando descarga Chromium:

```bash
playwright install chromium
```

### Paso 3.6 — (Opcional) Instalar pytest para tests

```bash
pip install pytest
```

---

## 4. Configurar variables de entorno (.env)

El archivo `.env` dentro de `vantage_scout/` guarda todas las claves y ajustes. **No lo subas a Git ni lo compartas.**

### Si aún no tienes .env

Copia la plantilla y edítala:

```bash
cd /Users/miguelpalacios/Downloads/vantage_scout
cp .env.example .env
```

### Estructura mínima del .env para Scout (plug and play)

```bash
# --- Motor de IA (Groq) ---
LLM_PROVIDER=openai_compatible
LLM_API_KEY=gsk_tu_groq_api_key_aqui
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-20b

# --- Ajustes del navegador Scout ---
BROWSER_HEADLESS=false
BROWSER_MAX_STEPS=70
LLM_COST_LIMIT=5.0
USE_CHEAP_FALLBACK=true
DOMAIN_MIN_DELAY=3.0
CHROME_USER_DATA_DIR=
```

### Variables obligatorias para Scout

| Variable | Valor requerido | Descripción |
|----------|----------------|-------------|
| `LLM_PROVIDER` | `openai_compatible` | Tipo de proveedor de IA |
| `LLM_API_KEY` | Tu API key de Groq | Empieza con `gsk_` |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | URL de la API de Groq |
| `LLM_MODEL` | `openai/gpt-oss-20b` | Modelo de IA a usar |

### Variables opcionales (otras integraciones VANTAGE)

Si usas otros scripts del ecosistema VANTAGE, puedes agregar:

```bash
# --- Layer 1: Notion + Google Drive (opcional) ---
NOTION_TOKEN=ntn_tu_token_aqui
NOTION_DB_OPPORTUNITIES=tu_db_id
NOTION_ARCHIVE_PAGE_ID=tu_page_id
NOTION_ARCHIVE_DB_ID=tu_archive_db_id

GOOGLE_OAUTH_CREDENTIALS_PATH=/ruta/a/tu/client_secret.json
GOOGLE_DRIVE_FOLDER_SKILLS=VANTAGE_Skills_Manifest
GOOGLE_DRIVE_FOLDER_BOOTLOADER=VANTAGE_Bootloader_Exports

# --- Layer 3: Gmail (opcional) ---
GMAIL_USER=tu_email@gmail.com
GMAIL_APP_PASS=tu_app_password
GMAIL_LABEL=.Jobs
```

**Nota:** Scout funciona perfectamente sin estas variables opcionales. Solo son necesarias si usas otros pipelines VANTAGE.

---

## 5. Tu primera ejecución — paso a paso

Sigue exactamente esta secuencia la primera vez.

### Paso A — Activar el entorno

```bash
cd /Users/miguelpalacios/Downloads/vantage_scout
source .venv/bin/activate
```

### Paso B — Prueba sin navegador (dry run)

Esto verifica que la instalación y el `.env` están bien **sin abrir Chromium ni gastar créditos de IA**:

```bash
cd /Users/miguelpalacios/Downloads
python vantage_scout/main.py --wrapper Prompt_Career_Sites --dry-run
```

**Resultado esperado:** verás un JSON en pantalla parecido a esto:

```json
{
  "prompt_variant": "A-weekly-unified-careersites",
  "prompt_version": "PromptA-v1.0+careersites",
  "today_date": "2026-08-18",
  "items": [],
  "audit_log": [],
  "data_quality_warnings": [],
  "reroute_candidates": []
}
```

Los `items` estarán vacíos en dry run — es normal. También se crea un archivo en `vantage_scout/output/`.

### Paso C — Verificar que el motor de IA responde

```bash
cd /Users/miguelpalacios/Downloads
source vantage_scout/.venv/bin/activate
python -c "
from vantage_scout.src.config import get_settings
from vantage_scout.src.browser_agent import build_llm
s = get_settings()
llm = build_llm(s)
print('OK — proveedor:', s.provider(), '| modelo:', s.llm_model)
"
```

Deberías ver: `OK — proveedor: openai_compatible | modelo: openai/gpt-oss-20b`

### Paso D — Primera ejecución real (opcional)

Cuando el dry run funcione, lanza una búsqueda real. Se abrirá una ventana de Chromium:

```bash
cd /Users/miguelpalacios/Downloads
python vantage_scout/main.py --wrapper Prompt_Career_Sites
```

**Importante:** La primera ejecución puede tardar **varios minutos** porque Scout tiene que:
- Abrir el navegador
- Visitar las páginas de carrera configuradas
- Navegar por cada sitio
- Extraer las ofertas que coincidan con el perfil
- Generar el reporte JSON

No cierres la terminal ni el navegador hasta que termine.

---

## 6. Interfaz web (UI)

La UI es la forma más cómoda de empezar si no te gusta la terminal.

### Cómo lanzarla

```bash
cd /Users/miguelpalacios/Downloads/vantage_scout
source .venv/bin/activate
python web_ui.py
```

Verás un mensaje como:

```
 * Running on http://127.0.0.1:5000
```

### Cómo usarla

1. Abre tu navegador (Chrome, Safari, etc.) en **http://127.0.0.1:5000**
2. Elige uno de los tres wrappers (Career Sites, LinkedIn o Aggregators)
3. Pulsa **Dry Run** para probar sin navegador, o **Ejecutar** para una búsqueda real
4. Los resultados aparecen en pantalla y se guardan en `output/`
5. La página se actualiza sola cada 30 segundos

### Detener la UI

En la terminal donde corre `web_ui.py`, pulsa `Ctrl + C`.

---

## 7. Línea de comandos (CLI)

### Sintaxis general

```bash
cd /Users/miguelpalacios/Downloads
source vantage_scout/.venv/bin/activate
python vantage_scout/main.py --wrapper <NOMBRE> [--dry-run] [--today YYYY-MM-DD]
```

### Ejemplos listos para copiar

```bash
# Career Sites — prueba rápida
python vantage_scout/main.py --wrapper Prompt_Career_Sites --dry-run

# Career Sites — búsqueda real
python vantage_scout/main.py --wrapper Prompt_Career_Sites

# LinkedIn
python vantage_scout/main.py --wrapper linkedin

# Agregadores (OCC, Indeed, etc.)
python vantage_scout/main.py --wrapper aggregators

# Dry run con fecha fija (testing)
python vantage_scout/main.py --wrapper Prompt_Career_Sites --dry-run --today 2026-08-18
```

### Alias aceptados

| Puedes escribir | Equivale a |
|-----------------|------------|
| `career_sites`, `careersites` | `Prompt_Career_Sites` |
| `linkedin` | `Prompt_LinkedIn` |
| `aggregators` | `Prompt_Aggregators` |

---

## 8. Wrappers: qué puedes buscar

Un **wrapper** es un "modo de búsqueda". Cada uno tiene su prompt en `prompts/`:

### Los 3 wrappers disponibles

| Wrapper | Qué busca | Qué páginas visita | Perfil Chrome necesario |
|---------|-----------|-------------------|:-----------------------:|
| **Prompt_Career_Sites** | Páginas de carrera oficiales | Richemont, LVMH, Kering, Gucci, Dior, Nike, Adidas, etc. | No |
| **Prompt_LinkedIn** | Vacantes en LinkedIn Jobs | Solo LinkedIn Jobs | Sí (recomendado) |
| **Prompt_Aggregators** | Portales de empleo | OCC, Indeed, Computrabajo, FashionJobs | No |

### ¿Qué hacen los prompts?

Los archivos en `prompts/` son las instrucciones que Scout sigue. Por ejemplo, `Prompt_Career_Sites.md` contiene:

- **Perfil del candidato**: Mauricio Meyrán, Visual Merchandising, Mexico City
- **Seniority aceptada**: Coordinator, Senior Coordinator, Lead, Supervisor, etc.
- **Industrias**: Luxury, Premium, Fashion, Beauty, Cosmetics
- **Exclusiones**: No puestos junior, no ventas, no ciertas empresas
- **URLs específicas**: Lista de 30 páginas de carrera de empresas de lujo

**Consejo para empezar:** usa `Prompt_Career_Sites`. Es el más sencillo y tiene menos bloqueos anti-bot.

---

## 9. Dónde quedan los resultados

Cada ejecución guarda un archivo JSON en:

```
/Users/miguelpalacios/Downloads/vantage_scout/output/
```

Nombre del archivo:

```
vantage_scout_<Wrapper>_<YYYYMMDD>.json
```

Ejemplo: `vantage_scout_Prompt_Career_Sites_20260818.json`

### Ver resultados en terminal

```bash
# Ver el JSON formateado (requiere jq instalado)
cat /Users/miguelpalacios/Downloads/vantage_scout/output/vantage_scout_*.json | jq .

# Contar cuántas vacantes encontró
cat /Users/miguelpalacios/Downloads/vantage_scout/output/vantage_scout_*.json | jq '.items | length'
```

### Estructura del JSON (PromptA-v1.0)

```json
{
  "prompt_variant": "A-weekly-unified-careersites",
  "prompt_version": "PromptA-v1.0+careersites",
  "today_date": "2026-08-18",
  "items": [
    {
      "job_id": "unique_id",
      "title": "Visual Merchandising Coordinator",
      "brand": "Richemont",
      "location": "Mexico City, CDMX",
      "apply_url": "https://...",
      "source_type": "career_page",
      "source_name": "Richemont",
      "fetch_status": "direct_apply",
      "prompt_version": "PromptA-v1.0+careersites"
    }
  ],
  "audit_log": [],
  "data_quality_warnings": [],
  "reroute_candidates": []
}
```

### Si hay errores

Scout es muy honesto. Si hay problemas, no inventa datos. Verás:

```json
{
  "items": [],
  "audit_log": [
    {
      "type": "HTTP",
      "source": "Prompt_Career_Sites",
      "message": "descripción del error"
    }
  ],
  "data_quality_warnings": [
    {
      "code": "NAVIGATION_BLOCKED",
      "severity": "high",
      "cause": "descripción del problema",
      "impact": "Zero items extracted"
    }
  ]
}
```

---

## 10. Configuración avanzada

### Cambiar proveedor de IA

Scout soporta varios proveedores. La configuración actual usa **Groq** vía API compatible con OpenAI. Alternativas en `.env`:

```bash
# Gemini
LLM_PROVIDER=gemini
GEMINI_API_KEY=tu_key
GEMINI_MODEL=gemini-2.0-flash

# OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5
```

### LinkedIn — perfil de Chrome persistente

LinkedIn suele pedir sesión iniciada. En `.env`:

```bash
CHROME_USER_DATA_DIR=/Users/tu_usuario/Library/Application Support/Google/Chrome
BROWSER_HEADLESS=false
```

Cierra Chrome completamente antes de ejecutar Scout para que no haya conflicto de perfil.

### Modo sin ventana (headless)

Para servidores o ejecución en segundo plano:

```bash
BROWSER_HEADLESS=true
```

### Control de costos y velocidad

```bash
LLM_COST_LIMIT=5.0          # límite USD por ejecución
USE_CHEAP_FALLBACK=true       # usa modelos más baratos si el límite es bajo
DOMAIN_MIN_DELAY=3.0          # segundos entre requests al mismo dominio
BROWSER_MAX_STEPS=70          # pasos máximos del agente (sube si hay timeout)
```

### Personalizar los prompts

Puedes editar los archivos en `prompts/` para:

- Cambiar el perfil del candidato
- Modificar las URLs a visitar
- Ajustar criterios de exclusión
- Agregar nuevas empresas

**Importante:** Mantén la estructura del prompt (secciones ROLE, MISSION, etc.) para que Scout pueda interpretarlo correctamente.

---

## 11. Solución de problemas

### "command not found: python" o "python3"

Usa siempre `python3` en macOS. Si creaste el venv, activa `.venv` primero.

### ModuleNotFoundError: No module named 'vantage_scout'

Estás en el directorio incorrecto. Los comandos CLI deben ejecutarse desde la **carpeta padre**:

```bash
cd /Users/miguelpalacios/Downloads   # ← aquí, no dentro de vantage_scout
python vantage_scout/main.py --wrapper Prompt_Career_Sites --dry-run
```

### LLM_BASE_URL is required / LLM_API_KEY is required

Faltan variables de Groq en `.env`. Revisa la sección 4 y asegúrate de tener:

```bash
LLM_PROVIDER=openai_compatible
LLM_API_KEY=gsk_...
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-20b
```

### Playwright not installed / Browser not found

```bash
cd /Users/miguelpalacios/Downloads/vantage_scout
source .venv/bin/activate
playwright install chromium
```

### La UI no abre en http://127.0.0.1:5000

1. Verifica que `web_ui.py` sigue corriendo en la terminal
2. Comprueba que el puerto 5000 no esté ocupado por otra app
3. Prueba reiniciar: `Ctrl+C` y vuelve a ejecutar `python web_ui.py`

### Cloudflare, CAPTCHA o bloqueos

1. Usa `BROWSER_HEADLESS=false` para ver qué pasa en el navegador
2. Sube `DOMAIN_MIN_DELAY` a `5.0` o más en `.env`
3. Para LinkedIn, configura `CHROME_USER_DATA_DIR` con sesión activa

### Timeout / el agente no termina

Aumenta pasos en `.env`:

```bash
BROWSER_MAX_STEPS=100
```

### Items vacíos después de ejecución real

Si el dry run funciona pero la ejecución real devuelve items vacíos:

1. Verifica que las URLs en el prompt sean correctas
2. Aumenta `BROWSER_MAX_STEPS` para dar más tiempo al agente
3. Usa `BROWSER_HEADLESS=false` para ver qué está haciendo el navegador
4. Revisa el `audit_log` en el JSON resultante para ver errores específicos

### Tests de verificación

```bash
cd /Users/miguelpalacios/Downloads
source vantage_scout/.venv/bin/activate
pip install pytest
pytest vantage_scout/tests/ -v
```

Es normal que falle 1 test si ya tienes `.env` completo (`test_missing_credentials`).

---

## 12. Automatización (opcional)

### Ejecutar los tres scouts seguidos

Guarda como `run_all_scouts.sh`:

```bash
#!/bin/bash
set -e

cd /Users/miguelpalacios/Downloads
source vantage_scout/.venv/bin/activate

echo "Career Sites..."
python vantage_scout/main.py --wrapper Prompt_Career_Sites

echo "LinkedIn..."
python vantage_scout/main.py --wrapper linkedin

echo "Aggregators..."
python vantage_scout/main.py --wrapper aggregators

echo "Listo. Revisa vantage_scout/output/"
```

```bash
chmod +x run_all_scouts.sh
./run_all_scouts.sh
```

### Programar ejecución diaria (cron)

```bash
crontab -e
```

Añade (ajusta la ruta si cambias de carpeta):

```cron
0 9  * * * cd /Users/miguelpalacios/Downloads && /Users/miguelpalacios/Downloads/vantage_scout/.venv/bin/python vantage_scout/main.py --wrapper Prompt_Career_Sites
0 10 * * * cd /Users/miguelpalacios/Downloads && /Users/miguelpalacios/Downloads/vantage_scout/.venv/bin/python vantage_scout/main.py --wrapper linkedin
0 11 * * * cd /Users/miguelpalacios/Downloads && /Users/miguelpalacios/Downloads/vantage_scout/.venv/bin/python vantage_scout/main.py --wrapper aggregators
```

---

## Resumen rápido (cheat sheet)

```bash
# Activar entorno (cada sesión nueva)
cd /Users/miguelpalacios/Downloads/vantage_scout && source .venv/bin/activate

# Prueba rápida sin navegador
cd /Users/miguelpalacios/Downloads
python vantage_scout/main.py --wrapper Prompt_Career_Sites --dry-run

# Interfaz web
cd /Users/miguelpalacios/Downloads/vantage_scout && python web_ui.py
# → abrir http://127.0.0.1:5000

# Búsqueda real
cd /Users/miguelpalacios/Downloads
python vantage_scout/main.py --wrapper Prompt_Career_Sites
```

---

## Soporte

Si algo falla:

1. Revisa la [sección 11 — Solución de problemas](#11-solución-de-problemas)
2. Ejecuta el dry run — si falla, el problema es instalación o `.env`
3. Revisa los archivos en `vantage_scout/output/` para ver logs de errores
4. Consulta `README.md` para un resumen aún más breve