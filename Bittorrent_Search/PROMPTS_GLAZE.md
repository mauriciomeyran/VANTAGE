# Prompts para Glaze — App de escritorio VANTAGE BitTorrent Search

Prompts optimizados y listos para ejecutar en **Agent Chat** de Glaze por Raycast, estructurados según las mejores prácticas del manual de Glaze (*Spell Out Details*, *Set Constraints*, *Sequential Building*).

---

## 📋 Guía Rápida de Preparación y Diagnóstico

### 1. Verificación del Backend en Terminal
```bash
cd ~/Documents/03\ Projects/VANTAGE/Bittorrent_Search
./scripts/vantage-search --doctor                       # Diagnóstico del sistema
./scripts/vantage-search "Oppenheimer 2023" --json | python3 -m json.tool | head -40
echo "Código de salida: $?"
```

### 2. Estado del Servicio Ollama
```bash
ollama list && curl -s http://localhost:11434/api/tags >/dev/null && echo "Ollama OK"
```

### 3. Consideraciones de Tiempos y Salud de Índices
* **Carga Inicial (Cold Start)**: La primera consulta tras iniciar Ollama puede tomar **~45s** (carga del modelo de 4.7 GB en memoria RAM/VRAM).
* **Warm Runs**: Búsquedas posteriores toman **~14s** si hay reintentos en índices caídos, y **~2.5s** cuando el backend los marca como `saltado_por_salud: true` (tras 2 fallos consecutivos).
* **Modos de Glaze**: Usa **Plan Mode** para la Fase 0 y Fase 1 (validación de arquitectura y CLI) y **Build Mode** para ajustes finos de UI/UX.

---

## 🚀 Prompts Estructurados por Fases

### PROMPT 0 — Validación de Ejecución CLI (Plan Mode)
*Objetivo: Verificar la ejecución asíncrona del binario local y lectura de JSON sin congelar la UI.*

#### 🇬🇧 English (Recomendado para el agente de Glaze)
```markdown
Before building any complex UI, verify that this Glaze app can execute a local macOS CLI binary and read its JSON output asynchronously.

Build a minimal single-window test app with the following specs:

1. UI Elements:
   - A text input field for a search phrase.
   - A "Run Search" button.
   - A secondary button labeled "Comprobar backend".
   - An output text area showing raw stdout/stderr results.
   - A status indicator (spinner + elapsed timer).

2. Execution & Data Handling:
   - When "Run Search" is clicked, execute this exact command:
     "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search" "<input_text>" --json
   - Display process exit code, total elapsed execution time, and parse stdout JSON to extract:
     `diagnostico.items_unicos` and `diagnostico.consulta_efectiva`.
   - When "Comprobar backend" is clicked, run:
     "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search" --doctor
     and display the returned JSON diagnostic report (Python, dependencies, Ollama status).

3. Constraints & Edge Cases:
   - Non-blocking execution: The CLI tool can take up to 45 seconds on cold start (loading local 4.7GB Ollama model) and ~15s on warm runs. The UI MUST remain fully responsive throughout execution.
   - If exit code != 0, display stderr in an error alert box.
   - All user-facing labels must be in Spanish (es-MX).

Do not create lists or formatting yet. Confirm if local binary execution is fully supported in this environment and specify the exact approach used.
```

#### 🇪🇸 Español
```markdown
Antes de construir ninguna interfaz compleja, verifica que esta app de Glaze pueda ejecutar una herramienta de línea de comandos local en macOS y leer su salida JSON de forma asíncrona.

Construye una app de prueba mínima con una sola ventana que haga lo siguiente:

1. Elementos de la interfaz:
   - Un campo de texto para escribir la frase de búsqueda.
   - Un botón "Ejecutar búsqueda".
   - Un segundo botón labeled "Comprobar backend".
   - Un área de texto para mostrar la salida bruta (stdout/stderr).
   - Un indicador de estado (spinner + cronómetro transcurrido).

2. Ejecución y manejo de datos:
   - Al hacer clic en "Ejecutar búsqueda", ejecuta este comando exacto:
     "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search" "<texto_ingresado>" --json
   - Muestra el código de salida del proceso, tiempo transcurrido y parsea el JSON de stdout para extraer:
     `diagnostico.items_unicos` y `diagnostico.consulta_efectiva`.
   - Al hacer clic en "Comprobar backend", ejecuta:
     "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search" --doctor
     y muestra el reporte JSON devuelto (estado de Python, dependencias y Ollama).

3. Restricciones y casos límite:
   - Ejecución no bloqueante: Puede tardar hasta 45s en cold start (cargando modelo de 4.7GB) y ~15s en warm runs. La interfaz DEBE mantenerse 100% responsiva.
   - Si el código de salida != 0, muestra el stderr en una alerta de error.
   - Todos los textos visibles para el usuario en español (es-MX).

No construyas listas ni formatos todavía. Confirma si la ejecución de binarios locales es posible y qué método se utilizó.
```

