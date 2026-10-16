# Prompts para Glaze — App de escritorio VANTAGE BitTorrent Search

Suite de prompts optimizada para **Glaze por Raycast**, diseñada específicamente para construir la interfaz gráfica (UI Wrapper) sobre un backend de Python ya existente, respetando un **presupuesto ajustado de 50 créditos**.

---

## ⚡ Estrategia de Maximización para Presupuesto de 50 Créditos

Con un saldo de 50 créditos, es fundamental **evitar que Glaze gaste recursos en escribir, refactorizar o reimplementar lógica de backend**. El backend ya está programado en Python y funciona localmente. Glaze debe actuar exclusivamente como un **constructor de UI gráfica nativa en macOS**.

### Reglas de Oro para Ahorrar Créditos:
1. **Uso primordial de Plan Mode (`Shift + Tab`)**: En Plan Mode, Glaze solo razona la arquitectura y el flujo de archivos sin compilar ni modificar código (~15–25 créditos por ciclo). Aprueba el plan en texto antes de permitirle pasar a Build Mode.
2. **Backend como Caja Negra**: Ordena explícitamente a Glaze que no programe scrapers, ni clientes HTTP de torrents, ni parsers de HTML dentro de Swift/macOS. Todo se obtiene ejecutando el binario local `vantage-search "<query>" --json`.
3. **Manejo Estricto de Rutas con Espacios**: Todas las invocaciones al CLI deben ir entre comillas dobles (`"/Users/.../03 Projects/..."`) desde el primer prompt para evitar fallos de shell que consuman créditos en reintentos.
4. **Plan de Contingencia (0 Créditos)**:
   - **Opción A (BYOA)**: Configura tu propia API Key de Anthropic/OpenAI en los ajustes de Glaze para continuar usando la app sin depender del saldo de la plataforma.
   - **Opción B (Cursor / Xcode)**: Glaze guarda el código Swift generado en `~/Glaze/<nombre-app>/`. Puedes abrir esa carpeta en Cursor o Xcode y hacer los retoques finales de forma 100% gratuita y local.

---

## 📋 Guía Rápida de Verificación del Backend (Previo a Glaze)

Ejecuta estas verificaciones en tu terminal antes de iniciar el chat con Glaze para asegurar que el backend responde correctamente:

```bash
cd ~/Documents/03\ Projects/VANTAGE/Bittorrent_Search
./scripts/vantage-search --doctor                       # Verifica Python, Ollama y dependencias
./scripts/vantage-search "Oppenheimer 2023" --json | python3 -m json.tool | head -40
echo "Código de salida: $?"
```

---

## 🚀 Prompts Estructurados y Delimitados

### PROMPT 0 — Validación de Wrapper CLI (Plan Mode)
*Modo en Glaze:* **Plan Mode** (`Shift + Tab`) | *Costo estimado:* ~15–20 créditos  
*Objetivo:* Confirmar que Glaze puede invocar la CLI local y leer la salida JSON de forma asíncrona sin bloquear la ventana, sin escribir lógica propia.

#### 🇬🇧 English (Recomendado para el agente de Glaze)
```markdown
Before building any UI code, I want to confirm a strict architectural constraint: this app is strictly a UI wrapper around an EXISTING local CLI backend. DO NOT write any web scrapers, BitTorrent parsing logic, or search algorithms in Swift/macOS.

Build a minimal test window in macOS that performs only this task:

1. Interface:
   - A single text field for input.
   - A "Run Search" button.
   - A "Comprobar backend" button.
   - A plain text output area.

2. Execution & Data Handling:
   - Clicking "Run Search" executes this exact local binary (quoted to handle spaces):
     "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search" "<input_text>" --json
   - Read stdout as JSON and display process exit code, elapsed time, and the fields `diagnostico.items_unicos` and `diagnostico.consulta_efectiva`.
   - Clicking "Comprobar backend" executes:
     "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search" --doctor

3. Strict Constraints:
   - Do NOT reimplement any Python logic in Swift/macOS. Treat the binary as a black box.
   - Keep the UI fully responsive during execution (up to 45s cold start for local Ollama model).
   - If exit code != 0, render stderr in the text area.
   - All user-facing labels in Spanish (es-MX).

First, explain in Plan Mode how you will execute this local subprocess asynchronously without blocking the main UI thread. Wait for my approval before modifying any files.
```

