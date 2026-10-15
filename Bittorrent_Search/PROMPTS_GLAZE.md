# Prompts para Glaze — App de escritorio de VANTAGE BitTorrent Search

Prompts listos para pegar en **Agent Chat** de Glaze, en el orden recomendado.
El brief completo (contrato de datos, pantallas y criterios de aceptación) está en `BRIEF_UI_GLAZE.md`.

> **Por qué hay versión en inglés y en español**: el agente de Glaze está documentado en
> inglés y suele acertar más con prompts en inglés, pero entiende español. Los prompts
> largos van en los dos idiomas; elige uno y pégalo tal cual. En todos se pide
> explícitamente que **los textos de la interfaz sean en español**.

---

## Antes de empezar

**1. Comprueba el backend a mano** (así sabes qué debe reproducir la app):

```bash
cd ~/Documents/03\ Projects/VANTAGE/Bittorrent_Search
./scripts/vantage-search --doctor                       # ¿está todo en su sitio?
./scripts/vantage-search "Oppenheimer 2023" --json | python3 -m json.tool | head -40
echo "código de salida: $?"
```

**2. Verifica que Ollama está corriendo** (si no, la app devolverá el código 3):

```bash
ollama list && curl -s http://localhost:11434/api/tags >/dev/null && echo "Ollama OK"
```

**3. Da contexto al agente.** Si el repo está en GitHub, conecta la integración de GitHub
y dile al agente que lea `Bittorrent_Search/README.md`. Si no, adjunta `BRIEF_UI_GLAZE.md`.

**4. Ten paciencia con los tiempos.** La **primera** búsqueda tras arrancar Ollama puede
llegar a **~45 s** (el modelo de 4,7 GB se carga en memoria); a partir de ahí, **~14 s**
mientras el backend siga intentando un índice caído, y **~2,5 s** en cuanto ese índice queda
apartado (ocurre solo, tras dos fallos: ver el punto 5). No es que la app se haya colgado.

**5. Los índices caídos se gestionan solos.** El backend guarda un historial persistente:
tras **dos fallos consecutivos** deja de consultar ese índice durante 30 minutos (el
diagnóstico lo reporta con `saltado_por_salud: true`) y luego lo reintenta con un timeout
corto, así que se recupera sin intervención. **La app no tiene que recordar nada**: no hace
falta desmarcar índices ni pasar `--sin-motores`. Eso es solo preferencia del usuario.

**6. Empieza en Plan mode** para la Fase 0 y la Fase 1 (hay un proceso externo de por medio),
y sigue en Build mode para los ajustes.

---

## PROMPT 0 — Verificar que la app puede ejecutar el comando (Plan mode)

> Es el único riesgo técnico real. Si esto funciona, el resto es interfaz.

### English

```
Before building any UI, I want to verify one thing: this app must run a local
command-line tool and read its JSON output.

Build a minimal Mac app with a single window that does only this:

- A text field for a search phrase, a "Run" button, and a text area for results.
- When I click Run, it executes this command (the path contains a space, so it must be
  quoted correctly):

  "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search"
  "<the text I typed>" --json

- It shows: the process exit code, the elapsed time, and the values of the JSON fields
  "diagnostico.items_unicos" and "diagnostico.consulta_efectiva" from stdout.
- Add a second button, "Comprobar backend", that runs the same tool with "--doctor" and
  prints the JSON it returns (it reports whether Python, the dependencies, Ollama and the
  model are ready).
- If the exit code is not 0, it shows what came out on stderr.
- The UI must stay responsive while the command runs. It can take up to **45 seconds the
  first time** (a local model loads into memory) and around 15 seconds afterwards, so show
  a spinner with the elapsed time and never look frozen.
- All user-facing labels in Spanish (es-MX).

Do not build anything else yet: no result list, no formatting. I only want to confirm
the app can run the tool and read the JSON. Tell me if running a local executable like
this is not possible in this environment, and what the alternative would be.
```

### Español