---

### PROMPT 1 — Fase 1: MVP (Plan Mode)
*Objetivo: Construcción de la interfaz principal de 3 paneles y gestión de códigos de salida.*

#### 🇬🇧 English
```markdown
Now build the main desktop application for BitTorrent search using our local CLI backend:
"/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search" "<query>" --json

Structure: Single window divided into 3 distinct sections:

1. Top Search Header:
   - Auto-focused search bar with placeholder: "Busca la serie Severance, Oppenheimer 2023, anime Frieren..."
   - Triggers search on Enter key.
   - Compact summary bar below search input displaying:
     - `diagnostico.items_unicos` (e.g., "98 resultados únicos")
     - `diagnostico.descartados_por_relevancia` ("X descartados por relevancia")
     - IMDb ID if present in JSON.
     - Effective query badge if `consulta_efectiva` != `consulta_original`: "Buscando: <consulta_efectiva>".

2. Main Results Area (Scrollable List):
   - Render items from the JSON array `resultados`.
   - Display per row: Title, Seeders, Leechers, File Size, and Source as a colored badge.
   - Preserve default sorting (Seeders descending); allow client-side column re-sorting by size or title.
   - First row must visually highlight as the recommended pick.
   - Smooth scrolling support for 100+ items.

3. Right Detail Panel (Selected Item):
   - Full Title, Seeders, Leechers, Size, Source badge.
   - Full Magnet URI (displayed truncated, fully selectable).
   - "Copiar magnet" button with temporary "¡Copiado!" confirmation feedback.
   - "Copiar título" button.

4. Exit Code & Error Handling:
   - Exit 0: Render results list normally.
   - Exit 2 (No results): Read `diagnostico.motores`. If all engines `ok: true` with 0 items, suggest broader terms or English titles. If any engine `ok: false`, highlight the failed engine and show its `error` field.
   - Exit 3 (Ollama Down): Show error state: "El servicio de IA local no responde." Include command "ollama serve" and a "Reintentar" button.
   - Exit 4 (Network/Blocked): Display "Error de conexión o bloqueo de índices".
   - Any other code: Show generic error message with stderr inside a collapsible "Detalles" disclosure.
   - `saltado_por_salud: true`: Display as "saltado" with its `motivo_salud` in diagnostics; do NOT treat as a search failure.

5. Execution Constraints:
   - Always parse stdout using `--json`. Never parse plain text or treat stderr as JSON.
   - Keep UI responsive during command runs (up to 45s cold start, 15s warm start).
   - Show indeterminate loading spinner with timer and a "Cancelar" button. Keep previous results list visible but dimmed during fresh searches.
   - Do not re-filter or re-deduplicate results: the CLI backend handles deduplication and relevance filtering.
   - All user-facing UI text in Spanish (es-MX).
```

#### 🇪🇸 Español
```markdown
Construye la aplicación principal de escritorio para búsqueda BitTorrent utilizando nuestro backend CLI local:
"/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search" "<consulta>" --json

Estructura: Una sola ventana dividida en 3 partes:

1. Encabezado de Búsqueda (Arriba):
   - Barra de búsqueda enfocada automáticamente al abrir. Placeholder: "Busca la serie Severance, Oppenheimer 2023, anime Frieren..."
   - Ejecuta la búsqueda al presionar Enter.
   - Barra de resumen compacta debajo del input mostrando:
     - `diagnostico.items_unicos` (ej. "98 resultados únicos")
     - `diagnostico.descartados_por_relevancia` ("X descartados por relevancia")
     - ID de IMDb si existe en el JSON.
     - Badge de consulta efectiva si `consulta_efectiva` != `consulta_original`: "Buscando: <consulta_efectiva>".

2. Área Principal de Resultados (Lista desplazable):
   - Renderiza elementos del array JSON `resultados`.
   - Mostrar por fila: Título, Semillas (Seeders), Descargadores (Leechers), Tamaño y Origen (Source) como badge de color.
   - Conservar orden predeterminado (semillas de mayor a menor); permitir reordenar por tamaño o nombre.
   - La primera fila debe destacarse visualmente como la opción recomendada.

3. Panel de Detalle Derecho (Elemento seleccionado):
   - Título completo, Semillas, Descargadores, Tamaño, Origen.
   - URI Magnet completo (mostrar truncado, pero seleccionable).
   - Botón "Copiar magnet" con confirmación temporal ("¡Copiado!").
   - Botón "Copiar título".

4. Manejo de Errores y Códigos de Salida:
   - Código 0: Muestra la lista de resultados normalmente.
   - Código 2 (Sin resultados): Lee `diagnostico.motores`. Si todos tienen `ok: true` y 0 ítems, sugiere menos palabras o títulos en inglés. Si alguno tiene `ok: false`, nómbralo y muestra su error.
   - Código 3 (Ollama inaccesible): Muestra mensaje "El servicio de IA local no responde", comando "ollama serve" y botón "Reintentar".
   - Código 4 (Bloqueo de red): Muestra "Error de conexión o bloqueo de índices".
   - Otro código: Mensaje breve con stderr dentro de un desplegable "Detalles".
   - `saltado_por_salud: true`: Mostrar como "saltado" con su `motivo_salud`; no contar como fallo.

5. Restricciones:
   - Usar siempre `--json` y parsear stdout. Nunca tratar stderr como datos.
   - Mantener UI responsiva durante la ejecución. Spinner con cronómetro y botón "Cancelar".
   - Todos los textos visibles en español (es-MX).
```