#### 🇪🇸 Español
```markdown
Antes de construir código de interfaz, quiero confirmar una restricción arquitectónica estricta: esta app es estrictamente un wrapper de interfaz sobre un backend CLI local YA EXISTENTE. NO escribas ningún scraper web, ni lógica de parseo de BitTorrent, ni algoritmos de búsqueda en Swift/macOS.

Construye una ventana de prueba mínima en macOS que haga únicamente esto:

1. Interfaz:
   - Un campo de texto único para entrada.
   - Un botón "Ejecutar búsqueda".
   - Un botón "Comprobar backend".
   - Un área de texto plano para la salida.

2. Ejecución y manejo de datos:
   - Al hacer clic en "Ejecutar búsqueda", ejecuta este binario local exacto (con comillas por los espacios):
     "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search" "<texto_ingresado>" --json
   - Lee stdout como JSON y muestra el código de salida, tiempo transcurrido y los campos `diagnostico.items_unicos` y `diagnostico.consulta_efectiva`.
   - Al hacer clic en "Comprobar backend", ejecuta:
     "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search" --doctor

3. Restricciones estrictas:
   - NO reimplementes lógica de Python en Swift/macOS. Trata el binario como una caja negra.
   - Mantén la interfaz totalmente responsiva (hasta 45s en inicio en frío de Ollama).
   - Si el código de salida != 0, muestra stderr en el área de texto.
   - Todos los textos visibles en español (es-MX).

Primero, explica en Plan Mode cómo ejecutarás este subproceso local de forma asíncrona sin bloquear el hilo principal. Espera mi aprobación antes de modificar archivos.
```

---

### PROMPT 1 — Fase 1: MVP de Interfaz de 3 Paneles (Build Mode)
*Modo en Glaze:* **Build Mode** | *Costo estimado:* ~25–30 créditos  
*Objetivo:* Construir la app principal de 3 paneles (Búsqueda, Resultados y Detalle) consumiendo únicamente el JSON emitido por la CLI.

#### 🇬🇧 English
```markdown
Build the desktop UI wrapper for the BitTorrent search app using the existing backend CLI:
"/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search" "<query>" --json

Structure: Single window divided into 3 distinct sections:

1. Top Search Header:
   - Search bar with placeholder: "Busca la serie Severance, Oppenheimer 2023, anime Frieren..."
   - Submitting executes the search CLI command asynchronously.
   - Compact summary bar showing: `diagnostico.items_unicos`, `diagnostico.descartados_por_relevancia`, and effective query badge if `consulta_efectiva` != `consulta_original`: "Buscando: <consulta_efectiva>".

2. Main Results List (Scrollable Table):
   - Render rows from stdout JSON array `resultados`.
   - Columns: Title, Seeders, Leechers, Size, Source badge.
   - Preserve default seeder sorting; support client-side column re-sorting by size or title.
   - Highlight the first row visually as the recommended pick.

3. Right Detail Panel:
   - Selected item details: Full title, Seeders, Leechers, Size, Source.
   - Full Magnet URI (truncated visually, fully selectable).
   - "Copiar magnet" button (copies full URI with temporary "¡Copiado!" feedback) and "Copiar título" button.

4. Exit Code & Error Handling:
   - Exit 0: Render results list.
   - Exit 2: Empty state. Read `diagnostico.motores` and explain the exact cause (e.g., index down or no matches).
   - Exit 3: Show error state "El servicio de IA local no responde. Ejecuta 'ollama serve'". Include a "Reintentar" button.
   - Exit 4: Show "Error de conexión o bloqueo de índices".
   - Exit 65: Show "Backend no encontrado en la ruta especificada".
   - Any other code: Collapsible disclosure showing raw stderr.

Strict Boundaries:
- NEVER parse plain text stdout; parse stdout strictly as JSON using `--json`.
- Do NOT re-filter, re-deduplicate, or alter search results: the CLI backend already handles deduplication and relevance filtering.
- Do NOT add local databases, torrent downloads, or external network calls.
- All user-facing UI labels in Spanish (es-MX).
```