```
Antes de construir ninguna interfaz, quiero verificar una cosa: esta app tiene que
ejecutar una herramienta de línea de comandos local y leer su salida JSON.

Construye una app de Mac mínima, con una sola ventana, que haga únicamente esto:

- Un campo de texto para una frase de búsqueda, un botón "Ejecutar" y un área de texto
  para el resultado.
- Al pulsar Ejecutar, ejecuta este comando (la ruta contiene un espacio, así que hay que
  citarla bien):

  "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search"
  "<el texto que escribí>" --json

- Muestra: el código de salida del proceso, el tiempo transcurrido y los valores de los
  campos JSON "diagnostico.items_unicos" y "diagnostico.consulta_efectiva" de stdout.
- Añade un segundo botón, "Comprobar backend", que ejecute la misma herramienta con
  "--doctor" y muestre el JSON que devuelve (informa si Python, las dependencias, Ollama
  y el modelo están listos).
- Si el código de salida no es 0, muestra lo que salió por stderr.
- La interfaz debe seguir respondiendo mientras corre el comando. Puede tardar hasta **45
  segundos la primera vez** (un modelo local se carga en memoria) y unos 15 segundos
  después, así que muestra un indicador con el tiempo transcurrido y nunca debe parecer
  congelada.
- Todos los textos visibles en español (es-MX).

No construyas nada más todavía: ni lista de resultados ni formateo. Solo quiero confirmar
que la app puede ejecutar la herramienta y leer el JSON. Si en este entorno no es posible
ejecutar un binario local así, dímelo y qué alternativa habría.
```

---

## PROMPT 1 — Fase 1: MVP (Plan mode)

### English

```
Now build the real app: a Mac desktop app that searches BitTorrent metadata and shows the
results. Same command as before (the backend already exists; do not reimplement the search):

  "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search"
  "<query>" --json

Single window, three parts:

1. Search bar at the top, focused when the app opens, runs on Enter. Placeholder text:
   "Busca la serie Severance, Oppenheimer 2023, anime Frieren..."
2. Results list (main area). One row per item from the JSON array "resultados", showing:
   title, seeders, leechers, size, and the "source" as a colored badge. The list arrives
   already sorted by seeders descending: keep that order and let me re-sort by size or name.
   It can contain 100+ rows, so it must scroll smoothly. The first row should look like the
   recommended pick.
3. Detail panel on the right for the selected row: full title, seeders, leechers, size,
   source, the full magnet selectable (show it truncated but copy the whole value), a
   "Copiar magnet" button with a brief "Copiado" confirmation, and a "Copiar título" button.

Error and empty states (the process exit code tells us which one):

- exit 0: results were found, show them.
- exit 2: no results. Do not just say "no results": read "diagnostico.motores" and explain
  the real cause. If every engine has "ok": true and 0 results, suggest fewer words or the
  English title. If an engine has "ok": false, name it and show its "error" text.
- exit 3: the local AI service is not responding. Show a clear notice with the exact
  command "ollama serve", plus a "Reintentar" button.
- exit 4: every index failed. Show a network/blocking notice.
- any other code: short message plus the stderr text behind a "Detalles" disclosure.

Show a compact summary line under the search bar: unique results, how many were dropped by
relevance filtering ("diagnostico.descartados_por_relevancia"), and the IMDb id if present.
If "diagnostico.consulta_efectiva" differs from "diagnostico.consulta_original", show the
effective query as "Buscando: <efectiva>".

In the diagnostics panel, an index with "saltado_por_salud": true must appear as "saltado"
together with its "motivo_salud", and must not be counted as a failure of this search: the
backend set it aside after two failures and will retry it on its own.

While the command runs: indeterminate spinner, elapsed time, and a Cancel button. Never show
"no results" before the process finishes. Keep the previous list visible but dimmed. Expect up
to 45 seconds on the first search after the local model loads into memory, around 15 seconds
while a dead index is still being attempted, and around 2-3 seconds once the backend has set
that index aside: present all of that as normal, not as an error.

Requirements:
- Always use "--json" and parse stdout as JSON. Never parse the text output, and never treat
  stderr as data.
- Do not re-filter or re-sort the results in the app: the backend already deduplicates,
  filters by relevance and sorts by seeders.
- The app must never freeze while the process runs.
- Search history: not yet.
- All user-facing copy in Spanish (es-MX).
```

