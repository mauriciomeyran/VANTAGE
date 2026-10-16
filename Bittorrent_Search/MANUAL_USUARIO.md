# Manual de uso de BitPuller

> Esta es la guía para usar la **app de escritorio**. Si prefieres la terminal, salta al
> final: [«Uso por terminal (avanzado)»](#uso-por-terminal-avanzado).

---

## ¿Qué es BitPuller?

BitPuller es la app de escritorio para macOS que pone **interfaz gráfica** al buscador de
metadatos BitTorrent de VANTAGE. Escribes lo que quieres en lenguaje natural y la app consulta
varios índices públicos a la vez, te muestra los resultados ordenados por semillas y te deja
copiar el magnet del que más conviene.

**Ejemplo:** escribes «Busca la serie Severance» y obtienes la lista de resultados, con el mejor
destacado arriba y su magnet a un clic.

La app **no busca por sí misma**: llama al backend que ya vive en la carpeta del proyecto, que es
quien consulta los índices y usa un modelo de IA local (Ollama) para entender tu frase. Ese
backend se puede seguir usando por terminal, y está documentado al final en
[«Uso por terminal»](#uso-por-terminal-avanzado).

**Lo que la app no hace**, por diseño: no descarga torrents, no abre ningún cliente de torrents,
no guarda nada fuera de tu equipo y no envía datos a ningún servicio. Solo busca metadatos y
copia magnets.

---

## Requisitos

Antes de empezar, necesitas tener instalado:

1. **Python 3.11 o superior** (probablemente ya lo tengas)
2. **Ollama** - Un programa para ejecutar inteligencia artificial en tu computadora

### ¿Cómo saber si tienes Python?

Abre la terminal y escribe:
```bash
python3 --version
```

Si ves un número como `3.11.0` o superior, estás listo.

### ¿Cómo instalar Ollama?

1. Ve a [ollama.com](https://ollama.com)
2. Descarga e instala la versión para tu sistema (Mac, Windows o Linux)
3. Una vez instalado, abre la terminal y verifica:
```bash
ollama --version
```

### Descargar el modelo de IA

VANTAGE necesita un modelo de inteligencia artificial para entender lo que escribes. Para este proyecto usamos `qwen2.5:7b`:

```bash
ollama pull qwen2.5:7b
```

Esto descargará aproximadamente 4.7 GB. Espera a que termine.

---

---

## Instalación

### Paso 1: Ir a la carpeta del proyecto

Abre la terminal y navega a la carpeta donde están los archivos de VANTAGE:

```bash
cd ~/Documents/03\ Projects/VANTAGE/Bittorrent_Search
```

### Paso 2: Crear un entorno virtual

Esto crea un espacio aislado para instalar las dependencias del proyecto sin afectar otros programas:

```bash
python3 -m venv venv
```

> Si ya tenías un entorno `venv` de antes, puedes reutilizarlo. Ojo: en macOS el
> Python de Homebrew no permite instalar paquetes globalmente, por eso todo va
> dentro de `venv`.

### Paso 3: Activar el entorno virtual

**En Mac/Linux:**
```bash
source venv/bin/activate
```

**En Windows:**
```bash
venv\Scripts\activate
```

Cuando lo actives, verás que aparece `(venv)` al inicio de tu línea de comandos.

### Paso 4: Instalar las dependencias

```bash
pip install -r requirements.txt
```

Esto instalará todo lo necesario: ollama (cliente Python), requests (para hacer peticiones web) y beautifulsoup4 (para leer páginas web).

Si además quieres ejecutar las pruebas automatizadas:

```bash
pip install -r requirements-dev.txt
```

---

### Paso 5: Abrir BitPuller

Con el backend instalado, abre **BitPuller** desde el Finder o desde Launchpad. La app usa la
carpeta del backend que acabas de preparar; no trae su propio Python.

### Paso 6: Comprobar que todo está listo

En la app, pulsa **Comprobar backend**. Debe salir todo en verde: intérprete, `main.py`,
dependencias, Ollama y el modelo. Si algo falla, ahí mismo verás cuál es el problema.

---

## La interfaz

La ventana principal tiene tres zonas: el **buscador** arriba, la **lista de resultados** en el
centro y el **panel de detalle** a la derecha. El panel de **diagnóstico** se despliega debajo de
la lista.

### Buscador y barra de resumen

- Campo de búsqueda con el texto de ayuda *"Busca la serie Severance, Oppenheimer 2023, anime
  Frieren…"*. Se puede lanzar con **Enter** o con el botón **Buscar**.
- Mientras busca verás un **cronómetro** y el botón **Cancelar** (ver más abajo).
- Debajo aparece la barra de resumen con: cuántos resultados hay, cuántos se **descartaron por
  relevancia**, el identificador de IMDb si se usó, la consulta efectiva (*"Buscando: …"*) cuando
  difiere de lo que escribiste, y los índices realmente consultados
  (*"Consultados: LimeTorrents, EZTV, Nyaa"*).

### Lista de resultados

- Columnas: **Título**, **Semillas**, **Descargadores**, **Tamaño** y **Origen**.
- El orden de llegada es por semillas, de mayor a menor. Puedes reordenar haciendo clic en los
  encabezados, pero el orden por semillas es el recomendado: más semillas es más estable.
- La primera fila queda destacada como la opción recomendada.
- La lista se despliega por tramos, así que se mantiene fluida con cientos de resultados.
- Junto al título pueden aparecer dos insignias:
  - **calidad de cámara** — el título contiene CAM, TS, HDCAM o HDTS: es una grabación de cine o
    de pantalla, con calidad muy inferior.
  - **buena calidad** — el título contiene BluRay, WEB-DL o WEBRip.
  Las insignias solo informan: **no cambian el orden**.

### Panel de detalle

Al seleccionar un resultado:

- Título completo, semillas, descargadores, tamaño y origen.
- El **magnet completo**, en un recuadro desplazable. Se muestra acortado para que quepa, pero el
  valor que se copia es el íntegro.
- **Copiar magnet** y **Copiar título**, con la confirmación «¡Copiado!».

### Panel de diagnóstico

Un panel plegable con una fila por índice. Muestra **Resultados**, **Latencia (ms)** y el error
literal cuando algo falla. Los estados posibles son:

| Estado | Qué significa |
| --- | --- |
| **OK** | El índice respondió. |
| **Fallo** | El índice no respondió; debajo aparece el motivo. |
| **Omitido** | No aplica a esa categoría (por ejemplo, EZTV en una búsqueda de películas). |
| **Saltado** | El backend lo apartó tras dos fallos seguidos y ya no lo espera. Se reintenta solo pasado un rato; si vuelve a responder, se recupera sin que hagas nada. |
| **sondeo (timeout Ns)** | Es el reintento de un índice saltado, con un tiempo de espera reducido. |

### Ajustes avanzados

Se abren desde el botón de **Configuración** en la barra superior y se aplican a la **siguiente
búsqueda**:

| Ajuste | Para qué sirve |
| --- | --- |
| **Seeders mínimos** | Descarta resultados por debajo de ese número de semillas (por defecto 5). |
| **No descartar por relevancia** | Conserva todo lo que devuelvan los índices, aunque no coincida con tu frase. |
| **No consultar IMDb** | Evita la consulta a IMDb; puede dejar a EZTV sin resultados. |
| **Buscar índices secuencialmente** | Uno por uno en lugar de en paralelo: más lento, más conservador. |
| **Modelo de Ollama** | Qué modelo local usar para entender tu frase (por defecto `qwen2.5:7b`). |
| **Host de Ollama** | Dónde escucha Ollama (por defecto `http://localhost:11434`). |
| **Índices** | Casillas para elegir en cuáles buscar. Desmarcar los que estén caídos acorta mucho la búsqueda. |
| **Historial de salud** | `auto` (recomendado), `off` para ignorar el historial en una búsqueda, o `reset` para borrarlo. |

Incluye **Restaurar valores por defecto**, la ruta del backend (de solo lectura) y el estado de
Ollama.

### Ayuda

El botón **Ayuda** abre una ventana con este mismo manual, resumido: qué es, cómo buscar, cómo
leer los resultados, qué hacer cuando algo falla y consejos. El botón **Ver el manual completo**
abre este archivo en el visor del sistema.

### Historial

Una barra lateral con las **últimas 50 búsquedas**. Al hacer clic en una se recuperan sus
resultados **sin volver a consultar los índices**, así que es instantáneo. Cada entrada se puede
borrar por separado, y hay un botón para vaciar todo el historial.

### Menú bar y atajo global

- Un icono en la **barra de menú**: al pulsarlo se abre un campo de búsqueda rápida. Escribes,
  pulsas Enter y la ventana principal se abre con los resultados. Con el botón derecho hay además
  *Buscar…*, *Mostrar ventana* y *Salir*.
- El atajo **⌘⇧F** trae la ventana al frente y deja el cursor en el buscador.

### Exportar

El botón **Exportar** guarda los resultados de la búsqueda actual con el diálogo nativo de macOS,
en **CSV** (columnas: Título, Seeders, Leechers, Tamaño, Fuente, Magnet) o en **JSON**, que
incluye además el diagnóstico completo.

### Cancelar una búsqueda

Junto al cronómetro hay un botón **Cancelar** disponible durante toda la búsqueda, incluido el
primer arranque en frío del modelo, que puede tardar bastante. Cancelar detiene el proceso de
verdad y devuelve la ventana al estado anterior, sin mensaje de error.

---

## Cómo interpreta tu búsqueda

Puedes escribir con toda naturalidad: VANTAGE separa lo que quieres buscar de las
palabras que solo indican de qué tipo es el contenido.

- `"Busca la película Oppenheimer"` → busca **Oppenheimer**
- `"Quiero descargar Dune 2021"` → busca **Dune 2021**
- `"The Game"` → busca **The Game**: si quitar una palabra dejaría la búsqueda
  vacía, no se toca nada

Cuando el sistema tiene que limpiar tu frase, el diagnóstico lo deja claro:

```
consulta='Oppenheimer' categoria=movies min_seeders=5 (peticion original='película Oppenheimer')
```

La categoría también se detecta sola: si dices "serie" se consulta EZTV, si dices
"película" se consulta YTS, y si pides música o juegos no se pierde tiempo en
índices que no tienen ese contenido.

**En el código:** el saneado lo hace `texto.limpiar_consulta()` con las listas
`PALABRAS_INTENCION` y `ARTICULOS_INICIALES`, y se aplica al principio de
`AgregadorTorrents.buscar_con_diagnostico()`. La categoría la normaliza
`normalizar_categoria()` con la tabla `ALIAS_CATEGORIAS` (categorías canónicas:
`movies`, `tv`, `anime`, `music`, `games`, `applications`, `books`, `all`).

---

---

## Filtro de relevancia

VANTAGE compara las palabras de tu búsqueda con el título de cada resultado y
descarta los que no coinciden. Por ejemplo, buscando `"Dune"` ya no aparece
*"Genshin Impact - The Unfathomable Sand Dunes"*, que es una banda sonora y no la
película.

Si alguna vez quieres ver **todo** lo que devuelven los índices, sin ese filtro:

```bash
python3 main.py "Dune" --sin-relevancia
```

**En el código:** la comparación está en `coincide_titulo()` (compara por palabra,
no por subcadena) y la aplica `buscar_con_diagnostico()` cuando
`exigir_coincidencia=True`, que es el valor por defecto. Las palabras que se
ignoran al comparar están en `PALABRAS_VACIAS`.

---

---

## Estados y errores de la app

| Lo que ves | Qué significa | Qué hacer |
| --- | --- | --- |
| **Buscando…** con cronómetro | La consulta está en marcha. | Esperar, o pulsar **Cancelar**. |
| **Lista de resultados** | Todo correcto. | Usar **Copiar magnet** en el que elijas. |
| **Sin resultados** | Tres causas posibles, y la app te dice cuál: (1) el historial de salud había apartado los índices, y ofrece restablecerlo; (2) los índices respondieron pero nada coincidía; (3) algún índice falló. | Sigue la indicación que aparezca. Si es la (1), pulsa **Restablecer historial de salud**. |
| **El servicio de IA local no responde** | Ollama está apagado. | Abre Ollama y pulsa **Reintentar**. |
| **Error de conexión o bloqueo de índices** | Ningún índice respondió. | Revisa tu conexión y reintenta más tarde. |
| **Backend no encontrado en la ruta especificada** | La app no encuentra el backend (o su entorno de Python). | Comprueba la instalación (ver «Instalación») y usa **Comprobar backend**. |
| **La búsqueda excedió el tiempo límite** | Pasaron más de dos minutos sin respuesta. | Reintenta; si se repite, revisa Ollama con **Comprobar backend**. |
| **Cancelada** | La detuviste tú. | Nada: vuelve a buscar cuando quieras. |

Los detalles técnicos de cada fallo quedan en un desplegable **Detalles**, y el botón
**Comprobar backend** comprueba de una vez el intérprete, las dependencias, Ollama, el modelo
descargado y el historial de salud de los índices.

---

## Estado de los índices

VANTAGE puede fallar en un índice sin que la búsqueda completa se rompa. Estado
verificado el **2026-10-14**:

| Índice | Estado | Notas |
| --- | --- | --- |
| YTS | Funciona | Solo películas. Se usa el dominio `yts.gg` porque `yts.mx` no resuelve |
| LimeTorrents | Funciona | Generalista. Es el que suele dar los resultados con más semillas |
| Nyaa | Funciona | Solo anime y contenido asiático: para películas occidentales devuelve vacío |
| EZTV | Funciona | Solo series, y necesita identificar la serie en IMDb (lo hace solo) |
| MagnetDL | **Caído** | No responde (timeout en `.com`, DNS en `.mx`). El motor sigue activo: si vuelve, funcionará sin cambios |

**En el código:** cada fila es una función de `engines.py` (`buscar_torrents_yts`,
`buscar_torrents_limetorrents`, `buscar_torrents_nyaa`, `buscar_torrents_eztv`,
`buscar_torrents_magnetdl`) con su lista de mirrors `BASE_URLS_*`. La descripción y
las notas de cada motor se declaran en `MOTORES_POR_DEFECTO`.

**Automático:** si un índice falla dos veces seguidas, VANTAGE deja de esperarlo
durante 30 minutos y aparece como `[SALTADO]` en el diagnóstico. Pasado ese tiempo lo
reintenta con un timeout corto, así que si el índice vuelve, se recupera solo. La
primera búsqueda tras dos fallos pasa de ~14 s a ~2 s.

Si quieres forzarlo a mano, o comparar con y sin historial:

```bash
python3 main.py "Severance" --salud off      # ignora el historial
python3 main.py "Severance" --salud reset    # borra el historial
python3 main.py "Severance" --sin-motores MagnetDL
```

---

---

## Cómo leer los resultados

VANTAGE te mostrará algo como:

```
Resultado óptimo:
  Title:    Oppenheimer (2023) [1080p] [BluRay] [5 1]
  Magnet:   magnet:?xt=urn:btih:...&dn=Oppenheimer...&tr=udp%3A%2F%2F...
  Seeders:  571
  Leechers: 77
  Size:     3.33 GB
  Source:   LimeTorrents
```

- **Title:** El nombre del torrent (incluye calidad y fuente)
- **Magnet:** El enlace magnético que puedes copiar y pegar en tu cliente de torrents (Transmission, qBittorrent, etc.)
- **Seeders:** Cantidad de personas compartiendo el archivo (más es mejor)
- **Leechers:** Cantidad de personas descargando el archivo
- **Size:** Tamaño del archivo
- **Source:** Índice de origen (YTS, LimeTorrents, Nyaa, EZTV o MagnetDL)

---

---

## Consejos de Uso

1. **Sé específico:** "Película Oppenheimer 2023" funciona mejor que solo "Oppenheimer"
2. **Idioma:** Puedes escribir en español o inglés, el sistema entiende ambos
3. **Categorías:** El sistema detecta la categoría solo; si la mencionas ("película", "serie", "música", "juego", "aplicación", "libro") se respeta esa intención
4. **Seeders:** VANTAGE prioriza los torrents con más semillas para asegurar descargas más rápidas y estables
5. **Anime:** para anime, Nyaa suele dar mejores resultados que los índices generalistas

---

---

## Solución de Problemas

### Error: "Error de conexión con Ollama"

**Causa:** Ollama no está corriendo.

**Solución:** Inicia Ollama:
```bash
ollama serve
```

### Mensaje: "No results found matching criteria"

**Causa:** Ningún índice devolvió torrents que cumplan el mínimo de semillas, o
ninguno coincidió con tu búsqueda.

**Solución:** Desde esta versión, VANTAGE imprime justo debajo el diagnóstico con el
motivo real. Ejemplo:

```
No results found matching criteria.
consulta='Zxqwvbn 1999 pelicula inexistente' categoria=movies min_seeders=5
items: 0 brutos, 0 únicos, 0 descartados por relevancia
[OK]      YTS            0 resultado(s) (1203 ms)
[FALLO]   MagnetDL       ErrorFuenteNoDisponible: ningún mirror respondió: ...
```

Lee esa lista: si todos dicen `[OK]` con 0 resultados, la búsqueda era demasiado
rara (prueba con menos palabras o el nombre en inglés). Si alguno dice `[FALLO]`,
ese índice está caído o bloqueado ese día; los demás siguen funcionando. Baja el
mínimo con `-s 1` si crees que el problema son las semillas.

Si en tu frase aparecían palabras como «película» o «serie», verás además
`(peticion original=...)`: significa que VANTAGE limpió esas palabras para buscar
solo el título, así que la búsqueda sí se hizo bien.

**En el código:** ese bloque lo genera `ResumenBusqueda.formatear()` y cada línea
es un `EstadoMotor`.

### Error: "ModuleNotFoundError: No module named 'ollama'"

**Causa:** No activaste el entorno virtual o no instalaste las dependencias.

**Solución:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Fallo en el procesamiento del LLM"

**Causa:** El modelo de IA no está instalado, Ollama no responde, o el modelo
devolvió algo que no se pudo interpretar.

**Solución:**
```bash
ollama pull qwen2.5:7b
ollama serve
```

### Las series no devuelven nada

**Causa:** EZTV necesita identificar la serie en IMDb. Si usas `--no-imdb` o la
resolución falla, EZTV no puede buscar.

**Solución:** No uses `--no-imdb`, o incluye el identificador de IMDb en tu
búsqueda, por ejemplo: `python3 main.py "tt11280740"`.

**En el código:** `resolver_imdb_id()` con la preferencia `TIPOS_TV`, que evita
confundir una serie con una película homónima.

### Un resultado no tiene nada que ver con lo que pedí

**Causa:** algún índice, cuando no encuentra coincidencias reales, devuelve una lista
genérica (se ha visto en LimeTorrents con títulos poco comunes). El filtro de relevancia
quita casi todo, pero un título que contenga tu palabra por casualidad puede colarse.

**Solución:** prueba con el título original (a menudo en inglés) o excluye ese índice en
esa búsqueda:

```bash
python3 main.py "Amélie" --sin-motores LimeTorrents
```

### Un índice aparece como [FALLO] todos los días

**Causa:** Los índices de torrents cambian de dominio con frecuencia (por ejemplo
`limetorrents.lol` redirige a `limetorrents.fun`, y `yts.mx` dejó de resolver).

**Solución:** Ejecuta el verificador para ver qué dominios responden hoy y actualiza
la lista correspondiente en `engines.py`: `BASE_URLS_YTS`, `BASE_URLS_LIME`,
`BASE_URLS_MAGNETDL`, `BASE_URLS_EZTV` o `BASE_URLS_NYAA`:

```bash
python3 scripts/verificar_engines.py
```

---

---

## Uso por terminal (avanzado)

Todo lo que hace la app por debajo se puede hacer a mano desde la terminal. Sirve para
automatizar, para depurar y para saber exactamente qué se está ejecutando. Nada de esta sección
es necesario para usar la app.

### Qué hace el backend

VANTAGE es un sistema que te permite buscar torrents usando lenguaje natural. En lugar de tener que saber cómo funcionan los buscadores de torrents, simplemente le escribes lo que quieres en español (o inglés) y el sistema se encarga de todo.

**Ejemplo:** Escribes "Busca la serie Severance" y VANTAGE consulta varios índices a la vez y te devuelve el resultado con más semillas.

**Características avanzadas:**
- Búsqueda multi-motor: YTS (películas), LimeTorrents (general), Nyaa (anime), EZTV (series) y MagnetDL (general)
- Deduplicación automática por hash: si dos índices tienen el mismo torrent, se queda la copia con más semillas
- Filtrado por semillas mínimas y ordenación por estabilidad (más semillas primero)
- **Diagnóstico por motor:** si algo falla, te dice qué índice falló y por qué
- **Filtro de relevancia:** evita resultados que no tienen que ver con lo que pediste
- Salida en texto o JSON, y opción de ver los N mejores resultados

> **Este manual es para usar VANTAGE, no para programarlo.** Aun así, cada sección
> indica el módulo, la función o la constante responsable, para que puedas pasar del
> comportamiento que ves al código que lo produce. Las referencias son por **nombre**
> (no por número de línea), así que siguen siendo válidas aunque el código cambie.

---

### Uso del CLI


#### Paso 1: Asegúrate de que Ollama esté corriendo


Ollama debe estar ejecutándose en segundo plano. Generalmente se inicia automáticamente cuando lo instalas. Si no, ejecuta:

```bash
ollama serve
```

(Déjalo corriendo en una terminal separada)

#### Paso 2: Activa el entorno virtual (si no lo está)


```bash
source venv/bin/activate
```

#### Paso 3: Ejecuta VANTAGE con tu búsqueda


```bash
python3 main.py "Busca la película Oppenheimer"
```

### Opciones de la línea de comandos

Puedes añadir opciones al final del comando:

| Opción | Para qué sirve | En el código |
| --- | --- | --- |
| `-n 5` | Muestra los 5 mejores resultados en lugar de solo el mejor | `main.construir_parser()` (`--all`) y el recorte en `main.ejecutar()` |
| `-s 20` | Sube el mínimo de semillas a 20 (por defecto son 5) | `main.SEEDERS_MINIMOS_POR_DEFECTO` → `AgregadorTorrents.buscar_con_diagnostico(min_seeders=...)` |
| `-v` | Muestra el detalle de cada motor: resultados, tiempos y errores | `ResumenBusqueda.formatear()` y `EstadoMotor.linea()` |
| `--json` | Devuelve la respuesta en formato JSON (útil para otros programas) | `main._payload_json()` |
| `-m mistral` | Usa otro modelo de Ollama | `ai_agent.MODELO_POR_DEFECTO` → `procesar_peticion_usuario(model=...)` |
| `--no-imdb` | No consulta IMDb (puede dejar sin resultados a las series) | `buscar_con_diagnostico(resolver_imdb=False)` |
| `--secuencial` | Consulta los motores uno por uno, con pausas (más lento) | `AgregadorTorrents(paralelo=False)` |
| `--sin-relevancia` | No filtra por coincidencia con tu búsqueda (ver más abajo) | `buscar_con_diagnostico(exigir_coincidencia=False)` |
| `--host http://...` | Usa otro servidor de Ollama (por defecto `http://localhost:11434`) | `main.HOST_OLLAMA_POR_DEFECTO` → `main.conectar_llm()` |
| `--debug` | Muestra información técnica de depuración | `logging.basicConfig(level=DEBUG)` en `main.ejecutar()` |
| `--motores LISTA` | Consulta solo los índices que le digas (ej. `--motores LimeTorrents,EZTV`) | `seleccionar_motores()` en `engines.py` |
| `--sin-motores LISTA` | **No** consulta los índices que le digas (override manual) | `seleccionar_motores()` en `engines.py` |
| `--salud auto\|off\|reset` | Controla el historial de índices caídos: `auto` (por defecto), `off` lo ignora, `reset` lo borra | `SaludMotores` en `salud_motores.py` |

**Ejemplo con varias opciones:**

```bash
python3 main.py "Busca la serie Severance" -n 3 -v
```

Salida (resumida):

```
Extracción LLM: query='Severance' categoria='tv'
consulta='Severance' categoria=tv min_seeders=5
imdb_id=tt11280740
items: 119 brutos, 98 únicos, 0 descartados por relevancia
[OMITIDO] YTS            no soporta categoria='tv'
[OK]      LimeTorrents   40 resultado(s) (659 ms)
[FALLO]   MagnetDL       ErrorFuenteNoDisponible: ningún mirror respondió: ...
[OK]      EZTV           79 resultado(s), imdb=tt11280740 (1129 ms)
[OK]      Nyaa           0 resultado(s) (426 ms)

Resultado #1:
  Title:    Severance S02E10 1080p WEB H264-SuccessfulCrab
  ...
```

Ese bloque `[OK] / [FALLO] / [OMITIDO]` es el **diagnóstico**: te dice exactamente qué motor
respondió, cuántos resultados dio, cuánto tardó y, si falló, el motivo.

---

### Más ejemplos por terminal

Puedes escribir tus búsquedas en lenguaje natural:

- `python3 main.py "Busca la serie Severance"`
- `python3 main.py "Quiero la película Dune 2021"`
- `python3 main.py "Busca la película Oppenheimer 2023" -n 5`
- `python3 main.py "Necesito Adobe Photoshop"`
- `python3 main.py "anime Frieren"`

El sistema detecta automáticamente la categoría (películas, series, anime, música,
juegos, aplicaciones o libros) y busca en los índices que sirven esa categoría. Por
ejemplo, si pides música, no perderá tiempo consultando EZTV (que solo tiene series).

---

---

## Estructura del Proyecto

La **app** (BitPuller) es la interfaz y se instala aparte, en `/Applications/Glaze/BitPuller.app`;
su código vive en `~/Glaze/Vantage Search/sources/`, y la app llama al backend por su ruta.

El **backend** vive en `~/Documents/03 Projects/VANTAGE/Bittorrent_Search`, con su propio
entorno de Python instalado dentro (`venv/`). Estos son sus archivos:

- `main.py` - Programa principal que une todo (línea de comandos)
- `ai_agent.py` - Módulo que usa IA para entender tu búsqueda
- `engines.py` - Motores de búsqueda multi-índice (YTS, LimeTorrents, Nyaa, EZTV, MagnetDL)
- `resolver.py` - Identifica series y películas en IMDb (necesario para EZTV)
- `texto.py` - Limpieza de texto, categorías, saneado de tu frase y comparación de títulos
- `scraper.py` - Compatibilidad con la versión anterior (solo Nyaa)
- `salud.py` - Comprueba que todo esté en su sitio (Python, dependencias, Ollama, modelo)
- `salud_motores.py` - Recuerda qué índices están fallando para no esperarlos
- `scripts/vantage-search` - Punto de entrada para la app de escritorio y otros programas
- `scripts/verificar_engines.py` - Comprueba qué índices están vivos hoy
- `tests/vantage/` - Pruebas automatizadas que no necesitan internet
- `requirements.txt` / `requirements-dev.txt` - Dependencias de ejecución y de pruebas
- `venv/` - Entorno de Python de esta carpeta (ya viene con las dependencias)
- `VERIFICACION_ENGINES.md` - Informe de qué índices respondieron y con qué latencia
- `handoffs/` - Notas de traspaso de este subsistema
- `README.md` - Documentación técnica para desarrolladores

---

---

## Mapa del código: de la palabra a la función

| Lo que ves o quieres cambiar | Función o constante | Archivo |
| --- | --- | --- |
| Entender tu frase (LLM) | `procesar_peticion_usuario()`, `SYSTEM_PROMPT` | `ai_agent.py` |
| Quitar "película" de la búsqueda | `limpiar_consulta()`, `PALABRAS_INTENCION`, `ARTICULOS_INICIALES` | `texto.py` |
| Categorías en español o inglés | `normalizar_categoria()`, `ALIAS_CATEGORIAS` | `texto.py` |
| Descartar resultados irrelevantes | `coincide_titulo()`, `PALABRAS_VACIAS` | `texto.py` |
| Buscar películas en YTS | `buscar_torrents_yts()`, `BASE_URLS_YTS`, `GENEROS_YTS` | `engines.py` |
| Buscar en LimeTorrents | `buscar_torrents_limetorrents()`, `CATEGORIAS_LIME`, `ETIQUETAS_LIME` | `engines.py` |
| Buscar anime en Nyaa | `buscar_torrents_nyaa()`, `CATEGORIAS_NYAA` | `engines.py` |
| Buscar series en EZTV | `buscar_torrents_eztv()` | `engines.py` |
| Buscar en MagnetDL | `buscar_torrents_magnetdl()`, `BASE_URLS_MAGNETDL` | `engines.py` |
| Identificar serie o película en IMDb | `resolver_imdb_id()`, `TIPOS_TV`, `TIPOS_PELICULA` | `resolver.py` |
| Decidir qué motores se consultan | `Motor.soporta()`, `MOTORES_POR_DEFECTO` | `engines.py` |
| Saltarse un índice caído | `seleccionar_motores()`, `ALIAS_MOTORES` | `engines.py` |
| Comprobar que todo está listo | `informe()`, `comprobar_ollama()` | `salud.py` |
| No volver a esperar a un índice caído | `SaludMotores.decision()`, `registrar()` | `salud_motores.py` |
| Ejecutar la búsqueda (en paralelo) | `buscar_con_diagnostico()`, `AgregadorTorrents` | `engines.py` |
| Deduplicar y ordenar por semillas | `deduplicar()`, `_ordenar_por_estabilidad()` | `engines.py` |
| Construir un magnet desde un hash | `construir_magnet()`, `TRACKERS_POR_DEFECTO` | `engines.py` |
| El bloque `[OK] / [FALLO] / [OMITIDO]` | `EstadoMotor`, `ResumenBusqueda.formatear()` | `engines.py` |
| Opciones de la línea de comandos | `construir_parser()` | `main.py` |
| Códigos de salida 0 / 2 / 3 / 4 | `EXIT_OK`, `EXIT_SIN_RESULTADOS`, `EXIT_ERROR_LLM`, `EXIT_MOTORES_CAIDOS` | `main.py` |
| Saber qué índices están vivos | `sondear_todo()`, `probar_motores()`, `SONDAS` | `scripts/verificar_engines.py` |
| Pruebas que no tocan red | `test_busqueda_torrents.py`, `conftest.py` | `tests/vantage/` |

---

---

## Recetas para cambiar el comportamiento

Cada receta indica el identificador exacto que hay que tocar. Son cambios dentro de la
carpeta del proyecto; después conviene ejecutar las pruebas (abajo del todo).

### Cambiar el modelo de IA por defecto

En `ai_agent.py`:

```python
MODELO_POR_DEFECTO = "qwen2.5:7b"   # escribe aquí el modelo que tengas en Ollama
```

Sin editar nada también puedes usar otro modelo puntualmente:

```bash
python3 main.py "Dune" -m mistral
```

### Cambiar el mínimo de semillas por defecto

En `main.py`:

```python
SEEDERS_MINIMOS_POR_DEFECTO = 5   # el -s de la línea de comandos lo sobreescribe
```

### Cambiar o añadir un dominio (mirror)

En `engines.py`, cada motor tiene su lista. **El orden importa**: se prueba el primero
y se cae al siguiente si falla.

```python
BASE_URLS_YTS = ("https://yts.gg", "https://yts.mx", "https://yts.lt", "https://yts.am")
BASE_URLS_LIME = ("https://www.limetorrents.fun", "https://www.limetorrents.lol")
```

Antes de tocar nada, mira qué responde hoy (y no edites a ciegas):

```bash
python3 scripts/verificar_engines.py
```

### Añadir un motor nuevo

1. Escribe una función con la firma
   `buscar_torrents_mi_indice(query, categoria=None, min_seeders=5)` que devuelva una
   lista de diccionarios con `title`, `magnet`, `seeders`, `leechers`, `size` y
   `source`. Puedes reutilizar `construir_magnet()` y el ayudante interno `_item()`.
2. Regístrala en `MOTORES_POR_DEFECTO`:

```python
Motor("MiIndice", buscar_torrents_mi_indice, ("movies", "all"), nota="HTML propio"),
```

El agregador la usa solo: aparece en el diagnóstico, entra en la deduplicación y
respeta el orden por semillas. El contrato de datos y de errores que debe cumplir esa
función (lista de diccionarios, cuándo devolver `[]` y cuándo lanzar excepción) está en
el docstring de `engines.py` y en el `README.md`.

### Cambiar cómo se clasifican las categorías

La tabla de sinónimos está en `texto.py`. Añade la palabra y su categoría canónica
(`movies`, `tv`, `anime`, `music`, `games`, `applications`, `books`, `all`):

```python
ALIAS_CATEGORIAS = {
    "documental": "movies",   # ejemplo
    ...
}
```

Si el índice tiene su propio código de categoría, añádelo en `CATEGORIAS_NYAA`,
`CATEGORIAS_LIME` o `GENEROS_YTS` (todos en `engines.py`).

### Ajustar el saneado de tu frase

En `texto.py`:

```python
PALABRAS_INTENCION = frozenset("""pelicula peliculas movie movies ...""".split())
ARTICULOS_INICIALES = frozenset({"the", "a", "an", "la", "el", ...})
```

Si una palabra de esa lista forma parte de un título que te interesa, quítala de
`PALABRAS_INTENCION` y dejará de eliminarse.

### Cambiar la preferencia de IMDb (series o películas)

`TIPOS_TV` y `TIPOS_PELICULA` (en `resolver.py`) definen el orden de preferencia. EZTV
usa `TIPOS_TV` para no confundir una serie con una película con el mismo nombre.

### Reducir el tiempo de espera por petición

`TIMEOUT_POR_DEFECTO` en `engines.py` (12 s) y en `resolver.py` (10 s). Con MagnetDL
caído, ese timeout es lo que más alarga una búsqueda.

### Índices caídos: qué hace VANTAGE solo

No hace falta que hagas nada. Tras **dos fallos seguidos** de un índice, VANTAGE deja
de consultarlo durante 30 minutos (verás `[SALTADO]` en el diagnóstico en vez de
`[FALLO]`) y lo reintenta con un timeout corto cuando vence ese plazo. Si vuelve a
funcionar, se recupera sin que toques nada.

El historial vive en `.estado_motores.json` (borrable a mano) y puedes controlarlo:

```bash
python3 main.py "Severance" --salud off      # ignora el historial en esta búsqueda
python3 main.py "Severance" --salud reset    # borra el historial
```

### Forzar los índices a mano (opcional)

Normalmente **no necesitas esto**: de los índices caídos se encarga el historial automático
que acabas de leer. Estos comandos sirven para excluir un índice por preferencia propia
(por ejemplo, si nunca quieres anime) o para forzar una comparación:

```bash
python3 main.py "Severance" --sin-motores MagnetDL
python3 main.py "Dune" --motores LimeTorrents,EZTV
python3 main.py "Dune" --motores LimeTorrents,EZTV,nyaa.si
```

Acepta los nombres (`YTS`, `LimeTorrents`, `MagnetDL`, `EZTV`, `Nyaa`) o sus dominios
(`yts.gg`, `nyaa.si`), sin distinguir mayúsculas ni acentos, y sin importar el orden.
Excluir un índice a mano consigue el mismo efecto que ya hace el historial automático
(~14 s → ~2,5 s), pero solo para esa ejecución.

### Verificar que no rompiste nada

```bash
source venv/bin/activate
pytest tests/vantage -q
python3 scripts/verificar_engines.py
```

---

---

## ¿Qué sigue?

Las recetas de la sección anterior cubren los cambios más habituales (modelo de IA,
mirrors, semillas mínimas, categorías, timeouts). Para la arquitectura completa y el
contrato de datos está el `README.md`. Para comprobar que todo sigue vivo después de
un cambio:

```bash
source venv/bin/activate
pytest tests/vantage -q
python3 scripts/verificar_engines.py
```

---

---

**Nota legal:** Este sistema es para fines educativos y de investigación. El uso de torrents para descargar contenido protegido por derechos de autor puede ser ilegal en tu jurisdicción. Úsalo responsablemente.