#### 🇪🇸 Español
```markdown
Construye la interfaz de escritorio para la app de búsqueda BitTorrent utilizando el backend CLI existente:
"/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search" "<consulta>" --json

Estructura: Una sola ventana dividida en 3 áreas distintas:

1. Encabezado de Búsqueda (Arriba):
   - Barra de búsqueda con placeholder: "Busca la serie Severance, Oppenheimer 2023, anime Frieren..."
   - Al presionar Enter ejecuta el comando CLI de forma asíncrona.
   - Barra de resumen compacta mostrando: `diagnostico.items_unicos`, `diagnostico.descartados_por_relevancia` y badge de consulta efectiva si difiere de la original.

2. Lista Principal de Resultados (Tabla desplazable):
   - Renderiza las filas del array JSON `resultados` de stdout.
   - Columnas: Título, Semillas (Seeders), Descargadores (Leechers), Tamaño, Origen (Source badge).
   - Mantiene el orden por semillas por defecto; permite reordenar por tamaño o título.
   - Destaca la primera fila visualmente como la recomendada.

3. Panel de Detalle Derecho:
   - Detalles del elemento seleccionado: Título completo, Semillas, Descargadores, Tamaño, Origen.
   - Magnet URI completo (truncado visualmente, completamente seleccionable).
   - Botón "Copiar magnet" (copia URI completo con mensaje "¡Copiado!") y botón "Copiar título".

4. Manejo de Errores por Código de Salida:
   - Código 0: Renderiza la lista de resultados.
   - Código 2: Estado vacío. Lee `diagnostico.motores` y explica la causa exacta.
   - Código 3: Muestra "El servicio de IA local no responde. Ejecuta 'ollama serve'". Incluye botón "Reintentar".
   - Código 4: Muestra "Error de conexión o bloqueo de índices".
   - Código 65: Muestra "Backend no encontrado en la ruta especificada".
   - Otro código: Desplegable con stderr bruto.

Límites Estrictos:
- NUNCA parsees texto plano; lee stdout exclusivamente como JSON usando `--json`.
- NO vuelvas a filtrar ni deduplicar resultados: el backend en Python ya lo realiza.
- NO agregues bases de datos locales, descargas de torrents ni peticiones de red externas.
- Todos los textos visibles en español (es-MX).
```

---

### PROMPT 2 — Fase 2: Diagnóstico de Motores y Ajustes Avanzados
*Modo en Glaze:* **Build Mode** | *Costo estimado:* ~15–20 créditos (ejecutar solo si resta saldo suficiente)

```markdown
Add two optional UI extensions while keeping all backend logic intact:

1. Collapsible Diagnostics Panel (Bottom Section):
   - Summary line: Raw results count, unique items, discarded by relevance, IMDb ID.
   - Table of engines from `diagnostico.motores`: Name, Status (OK / FALLO / OMITIDO), item count, execution latency (ms), and error text if present.

2. Advanced Settings Window (Modal / Separate View):
   - Minimum seeders input (default: 5) -> appends `-s <n>`
   - Toggle "No descartar resultados por relevancia" (default: off) -> appends `--sin-relevancia`
   - Toggle "No consultar IMDb" (default: off) -> appends `--no-imdb`
   - Toggle "Buscar índices secuencialmente" (default: off) -> appends `--secuencial`
   - Ollama model string (default: "qwen2.5:7b") -> appends `-m <modelo>`
   - Ollama host URL (default: "http://localhost:11434") -> appends `--host <url>`
   - "Restaurar valores por defecto" button.

All UI text in Spanish (es-MX).
```

---

### PROMPT 3 — Fase 3: Historial y Exportación
*Modo en Glaze:* **Build Mode** | *Costo estimado:* ~10–15 créditos

```markdown
Implement two comfort features for the frontend:

1. Local Search History:
   - Persist the last 50 searches locally on disk.
   - Store: query string, effective query, timestamp, and result count.
   - Provide a Sidebar or "Historial" view allowing 1-click re-opening of past search results.

2. Data Export:
   - "Exportar" button supporting CSV and JSON formats via native macOS Save Dialog.

All UI copy in Spanish (es-MX).
```

---

## 🛠️ Plantilla para Correcciones de UI (Sin Desperdicio de Créditos)

Si la interfaz requiere un ajuste visual, usa esta plantilla de 1 solo intento para no malgastar créditos en ida y vuelta:

```markdown
Lo que veo: <comportamiento actual de la UI>
Lo que quiero: <comportamiento esperado concreto>
Datos concretos: <código de salida, campo JSON, o captura/annotated image>
No cambies: <componentes de UI que ya funcionan bien>
```

*Ejemplo:*
```markdown
Lo que veo: Al hacer clic en "Copiar magnet", la app copia solo los primeros 30 caracteres truncados.
Lo que quiero: Que copie la cadena completa del URI Magnet almacenada en el objeto JSON.
Datos concretos: Campo `resultados[i].magnet`.
No cambies: El botón "Copiar título" ni el diseño del panel derecho.
```