### Español

```
Ahora construye la app real: una app de escritorio para Mac que busque metadatos de
BitTorrent y muestre los resultados. El mismo comando de antes (el backend ya existe; no
reimplementes la búsqueda):

  "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search"
  "<consulta>" --json

Una sola ventana, con tres partes:

1. Barra de búsqueda arriba, con el foco al abrir la app, que busca al pulsar Enter. Texto
   de ayuda: "Busca la serie Severance, Oppenheimer 2023, anime Frieren..."
2. Lista de resultados (área principal). Una fila por elemento del array JSON "resultados",
   con: título, semillas, descargadores, tamaño y el "source" como etiqueta de color. La
   lista ya llega ordenada por semillas de mayor a menor: conserva ese orden y déjame
   reordenar por tamaño o por nombre. Puede tener más de 100 filas: debe desplazarse con
   fluidez. La primera fila debe verse como la opción recomendada.
3. Panel de detalle a la derecha para la fila seleccionada: título completo, semillas,
   descargadores, tamaño, origen, el magnet completo seleccionable (muéstralo truncado pero
   copia el valor íntegro), un botón "Copiar magnet" con una confirmación breve ("Copiado")
   y un botón "Copiar título".

Estados de error y vacío (el código de salida del proceso dice cuál es):

- código 0: hay resultados, muéstralos.
- código 2: sin resultados. No te limites a decir "sin resultados": lee
  "diagnostico.motores" y explica la causa real. Si todos los motores tienen "ok": true y 0
  resultados, sugiere menos palabras o el título en inglés. Si algún motor tiene "ok": false,
  nómbralo y muestra su texto "error".
- código 3: el servicio de IA local no responde. Muestra un aviso claro con el comando
  exacto "ollama serve" y un botón "Reintentar".
- código 4: fallaron todos los índices. Muestra un aviso de red o bloqueo.
- cualquier otro código: mensaje breve y el texto de stderr dentro de un desplegable
  "Detalles".

Muestra una línea de resumen compacta bajo la barra de búsqueda: resultados únicos, cuántos
se descartaron por relevancia ("diagnostico.descartados_por_relevancia") y el IMDb id si
existe. Si "diagnostico.consulta_efectiva" es distinta de "diagnostico.consulta_original",
muestra la consulta efectiva como "Buscando: <efectiva>".

En el panel de diagnóstico, un índice con "saltado_por_salud": true debe mostrarse como
"saltado" con su "motivo_salud", no como un fallo de esta búsqueda.

Mientras corre el comando: indicador indeterminado, tiempo transcurrido y botón Cancelar.
No muestres nunca "sin resultados" antes de que termine el proceso. Mantén la lista anterior
visible pero atenuada. Cuenta con hasta 45 segundos en la primera búsqueda tras cargar el
modelo local en memoria, unos 15 segundos mientras aún se intenta un índice caído, y unos
2-3 segundos cuando el backend ya lo ha apartado: preséntalo todo como normal, no como error.

Requisitos:
- Usa siempre "--json" y parsea stdout como JSON. No parsees la salida de texto y no trates
  stderr como datos.
- No vuelvas a filtrar ni reordenar los resultados en la app: el backend ya deduplica, filtra
  por relevancia y ordena por semillas.
- La app no debe congelarse mientras corre el proceso.
- Historial de búsquedas: todavía no.
- Todos los textos visibles en español (es-MX).
```

---

## PROMPT 2 — Fase 2: diagnóstico visible, calidad y ajustes

### English

