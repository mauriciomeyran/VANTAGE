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
     Exit code 0 means everything is fine; **exit code 66** means some check failed, so show
     the failing `checks[]` entries (`nombre` + `detalle`). Note the wrapper uses **65** when
     it cannot find the backend at all, and then stdout carries `{"error": ...}` instead. The
     two shapes are distinguishable: `.error` = wrapper, `.ok`/`.checks` = doctor report.

3. Constraints & Edge Cases:
   - Non-blocking execution: The CLI tool can take up to 45 seconds on cold start (loading local 4.7GB Ollama model) and ~15s on warm runs. The UI MUST remain fully responsive (100%) throughout execution.
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
     El código de salida 0 significa que todo está bien; el **66** significa que alguna
     comprobación falló, así que muestra las entradas `checks[]` que fallen (`nombre` +
     `detalle`). Ojo: el wrapper usa **65** cuando no encuentra el backend, y en ese caso
     stdout trae `{"error": ...}`. Las dos formas se distinguen solas: `.error` = wrapper,
     `.ok`/`.checks` = informe del doctor.

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
     - `diagnostico.motores_consultados` (e.g., "Consultados: LimeTorrents, EZTV, Nyaa"): it
       lists only the indexes actually queried, excluding category-omitted and health-skipped ones.

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
   - Exit 2 (No results): Read `diagnostico.motores` and pick the real cause, in this order:
     (1) if any engine has `saltado_por_salud: true` and `motores_consultados` is empty or
     returned nothing, explain that the health history set those indexes aside (offer
     "--salud reset") — do NOT suggest rephrasing the search;
     (2) if every consulted engine is `ok: true` with 0 items, suggest broader terms or English titles;
     (3) if any engine has `ok: false`, highlight it and show its `error` field.
   - Exit 3 (Ollama Down): Show error state: "El servicio de IA local no responde." Include command "ollama serve" and a "Reintentar" button.
   - Exit 4 (Network/Blocked): Display "Error de conexión o bloqueo de índices".
   - Any other code: Show generic error message with stderr inside a collapsible "Detalles" disclosure.
   - Codes 64 (invalid arguments), 65 (the wrapper could not find the backend; stdout carries
     `{"error": ...}`) and 66 (a doctor check failed; stdout carries `.ok`/`.checks`): show the
     matching message and, for 65 and 66, the actionable detail from the JSON rather than stderr.
   - `saltado_por_salud: true`: Display as "saltado" with its `motivo_salud` in diagnostics; do NOT treat as a search failure.

5. Execution Constraints:
   - Always parse stdout using `--json`. Never parse plain text or treat stderr as JSON.
   - Keep UI responsive during command runs (up to 45s on cold start, ~15s while a dead index is
     still being retried, ~2-3s once the backend has set it aside).
   - Show indeterminate loading spinner with timer and a "Cancelar" button. Keep previous results list visible but dimmed during fresh searches.
   - Do not re-filter or re-deduplicate results: the CLI backend handles deduplication and relevance filtering.
   - Quote the backend paths: the folder contains a space ("03 Projects"). Pass the command as a single
     quoted argument list; never assemble it with unquoted concatenation, and never modify the backend folder.
   - Non-goals: the app does NOT download torrents and does NOT open a torrent client; it only searches
     metadata and copies magnets. No analytics or telemetry of any kind.
   - All user-facing UI text in Spanish (es-MX), taken **verbatim from Annex A of the brief**
     (`MANUAL_USUARIO.md`): the labels, examples and error messages are copy to reproduce, not inspiration.
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
     - `diagnostico.motores_consultados` (ej. "Consultados: LimeTorrents, EZTV, Nyaa"): lista solo
       los índices consultados de verdad, sin los omitidos por categoría ni los saltados por salud.

2. Área Principal de Resultados (Lista desplazable):
   - Renderiza elementos del array JSON `resultados`.
   - Mostrar por fila: Título, Semillas (Seeders), Descargadores (Leechers), Tamaño y Origen (Source) como badge de color.
   - Conservar orden predeterminado (semillas de mayor a menor); permitir reordenar por tamaño o nombre.
   - La primera fila debe destacarse visualmente como la opción recomendada.
   - Desplazamiento fluido con más de 100 ítems (virtualiza la lista si hace falta).

3. Panel de Detalle Derecho (Elemento seleccionado):
   - Título completo, Semillas, Descargadores, Tamaño, Origen.
   - URI Magnet completo (mostrar truncado, pero seleccionable).
   - Botón "Copiar magnet" con confirmación temporal ("¡Copiado!").
   - Botón "Copiar título".