---

### PROMPT 2 — Fase 2: Diagnóstico, Calidad y Ajustes Avanzados (Build Mode)
*Objetivo: Panel de salud de motores, badges de calidad de video y vista de ajustes avanzados.*

#### 🇬🇧 English
```markdown
Add three enhancements to the search app while preserving all existing functionality:

1. Collapsible Diagnostics Panel (Bottom Section):
   - Collapsed by default below the results table; remains accessible even when results are empty.
   - Summary line: Raw results count, unique items, discarded by relevance, IMDb ID.
   - Table of engines from `diagnostico.motores`: Engine Name, Status (OK / FALLO if ok=false / OMITIDO if omitido=true), item count, execution latency (ms), and error text if present.

2. Quality Indicators & Badges:
   - If title contains CAM, TS, HDCAM, or HDTS: add warning badge "calidad de cámara" with tooltip explaining cinema/screener source.
   - If title contains BluRay, WEB-DL, or WEBRip: add subtle "buena calidad" badge.
   - Do NOT alter sorting order; seeders remain the primary sorting criteria.

3. Advanced Settings Window (Modal / Separate View):
   - Minimum seeders input (default: 5) -> appends `-s <n>`
   - Toggle "No descartar resultados por relevancia" (default: off) -> appends `--sin-relevancia`
   - Toggle "No consultar IMDb" (default: off) -> appends `--no-imdb`
   - Toggle "Buscar índices secuencialmente" (default: off) -> appends `--secuencial`
   - Ollama model string (default: "qwen2.5:7b") -> appends `-m <modelo>`
   - Ollama host URL (default: "http://localhost:11434") -> appends `--host <url>`
   - Index selection checkboxes (YTS, LimeTorrents, MagnetDL, EZTV, Nyaa) -> appends `--sin-motores <unchecked>`
   - Health history selector (auto, off, reset) -> appends `--salud <option>`
   - Backend path indicator (read-only) + Ollama status indicator light with a "Comprobar conexión" ping button to http://localhost:11434.
   - "Restaurar valores por defecto" button.

All UI text in Spanish (es-MX).
```

---

### PROMPT 3 — Fase 3: Historial, Menu Bar y Exportación (Build Mode)
*Objetivo: Persistencia de búsquedas pasadas, integración con barra de menú de macOS y exportación de datos.*

#### 🇬🇧 English
```markdown
Implement three productivity features:

1. Local Search History:
   - Persist the last 50 searches locally on disk.
   - Store: query string, effective query, timestamp, and result count.
   - Provide a Sidebar or "Historial" view allowing 1-click re-opening of past search results without re-running the CLI command.
   - Options to delete individual entries or clear full history.

2. macOS Menu Bar Integration:
   - Menu bar icon with a quick search popover input.
   - Submitting a query executes the search and opens/focuses the main window with results.

3. Data Export & Global Shortcut:
   - "Exportar" button supporting CSV and JSON formats via native macOS Save Dialog.
   - Global keyboard shortcut (e.g., Cmd+Shift+F) to bring the main window to focus and highlight the search bar.

All user-facing copy in Spanish (es-MX).
```

---

## 🛠️ Plantilla para Corrección de Desajustes en Glaze

Al solicitar correcciones al agente de Glaze, describe **el comportamiento esperado** de manera objetiva:

```markdown
Lo que veo: <comportamiento actual concreto>
Lo que quiero: <comportamiento esperado concreto>
Datos concretos: <código de salida, campos JSON relevantes, consulta de prueba>
No cambies: <componentes de UI o lógica que ya funcionan correctamente>
```

*Ejemplo:*
```markdown
Lo que veo: Al buscar "Severance", la lista aparece vacía pero el comando en terminal devuelve 98 resultados con código 0.
Lo que quiero: Que la lista de la interfaz renderice esos 98 resultados.
Datos concretos: exit code 0, diagnostico.items_unicos = 98, resultados.length = 98.
No cambies: La barra de búsqueda ni el panel de detalles derecho.
```