```
Three additions to the search app. Keep everything else as it is.

1. Diagnostics panel, collapsed by default, below the results list. One row per engine from
   "diagnostico.motores": name, state (OK / FALLO if "ok" is false / OMITIDO if "omitido" is
   true), the number of results, the milliseconds, and the "error" text when there is one.
   Above the rows, a summary: raw results, unique results, dropped by relevance, IMDb id.
   This panel is what explains an empty search, so it must be visible even when there are
   zero results.

2. Release quality tagging in the list and the detail panel. When the title contains CAM,
   TS, HDCAM or HDTS, show a warning badge that says "calidad de cámara" with a tooltip
   explaining that it was recorded in a cinema or from a screener. When it contains BluRay,
   WEB-DL or WEBRip, show a subtle "buena calidad" badge. Important: do NOT change the
   sorting — seeders order is the agreed criterion of the backend. Just make the quality
   visible.

3. Advanced settings panel (separate from the main screen), with these options and their
   current defaults shown, plus a "Restaurar valores" button:
   - Minimum seeders, default 5 → passes "-s <n>"
   - "No descartar resultados que no coincidan con mi búsqueda" (off by default) → "--sin-relevancia"
   - "No consultar IMDb" (off) → "--no-imdb"
   - "Buscar en los índices uno a uno" (off) → "--secuencial"
   - Ollama model, default "qwen2.5:7b" → "-m <modelo>"
   - Ollama server, default "http://localhost:11434" → "--host <url>"
   - Which indexes to consult (checkboxes: YTS, LimeTorrents, MagnetDL, EZTV, Nyaa) →
     "--sin-motores <unchecked>". This is a user preference only: the backend already stops
     waiting for an index that failed twice (it reports "saltado_por_salud" and retries it
     later on its own). Leave every box checked and let the backend handle it.
   - Health history: a small control with "auto" (default), "off" and "reset" → "--salud".
   Also show in this panel: the backend folder path (not editable for now) and an Ollama
   status light with a "Comprobar conexión" button that checks http://localhost:11434 and
   turns green or red.

All labels in Spanish (es-MX).
```

---

## PROMPT 3 — Fase 3: comodidad (historial, menú bar, exportar)

### English

```
Three comfort features, one at a time if that is easier:

1. Search history: keep the last 50 searches on disk (local only). Each entry stores the
   text I typed, the effective query, the date, and the results, so I can reopen a past
   search without running the command again. Add a sidebar or a "Historial" section with a
   click to repeat, and a way to delete one entry or clear everything.

2. Menu bar: a menu bar item with a compact search field. Typing a query and pressing Enter
   runs the search and opens the main window with the results.

3. Export: a button to export the current results to CSV and to JSON, saved wherever I
   choose with a save dialog.

Also: a global keyboard shortcut to open the app and focus the search field.
All labels in Spanish (es-MX).
```

---

## Plantilla para corregir desajustes

Cuando el resultado no sea lo que querías, describe **el comportamiento esperado**, no el
error. (Y si el problema es visual, usa el botón **Annotate** y señala el elemento exacto.)

```
Lo que veo: <comportamiento actual, concreto>
Lo que quiero: <comportamiento esperado, concreto>
Datos concretos: <código de salida, campo del JSON, ejemplo de búsqueda>
No cambies: <lo que ya funciona y no debe romperse>
```

Ejemplo:

```
Lo que veo: al buscar "Severance" la lista sale vacía, pero el comando en la terminal
devuelve 98 resultados con código 0.
Lo que quiero: que la lista muestre esos 98 resultados.
Datos concretos: exit code 0, diagnostico.items_unicos = 98, resultados.length = 98.
No cambies: la barra de búsqueda ni el panel de detalle.
```

> Si después de 3 o 4 correcciones la app se aleja de lo que quieres, no sigas parcheando:
> vuelve a una versión anterior en **Version History** y repite ese paso con un prompt más
> claro.

---

## Notas de uso de Glaze

- **Plan mode** para la Fase 0 y la Fase 1; Build mode para ajustes pequeños.
- Los **créditos** se gastan por trabajo: la Fase 0 es barata a propósito (es un experimento).
- Si conectas la **integración de GitHub**, el agente puede leer el `README.md` y el
  `MANUAL_USUARIO.md` del backend: úsalos como fuente de los textos en español.
- Añade un **icono** cuando la app funcione (generarlo no gasta créditos).