4. Manejo de Errores y Códigos de Salida:
   - Código 0: Muestra la lista de resultados normalmente.
   - Código 2 (Sin resultados): Lee `diagnostico.motores` y elige la causa real, en este orden:
     (1) si algún motor trae `saltado_por_salud: true` y `motores_consultados` está vacío o no
     devolvió nada, explica que el historial de salud apartó esos índices (ofrece
     "--salud reset") — NO sugieras reformular la búsqueda;
     (2) si todos los motores consultados tienen `ok: true` con 0 ítems, sugiere menos palabras o títulos en inglés;
     (3) si alguno tiene `ok: false`, nómbralo y muestra su `error`.
   - Código 3 (Ollama inaccesible): Muestra mensaje "El servicio de IA local no responde", comando "ollama serve" y botón "Reintentar".
   - Código 4 (Bloqueo de red): Muestra "Error de conexión o bloqueo de índices".
   - Otro código: Mensaje breve con stderr dentro de un desplegable "Detalles".
   - Códigos 64 (argumentos inválidos), 65 (el wrapper no encontró el backend; stdout trae
     `{"error": ...}`) y 66 (falló una comprobación del doctor; stdout trae `.ok`/`.checks`):
     muestra el mensaje correspondiente y, en 65 y 66, el detalle accionable del JSON, no el stderr.
   - `saltado_por_salud: true`: Mostrar como "saltado" con su `motivo_salud`; no contar como fallo.

5. Restricciones:
   - Usar siempre `--json` y parsear stdout. Nunca tratar stderr como datos.
   - Mantener la UI responsiva durante la ejecución (hasta 45s en arranque frío, ~15s mientras aún se
     reintenta un índice caído, ~2-3s cuando el backend ya lo ha apartado). Spinner con cronómetro y
     botón "Cancelar".
   - Citar las rutas del backend: la carpeta contiene un espacio ("03 Projects"). Pasa el comando como
     una lista de argumentos citada; nunca lo armes por concatenación sin comillas, y no modifiques la
     carpeta del backend.
   - No-objetivos: la app NO descarga torrents ni abre un cliente de torrents; solo busca metadatos y
     copia magnets. Sin analítica ni telemetría de ningún tipo.
   - Todos los textos visibles en español (es-MX), **copiados literalmente del Anexo A del brief**
     (`MANUAL_USUARIO.md`): las etiquetas, los ejemplos y los mensajes de error se reproducen, no se inventan.
```

---

### PROMPT 2 — Fase 2: Diagnóstico, Calidad y Ajustes Avanzados (Build Mode)
*Objetivo: Panel de salud de motores, badges de calidad de video y vista de ajustes avanzados.*

#### 🇬🇧 English
```markdown
Add three enhancements to the search app while preserving all existing functionality:

1. Collapsible Diagnostics Panel (Bottom Section):
   - Collapsed by default below the results table; remains accessible even when results are empty.
   - Summary line: Raw results count, unique items, discarded by relevance, IMDb ID, and
     `motores_consultados` (the indexes actually queried).
   - Table of engines from `diagnostico.motores`: Engine Name, Status (OK / FALLO if ok=false /
     OMITIDO if omitido=true / **SALTADO** if saltado_por_salud=true), item count, execution latency
     (ms), and error text if present.
   - For a SALTADO engine, show its `motivo_salud` instead of an error, and when `timeout_segundos` is
     present, say that it is a reduced-timeout probe ("sondeo").

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

4. Help Screen (in-app):
   - Separate window or section that reproduces `MANUAL_USUARIO.md`, in this exact order: what VANTAGE
     is; how to search (the five examples); how to read the results (field glossary); what to do when
     something fails (the **seven** cases below); usage tips; and the index status table.
   - The seven cases come from Annex A.4 of the brief and are: Ollama connection error; "No results
     found matching criteria"; `ModuleNotFoundError: No module named 'ollama'`; "Fallo en el
     procesamiento del LLM"; series returning nothing (EZTV needs IMDb); an unrelated result (an index
     returned a generic list); and an index stuck on [FALLO]. Cover all seven, not a selection.
   - Ground the field labels with the Annex A.2 wordings as tooltips, and close with the legal note.
   - A "Ver el manual completo" button that opens `MANUAL_USUARIO.md` in the system viewer.

All UI text in Spanish (es-MX), reproduced verbatim from Annex A of the brief (`MANUAL_USUARIO.md`).
```

#### 🇪🇸 Español
```markdown
Añade tres mejoras a la app de búsqueda sin romper nada de lo que ya funciona:

1. Panel de Diagnóstico Plegable (parte inferior):
   - Plegado por defecto bajo la tabla de resultados; accesible incluso cuando no hay resultados.
   - Línea de resumen: resultados brutos, ítems únicos, descartados por relevancia, ID de IMDb y
     `motores_consultados` (los índices realmente consultados).
   - Tabla de motores desde `diagnostico.motores`: nombre del motor, estado (OK / FALLO si ok=false /
     OMITIDO si omitido=true / **SALTADO** si saltado_por_salud=true), número de ítems, latencia (ms)
     y el texto de error si lo hay.
   - Para un motor SALTADO, muestra su `motivo_salud` en lugar de un error y, cuando venga
     `timeout_segundos`, indica que es un re-sondeo con timeout reducido ("sondeo").

2. Indicadores de Calidad y Badges:
   - Si el título contiene CAM, TS, HDCAM o HDTS: badge de aviso "calidad de cámara" con una ayuda
     emergente que explique que es una grabación de cine o screener.
   - Si el título contiene BluRay, WEB-DL o WEBRip: badge discreto "buena calidad".
   - NO alteres el orden: las semillas siguen siendo el criterio principal.

3. Ventana de Ajustes Avanzados (modal o vista aparte):
   - Campo de semillas mínimas (por defecto 5) -> añade `-s <n>`
   - Interruptor "No descartar resultados por relevancia" (por defecto, apagado) -> añade `--sin-relevancia`
   - Interruptor "No consultar IMDb" (apagado) -> añade `--no-imdb`
   - Interruptor "Buscar índices secuencialmente" (apagado) -> añade `--secuencial`
   - Modelo de Ollama (por defecto "qwen2.5:7b") -> añade `-m <modelo>`
   - URL del host de Ollama (por defecto "http://localhost:11434") -> añade `--host <url>`
   - Casillas de selección de índices (YTS, LimeTorrents, MagnetDL, EZTV, Nyaa) -> añade
     `--sin-motores <los desmarcados>`
   - Selector del historial de salud (auto, off, reset) -> añade `--salud <opción>`
   - Indicador de la ruta del backend (solo lectura) + semáforo del estado de Ollama con un botón
     "Comprobar conexión" que hace ping a http://localhost:11434.
   - Botón "Restaurar valores por defecto".

4. Pantalla de Ayuda (dentro de la app):
   - Ventana o sección aparte que reproduce el `MANUAL_USUARIO.md`, en este orden exacto: qué es
     VANTAGE; cómo buscar (los cinco ejemplos); cómo leer los resultados (glosario de campos); qué
     hacer si algo falla (los **siete** casos de abajo); consejos de uso; y la tabla de estado de los
     índices.
   - Los siete casos salen del Anexo A.4 del brief y son: error de conexión con Ollama; "No results
     found matching criteria"; `ModuleNotFoundError: No module named 'ollama'`; "Fallo en el
     procesamiento del LLM"; series que no devuelven nada (EZTV necesita IMDb); un resultado que no
     tiene que ver (un índice devolvió una lista genérica); y un índice atascado en [FALLO]. Cubre los
     siete, no una selección.
   - Usa los textos del Anexo A.2 como ayuda emergente de las etiquetas, y cierra con la nota legal.
   - Botón "Ver el manual completo" que abra `MANUAL_USUARIO.md` en el visor del sistema.

Todos los textos visibles en español (es-MX), copiados literalmente del Anexo A del brief
(`MANUAL_USUARIO.md`).
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

#### 🇪🇸 Español
```markdown
Implementa tres funciones de comodidad:

1. Historial de Búsquedas Local:
   - Guarda en disco las últimas 50 búsquedas.
   - Almacena: la frase escrita, la consulta efectiva, la fecha y el número de resultados.
   - Ofrece una barra lateral o vista "Historial" que permita reabrir con un clic los resultados de
     una búsqueda pasada, sin volver a ejecutar el comando del CLI.
   - Opciones para borrar entradas sueltas o vaciar todo el historial.

2. Integración con la Barra de Menú de macOS:
   - Icono en la barra de menú con un campo de búsqueda rápida.
   - Al enviar una consulta, se ejecuta la búsqueda y se abre o se trae al frente la ventana principal
     con los resultados.

3. Exportación de Datos y Atajo Global:
   - Botón "Exportar" con formatos CSV y JSON mediante el diálogo de guardado nativo de macOS.
   - Atajo de teclado global (por ejemplo, Cmd+Shift+F) que traiga la ventana principal al frente y
     enfoque la barra de búsqueda.

Todos los textos visibles en español (es-MX).
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
