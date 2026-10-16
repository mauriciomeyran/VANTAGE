# Brief técnico — App de escritorio (macOS) para VANTAGE BitTorrent Search

**Destinatario:** agente de Glaze (Raycast) para construir la app
**Versión:** 1.0 — 2026-10-14
**Backend existente:** `~/Documents/03 Projects/VANTAGE/Bittorrent_Search` (Python, ya funciona)

> Este brief describe **qué debe hacer** la app, **con qué datos trabaja** y **cómo se ve**. No prescribe framework ni estructura de archivos: eso lo decide el agente de Glaze. Lo que sí es obligatorio es el contrato de integración de la sección 4 y la copia visible del **Anexo A** (integrada desde `MANUAL_USUARIO.md`).

---

## 1. Objetivo

Una app de escritorio para Mac que ponga interfaz gráfica al motor de búsqueda que **ya existe** en Python: el usuario escribe una petición en lenguaje natural ("la serie Severance", "Oppenheimer 2023") y la app devuelve la lista de resultados ordenados por semillas, con su magnet listo para copiar.

La app es **una capa de interfaz sobre el pipeline actual**. No se reescribe la lógica de búsqueda: se invoca y se muestra.

### Lo que la app resuelve hoy en terminal

```
$ python3 main.py "Busca la serie Severance" --verbose -n 2
Extracción LLM: query='Severance' categoria='tv'
imdb_id=tt11280740
items: 119 brutos, 98 únicos, 0 descartados por relevancia
[OMITIDO] YTS            no soporta categoria='tv'
[OK]      LimeTorrents   40 resultado(s) (659 ms)
[FALLO]   MagnetDL       ErrorFuenteNoDisponible: ningún mirror respondió: ...
[OK]      EZTV           79 resultado(s), imdb=tt11280740 (1129 ms)
[OK]      Nyaa           0 resultado(s) (426 ms)

Resultado óptimo:
  Title:    Severance S02E10 1080p WEB H264-SuccessfulCrab
  Magnet:   magnet:?xt=urn:btih:f66008699dbee820082b4de1ce59c560d9d6dd85&dn=...
  Seeders:  3845
  Leechers: 1321
  Size:     5.69 GB
  Source:   LimeTorrents
```

La app debe reproducir esa información en una ventana nativa, con la lista completa en vez de un solo resultado.

---

## 2. No-objetivos (explícitos)

- **No descarga torrents** ni los abre en un cliente. Solo busca metadatos y entrega el magnet (copiar al portapapeles).
- **No reimplementa** el scraping, el parseo del LLM ni la deduplicación en otro lenguaje.
- **No es web, ni móvil, ni extensión de navegador.**
- **No sustituye al CLI**: ambos usan el mismo backend y deben convivir.
- **No añade telemetría** ni envía las búsquedas a ningún servicio propio.

---

## 3. Contexto técnico: el backend ya existe

| Dato | Valor |
| --- | --- |
| Carpeta del backend | `/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search` |
| ⚠️ Atención | La ruta **contiene un espacio** (`03 Projects`): hay que citarla siempre |
| Intérprete | `venv/bin/python` (Python 3.15) — **ya tiene las dependencias instaladas** |
| Script de entrada | `main.py` |
| Dependencia externa | **Ollama** corriendo en `http://localhost:11434` con el modelo `qwen2.5:7b` |
| Salida máquina-legible | Sí: `--json` (sección 4.2) |
| Documentación | `README.md` (técnica), `MANUAL_USUARIO.md` (uso) en la misma carpeta |

**Comando que la app debe ejecutar** (equivale a una búsqueda completa):

```bash
"/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search" \
  "Busca la serie Severance" --json
```

> Encapsula la ruta del `venv` y la del script. Si por lo que sea hubiera que llamar al
> intérprete directamente, sería
> `"<carpeta>/venv/bin/python" "<carpeta>/main.py" "<consulta>" --json`, con la misma salida.

---

## 4. Contrato de integración (obligatorio)

### 4.1 Cómo se invoca

- Se lanza **un proceso por búsqueda** ejecutando `scripts/vantage-search` (el wrapper
  encapsula el `venv`; no hay que saber dónde está el intérprete).
- El wrapper puede fallar **antes** de llegar al backend: en ese caso escribe en stdout
  `{"error": {"tipo": ..., "mensaje": ...}}` y sale con **65**. La app debe leer
  `.error.mensaje` y mostrarlo (es el caso "falta el backend").
- Para el botón **Comprobar conexión**, ejecutar `scripts/vantage-search --doctor`. Devuelve
  el informe completo del backend:

  ```json
  { "ok": true, "raiz": "<carpeta>", "host": "http://localhost:11434",
    "modelo": "qwen2.5:7b",
    "checks": [ { "nombre": "ollama", "ok": true, "detalle": "..." }, ... ],
    "motores": [ { "nombre": "MagnetDL", "degradado": true, "fallos_consecutivos": 3,
                   "ultimo_exito": null, "ultimo_fallo": "2026-10-15 16:47:19",
                   "ultimo_error": "ErrorFuenteNoDisponible: ...",
                   "nota": "Sin respuesta verificado el 2026-10-14/15: ..." } ] }
  ```

  **Códigos de salida: 0 si todo está bien, 66 si alguna comprobación falla.** El 65 está
  reservado para el wrapper cuando no encuentra el backend, así que un cliente distingue
  los dos casos por el código: si el JSON trae `.error` es el wrapper; si trae `.ok` y
  `.checks` es el informe del doctor.
- La consulta del usuario se pasa **como un único argumento** entre comillas.
- `--json` en stdout es la **única** fuente de datos: la app **no debe** parsear la salida en modo texto.
- `stderr` puede traer mensajes de diagnóstico o de error: guardarlos para mostrarlos si algo falla.
- **Nunca** matar el proceso por cerrar la ventana: si el usuario cierra la ventana con una búsqueda en curso, se cancela limpiamente o se deja terminar.

### 4.2 JSON de salida (estructura exacta)

```json
{
  "consulta": { "query": "Severance", "categoria": "tv" },
  "resultados": [
    {
      "title": "Severance S02E10 1080p WEB H264-SuccessfulCrab",
      "magnet": "magnet:?xt=urn:btih:f66008699dbee820082b4de1ce59c560d9d6dd85&dn=...&tr=...",
      "seeders": 3845,
      "leechers": 1321,
      "size": "5.69 GB",
      "source": "LimeTorrents"
    }
  ],
  "mejor": { "title": "...", "magnet": "...", "seeders": 3845, "leechers": 1321, "size": "5.69 GB", "source": "LimeTorrents" },
  "diagnostico": {
    "consulta_efectiva": "Severance",
    "consulta_original": "Busca la serie Severance",
    "categoria": "tv",
    "imdb_id": "tt11280740",
    "error_imdb": null,
    "min_seeders": 5,
    "items_brutos": 119,
    "items_unicos": 98,
    "descartados_por_relevancia": 0,
    "motores_consultados": ["LimeTorrents", "EZTV", "Nyaa"],
    "motores": [
      { "nombre": "YTS", "ok": true, "omitido": true, "resultados": 0, "error": "no soporta categoria='tv'", "ms": 0, "imdb_id": null, "saltado_por_salud": false, "motivo_salud": null, "timeout_segundos": null },
      { "nombre": "LimeTorrents", "ok": true, "omitido": false, "resultados": 40, "error": null, "ms": 659, "imdb_id": null, "saltado_por_salud": false, "motivo_salud": null, "timeout_segundos": null },
      { "nombre": "MagnetDL", "ok": false, "omitido": false, "resultados": 0, "error": "ErrorFuenteNoDisponible: ...", "ms": 15284, "imdb_id": null, "saltado_por_salud": false, "motivo_salud": null, "timeout_segundos": null },
      { "nombre": "EZTV", "ok": true, "omitido": false, "resultados": 79, "error": null, "ms": 1129, "imdb_id": "tt11280740", "saltado_por_salud": false, "motivo_salud": null, "timeout_segundos": null },
      { "nombre": "Nyaa", "ok": true, "omitido": false, "resultados": 0, "error": null, "ms": 426, "imdb_id": null, "saltado_por_salud": false, "motivo_salud": null, "timeout_segundos": null }
    ]
  }
}
```

| Campo | Tipo | Notas para la UI |
| --- | --- | --- |
| `consulta.query` | texto | Lo que **entendió el LLM** (puede incluir la categoría: "película Oppenheimer") |
| `consulta.categoria` | texto | Una de: `movies`, `tv`, `anime`, `music`, `games`, `applications`, `books`, `all` |
| `resultados[]` | lista | Puede venir **vacía**; puede traer **90+ elementos**; ya viene ordenada por semillas descendente |
| `resultados[].title` | texto | Nombre del release (calidad y fuente incluidas) |
| `resultados[].magnet` | texto | **Muy largo**: se muestra truncado, se copia completo |
| `resultados[].seeders` | entero | Criterio de orden y de "estabilidad" |
| `resultados[].leechers` | entero | |
| `resultados[].size` | texto | Puede ser `"N/A"` |
| `resultados[].source` | texto | Uno de: `YTS`, `LimeTorrents`, `Nyaa`, `EZTV`, `MagnetDL` |
| `mejor` | objeto o `null` | El primer resultado; `null` si no hay ninguno |
| `diagnostico.consulta_efectiva` | texto | Lo que **realmente se buscó** (ya limpio). Esto es lo que hay que mostrar al usuario |
| `diagnostico.consulta_original` | texto o `null` | La frase original, solo si difiere de la efectiva |
| `diagnostico.imdb_id` | texto o `null` | Identificador usado para series |
| `diagnostico.items_brutos` / `items_unicos` | entero | Antes y después de deduplicar |
| `diagnostico.descartados_por_relevancia` | entero | Cuántos se cayeron por no coincidir con la búsqueda |
| `diagnostico.motores_consultados` | lista | Nombres de los índices **realmente consultados**: excluye los omitidos por categoría y los saltados por salud |
| `diagnostico.motores[]` | lista | Estado de cada índice: `ok`, `omitido`, `resultados`, `error`, `ms`, `imdb_id`, más los campos de salud `saltado_por_salud`, `motivo_salud` y `timeout_segundos` |

> Las cifras del ejemplo salen de una ejecución real y **cambian en cada búsqueda** (los índices se mueven minuto a minuto): sirven para conocer los nombres y los tipos de los campos, no como valores esperados.

### 4.3 Códigos de salida y qué debe hacer la UI

| Código | Significado | Respuesta de la UI |
| --- | --- | --- |
| `0` | Búsqueda con resultados | Mostrar lista y panel de diagnóstico |
| `2` | Ningún resultado pasó los filtros | Estado vacío **con la causa real**, leyendo `diagnostico.motores` en este orden: (1) si hay filas con `saltado_por_salud: true` y ninguna consulta efectiva (`motores_consultados` vacío o sin resultados), explicar que el historial de salud apartó los índices y ofrecer `--salud reset` — **no** sugerir reformular la búsqueda; (2) si todos los consultados están `ok` con 0 resultados → sugerir menos palabras o el título en inglés; (3) si alguno tiene `ok: false` → indicar que ese índice está caído |
| `3` | Falló el LLM (Ollama) | Aviso claro "Ollama no responde", botón **Reintentar**, e indicar que hace falta `ollama serve` con el modelo configurado |
| `4` | Todos los índices fallaron | Aviso de red/bloqueo, y enlace a la sección de índices del `MANUAL_USUARIO.md` |
| `64` | Argumentos inválidos | No debería pasar (la app construye los flags): mostrar los detalles |
| `65` | El wrapper no encontró el backend | Leer `.error.mensaje` del JSON de stdout y ofrecer configuración de la ruta |
| `66` | Solo `--doctor`: alguna comprobación del backend falló | Pintar `checks[]` (cada uno trae `nombre`, `ok` y `detalle`) |
| `130` | Cancelado por el usuario | Volver al estado inicial sin error |
| otro | Fallo inesperado | Mostrar el texto de `stderr` en un desplegable "detalles" |

### 4.4 Tiempos: qué puede prometer la UI

Medido en este equipo (2026-10-15):

- **Primera búsqueda tras arrancar Ollama: hasta ~45 s** (medido: 43 s): el modelo (4,7 GB) se
  carga en memoria. Solo ocurre la primera vez.
- **Régimen normal mientras un índice caído aún se intenta: ~14 s.** De ellos, 1,2–1,4 s son la
  extracción con el LLM y ~12 s el timeout de MagnetDL.
- **Cuando el backend ya apartó ese índice: ~2,5 s** (medido: 2 140–2 562 ms). Es el estado
  habitual tras las primeras búsquedas, y ocurre solo: la UI **no** debe asumir 15 s.
- El backend **no emite progreso incremental**: entrega un único JSON al final. Por tanto:
  - Mostrar un **indicador indeterminado** con **tiempo transcurrido** y un texto de fase ("interpretando tu búsqueda…", "consultando índices…").
  - **No** prometer barra de progreso porcentual.
  - Ofrecer **Cancelar** en todo momento.
  - **No** mostrar "sin resultados" hasta que el proceso termine y devuelva el código 2.

### 4.5 Opciones del CLI que la UI puede exponer (ajustes avanzados)

| Opción | Efecto | Valor por defecto |
| --- | --- | --- |
| `-s N` / `--min-seeders N` | Sembradores mínimos | `5` |
| `--sin-relevancia` | No descarta resultados que no coinciden con la búsqueda | desactivado |
| `--no-imdb` | No consulta IMDb (degrada las búsquedas de series) | desactivado |
| `--secuencial` | Consulta los índices uno a uno (más lento, más conservador) | desactivado |
| `--sin-motores LISTA` | No consulta esos índices (override manual; el backend ya se salta solo los caídos) | desactivado |
| `--salud {auto,off,reset}` | Historial de índices caídos: `auto` (por defecto) no vuelve a esperarlos, `off` lo ignora, `reset` lo borra | `auto` |
| `--motores LISTA` | Consulta solo esos índices | todos |
| `-m MODELO` | Otro modelo de Ollama | `qwen2.5:7b` |
| `--host URL` | Otro servidor de Ollama | `http://localhost:11434` |

---

## 5. Pantallas y comportamiento

### 5.1 Ventana principal — buscador y resultados

- **Barra de búsqueda** arriba, con foco al abrir la app y búsqueda con `Enter`. Ejemplos sugeridos como texto de ayuda: *"Busca la serie Severance"*, *"Oppenheimer 2023"*, *"anime Frieren"*.
- **Lista de resultados** (la vista principal), una fila por resultado con:
  - **Título** (puede ser largo: una o dos líneas con truncado elegante),
  - **Semillas** y **descargadores** como columnas numéricas ordenables,
  - **Tamaño**,
  - **Origen** como etiqueta de color (`YTS`, `LimeTorrents`, `Nyaa`, `EZTV`, `MagnetDL`).
- La lista **ya viene ordenada por semillas** de mayor a menor: conservar ese orden por defecto y permitir reordenar por tamaño o nombre.
- **Debe soportar 100+ filas con soltura** (virtualizar la lista si hace falta).
- El resultado **número 1** debe distinguirse visualmente como "mejor opción".

### 5.2 Panel de detalle (al seleccionar un resultado)

- Título completo, semillas, descargadores, tamaño y origen.
- El **magnet completo**, seleccionable y **truncado solo visualmente**: el valor copiado debe ser el íntegro.
- Botón **Copiar magnet** con confirmación breve ("Copiado").
- Botón **Copiar título**.
- **Etiqueta de calidad** cuando el título lo indique: marcar claramente `CAM`, `TS`, `HDCAM` o `HDTS` como *"calidad de cámara"* frente a `BluRay`, `WEB-DL`, `WEBRip`. En la verificación real, el primer resultado por semillas de "Oppenheimer 2023" fue un `HQ-CAM` con 1276 semillas: la UI debe avisar de eso, **sin cambiar el orden** (el orden por semillas es el criterio acordado del backend).

### 5.3 Panel de diagnóstico (siempre accesible, no invasivo)

Un panel plegable con una fila por índice: nombre, estado (`OK` / `FALLO` / `OMITIDO` / `SALTADO`), número de resultados y milisegundos; y el error literal cuando falla. Cuando un índice llega con `saltado_por_salud: true`, la fila debe explicar el `motivo_salud` y no contarse como fallo de esta búsqueda: el backend ya lo apartó tras dos fallos y lo reintentará solo.

Encima del panel, una línea resumen: *"47 resultados únicos de 49 · descartados por relevancia: 0 · IMDb: tt11280740"*.

### 5.4 Ajustes avanzados

Los de la tabla 4.5, en un panel de ajustes (no en la pantalla principal), con los valores por defecto visibles y un botón para restaurarlos. Incluir además la **ruta del backend** y el **estado de Ollama** (verde/rojo), con un botón
"Comprobar conexión" que ejecute `scripts/vantage-search --doctor` y pinte el resultado de
sus `checks` (intérprete, dependencias, Ollama, modelo).

Añadir un ajuste de **índices a consultar** (lista con casillas: YTS, LimeTorrents,
MagnetDL, EZTV, Nyaa) que se traduzca en `--motores`, y recordar la elección entre
sesiones. Es **preferencia del usuario, no salud**: de los índices caídos se encarga ya
el backend (decisión 6), así que la app no necesita llevar ninguna cuenta. Un ajuste
`--salud auto|off` basta para quien quiera forzar una comparación.

### 5.5 Estados de la app

| Estado | Qué se ve |
| --- | --- |
| Inicial (sin búsqueda) | Buscador centrado, con ejemplos; sin lista |
| Buscando | Indicador indeterminado + tiempo transcurrido + Cancelar; la lista anterior permanece atenuada. La primera búsqueda tras arrancar el modelo puede llegar a ~45 s, y ~14 s mientras se sigue intentando un índice caído: mostrarlo como normal, no como error. Cuando el backend ya lo apartó, la búsqueda baja a ~2-3 s |
| Con resultados | Lista + panel de diagnóstico |
| Sin resultados | Mensaje claro + causa real (sección 4.3, código 2) + sugerencias accionables: bajar el mínimo de semillas, quitar `--sin-relevancia`, probar el título en inglés |
| Ollama caído | Aviso con instrucciones y botón Reintentar (código 3) |
| Índices caídos | Aviso de red/bloqueo (código 4) |
| Error inesperado | Mensaje breve + detalles de `stderr` |

### 5.6 Extras deseables (fases posteriores, no MVP)

- **Historial de búsquedas** (local, con la fecha y la consulta efectiva), y repetir una búsqueda con un clic. Guardar también los últimos resultados para reabrirlos sin volver a consultar.
- **Favoritos** de releases.
- **Menú bar**: lanzar una búsqueda rápida o pegar un magnet.
- **Atajo global** para abrir la ventana y buscar.
- **Exportar** los resultados de una búsqueda a CSV/JSON.

---

### 5.7 Ayuda dentro de la app

Una pantalla de ayuda (ventana aparte o sección propia) con el contenido del
`MANUAL_USUARIO.md`, en este orden y con estas palabras: qué es VANTAGE, ejemplos de
búsqueda, interpretación de los resultados, problemas frecuentes y consejos de uso. El
detalle de los textos está en el **Anexo A**, que es copia literal del manual.

- Un botón **"Ver el manual completo"** que abra `MANUAL_USUARIO.md` en el visor del sistema.
- Los **problemas frecuentes** de la ayuda deben incluir los siete casos del manual (Anexo A.4),
  no una selección.
- Si una comprobación falla, el aviso debe enlazar con el caso correspondiente de la ayuda
  (por ejemplo, dependencias ausentes → el caso de `ModuleNotFoundError`).

---

## 6. Reglas y casos límite que hay que respetar

1. **Rutas con espacios**: la carpeta del backend contiene `03 Projects`. Citar siempre rutas y argumentos; no concatenar comandos con `&&` sin citar.
2. **Una búsqueda = un proceso**: no reutilizar procesos entre búsquedas ni asumir estado. Dos búsquedas simultáneas deben poder convivir (o bloquearse explícitamente con un aviso).
3. **No parsear texto**: usar `--json` siempre. Los mensajes de `stderr` son para mostrar, nunca para decidir el resultado.
4. **La relevancia y la deduplicación las hace el backend.** La UI no debe volver a filtrar ni reordenar por defecto: si añade un filtro local, debe ser explícito y visible para el usuario.
5. **Nunca truncar el magnet en el portapapeles.**
6. **`size` puede ser `"N/A"`** y `source` puede faltar en casos raros: la UI no debe romperse.
7. **Fuente y estado**: `ok: false` con `error` es informativo, no fatal: la búsqueda sigue siendo válida con los demás índices.
8. **Nada de descargas**: la app no abre clientes de torrents ni guarda `.torrent`.
9. **Sin telemetría** y sin peticiones de red propias más allá de lo que hace el backend.
10. **Rendimiento**: la lista virtualizada y la ventana nunca deben congelarse mientras corre el proceso; todo el trabajo del CLI va fuera del hilo de interfaz.

---

## 7. Fases de construcción (una por prompt)

| Fase | Alcance | Entregable verificable |
| --- | --- | --- |
| **0. Verificación** | Comprobar que la app puede lanzar el comando y leer el JSON | Un botón de prueba que ejecute el comando y muestre `items_unicos` y el código de salida |
| **1. MVP** | Buscador + lista + detalle + copiar magnet + estados de error | Buscar "Oppenheimer 2023" en la app y obtener la misma lista que el CLI |
| **2. Diagnóstico y calidad** | Panel de índices, etiqueta de calidad (CAM/TS), contadores y ajustes avanzados | Con MagnetDL caído se ve `FALLO` con su motivo; el `HQ-CAM` queda marcado |
| **3. Comodidad** | Historial, favoritos, menú bar, atajo global, exportar | Repetir una búsqueda del historial con un clic |

> La Fase 0 existe porque ejecutar un proceso externo es el único riesgo técnico real del proyecto. Si el entorno de la app no permitiera lanzar el intérprete del `venv`, el plan B está en la sección 9.

---

## 8. Criterios de aceptación

- [ ] Buscar `"Busca la serie Severance"` devuelve **decenas** de resultados y el mismo "mejor resultado" que el CLI (comparado a mano al menos una vez).
- [ ] Buscar `"Oppenheimer 2023"` muestra el `HQ-CAM` primero, **marcado como calidad de cámara**.
- [ ] El botón Copiar magnet deja en el portapapeles el magnet **completo** (verificado pegándolo en un editor).
- [ ] Con Ollama detenido, la app muestra el aviso del código 3 y no se queda colgada.
- [ ] Una búsqueda sin resultados (`"Zxqwvbn 1999 pelicula inexistente"`) explica **qué índice falló y con qué error**, y no solo "sin resultados".
- [ ] El panel de diagnóstico muestra los 5 índices con su estado y su tiempo, incluido MagnetDL como `FALLO`.
- [ ] Una búsqueda de 90+ resultados se desplaza con fluidez y la ventana nunca se congela.
- [ ] Cancelar durante una búsqueda devuelve la app al estado inicial sin dejar procesos huérfanos.
- [ ] El ajuste `--min-seeders` cambia visiblemente los resultados (por ejemplo, `300` reduce la lista a unos pocos).
- [ ] Desmarcar MagnetDL como índice baja el tiempo de búsqueda de ~15 s a ~2-3 s, con los mismos resultados.
- [ ] Tras dos búsquedas con un índice caído, la tercera lo muestra como `SALTADO` (no como `FALLO`) y tarda ~2 s, sin haber hecho la petición.
- [ ] El botón "Comprobar conexión" refleja el estado real (verde con Ollama arriba, rojo si se detiene).
- [ ] Los textos visibles coinciden con el Anexo A (etiquetas de A.2, ejemplos de A.3, mensajes de A.4).
- [ ] La ayuda de la app cubre los **siete** casos de A.4, no una selección, y abre `MANUAL_USUARIO.md` con su botón.

---

## 9. Riesgos y plan B

| Riesgo | Probabilidad | Plan B |
| --- | --- | --- |
| El entorno de la app no permite lanzar el intérprete del `venv` | Media | Envolver el backend en un servidor HTTP local (FastAPI) que exponga `/buscar?q=...` devolviendo el mismo JSON, y que la app lo consuma; el servidor ya incluiría la lógica de progreso |
| El usuario comparte la app y en el otro Mac no existe la carpeta ni el `venv` | Media | La app debe **comprobar** la presencia del backend al arrancar, explicar qué falta y ofrecer configurar la ruta; empaquetar el backend es un proyecto aparte |
| Ollama no instalado o modelo ausente | Media | Detección al arrancar y mensaje con el comando exacto (`ollama pull qwen2.5:7b`) |
| Índices que cambian de dominio | Alta con el tiempo | Ya está resuelto en el backend (mirrors + diagnóstico): la app no debe hardcodear dominios |
| El comando tarda y el usuario cree que se colgó | Alta | Tiempo transcurrido visible y Cancelar desde el primer segundo |

---

## 10. Decisiones abiertas (a confirmar por el autor)

1. **Empaquetado**: ¿la app asume que el backend vive en esa ruta fija (simple), o debe permitir elegir la carpeta (más robusto, más trabajo)?
2. **Idioma de la interfaz**: español (coherente con el manual) o bilingüe.
3. **Fase 3**: ¿merecen la pena historial, favoritos y menú bar desde el principio?
4. **Publicación**: ¿es una app personal o se va a compartir por el Store? (determina cuánto importa la portabilidad del punto 9).
5. ~~Wrapper opcional~~ **RESUELTO**: existe `scripts/vantage-search` (con `--doctor` para el
   estado del backend). La app debe llamarlo a él, no al `venv` directamente.

6. ~~Coste del índice caído~~ **RESUELTO en el backend**: `salud_motores.py` degrada un
   índice tras dos fallos, lo salta dentro del TTL y lo re-sondea con timeout reducido al
   vencer. Medido: **13 840 ms → 2 140 ms** con los mismos 47 resultados, y se auto-cura
   cuando el índice vuelve (el cliente no tiene que recordar nada).
   `--motores`, `--sin-motores` y `--salud` quedan como overrides explícitos.
   Detalle histórico: como MagnetDL está caído y su
   timeout es de 15 s, **cada búsqueda pierde ~15 s** esperándolo — es la mayor parte del tiempo
   total. Opciones, de menos a más trabajo:
   1. bajar `TIMEOUT_POR_DEFECTO` en `engines.py` (de 12 s a, por ejemplo, 5 s);
   2. añadir un flag `--motores` para elegir qué índices se consultan, de modo que la app pueda
      saltarse los que están caídos;
   3. recordar en memoria los motores que fallan y no reintentarlos en la misma sesión.

   Con el punto 2, la búsqueda pasaría de ~15 s a **~2–3 s** (el resto de motores tarda ~1 s en
   total). Para una app de escritorio, la diferencia entre 15 s y 3 s se nota en cada búsqueda.

---

## 11. Contexto que conviene darle al agente de Glaze

- Si el repositorio está en **GitHub**, conectar la integración de GitHub para que el agente pueda leer `README.md`, `MANUAL_USUARIO.md` y `main.py`: eso le da el contrato exacto sin que haya que copiarlo en cada prompt.
- Si no, adjuntar como referencia **este brief** y el `README.md` de la carpeta.
- Usar **Plan mode** para la Fase 1 (es una app con varios elementos: proceso externo, lista, detalle, estados de error) y Build mode para los ajustes.
- El `MANUAL_USUARIO.md` es la **fuente de verdad de la copia visible** y está integrado en el
  **Anexo A** de este brief (etiquetas, ejemplos, mensajes de error, consejos y el orden de la
  pantalla de ayuda). Adjúntalo al proyecto.


---

## Anexo A — Textos de la interfaz, integrados desde `MANUAL_USUARIO.md`

Este anexo es **copia literal** del manual de uso: es la fuente de verdad de todo lo que lee
el usuario final. Si un texto de la app cambia, cambia primero aquí y en el manual.

### A.1 Regla de sincronización

1. `MANUAL_USUARIO.md` manda sobre la copia visible: etiquetas, mensajes, ayuda y ejemplos.
2. `BRIEF_UI_GLAZE.md` (este anexo) es la versión que consume el agente: no inventes textos
   que no estén aquí o en el manual.
3. Al añadir un estado nuevo a la app, añade su texto al manual **y** a A.4.
4. Hay una prueba automática que comprueba que los siete casos de A.4 siguen existiendo como
   secciones en el manual (`tests/vantage/test_busqueda_torrents.py`).

### A.2 Etiquetas de los campos del resultado

Salen del manual («Paso 4: Interpretar los resultados») y son también las etiquetas que
imprime el CLI, así que la app debe usar **las mismas palabras**:

| Etiqueta en la UI | Texto del manual (ayuda emergente o glosario) |
| --- | --- |
| `Title` | "El nombre del torrent (incluye calidad y fuente)" |
| `Magnet` | "El enlace magnético que puedes copiar y pegar en tu cliente de torrents (Transmission, qBittorrent, etc.)" |
| `Seeders` | "Cantidad de personas compartiendo el archivo (más es mejor)" |
| `Leechers` | "Cantidad de personas descargando el archivo" |
| `Size` | "Tamaño del archivo" |
| `Source` | "Índice de origen (YTS, LimeTorrents, Nyaa, EZTV o MagnetDL)" |

### A.3 Ejemplos de búsqueda (placeholder y sugerencias)

Del manual («Ejemplos de Búsqueda»), sin el `python3 main.py`:

- "Busca la serie Severance"
- "Quiero la película Dune 2021"
- "Busca la película Oppenheimer 2023"
- "Necesito Adobe Photoshop"
- "anime Frieren"

Placeholder de la barra: `Busca la serie Severance, Oppenheimer 2023, anime Frieren...`

Además, el manual explica («Cómo interpreta tu búsqueda») que se puede escribir con
naturalidad porque el backend separa el título de palabras como "película" o "serie": eso debe
quedar dicho en la ayuda, porque si no el usuario ve que su frase se ha acortado y no entiende
por qué.

### A.4 Estados de error y vacío, con los textos del manual

Cada fila es una sección de «Solución de Problemas» del manual. La app debe mostrar el
titular y la causa, y ofrecer la solución.

| Caso (sección del manual) | Lo que muestra la app | Solución que ofrece |
| --- | --- | --- |
| `Error: "Error de conexión con Ollama"` | "El servicio de IA local no responde" + "Ollama no está corriendo" | Botón **Reintentar** y el comando `ollama serve` (código 3) |
| `Mensaje: "No results found matching criteria"` | El texto literal del CLI y, debajo, el diagnóstico por motor | Las tres ramas de §4.3: historial de salud, términos más amplios o título en inglés, o el índice concreto que falla |
| `Error: "ModuleNotFoundError: No module named 'ollama'"` | Aviso de dependencias ausentes (viene del doctor: `checks` con `dependencias` en falso, o del wrapper con código 65) | `source venv/bin/activate` y `pip install -r requirements.txt` |
| `Error: "Fallo en el procesamiento del LLM"` | Ese titular, tal cual | `ollama pull qwen2.5:7b` y `ollama serve` (código 3) |
| `Las series no devuelven nada` | Explicación de que EZTV necesita identificar la serie en IMDb | "No uses `--no-imdb`" o buscar por IMDb id (`tt11280740`) |
| `Un resultado no tiene nada que ver con lo que pedí` | Explicación de que un índice puede devolver una lista genérica cuando no encuentra coincidencias reales | Probar el título original (a menudo en inglés) o excluir ese índice (`--sin-motores LimeTorrents`) |
| `Un índice aparece como [FALLO] todos los días` | Explicación de que los índices cambian de dominio | Ejecutar `scripts/verificar_engines.py` |

### A.5 Consejos de uso (para la ayuda)

Del manual («Consejos de Uso»), literales:

1. **Sé específico:** "Película Oppenheimer 2023" funciona mejor que solo "Oppenheimer"
2. **Idioma:** Puedes escribir en español o inglés, el sistema entiende ambos
3. **Categorías:** El sistema detecta la categoría solo; si la mencionas ("película", "serie", "música", "juego", "aplicación", "libro") se respeta esa intención
4. **Seeders:** VANTAGE prioriza los torrents con más semillas para asegurar descargas más rápidas y estables
5. **Anime:** para anime, Nyaa suele dar mejores resultados que los índices generalistas

### A.6 Estado de los índices (tabla informativa)

Del manual («Estado de los índices»), que la app puede mostrar en el panel de diagnóstico:

| Índice | Estado | Notas |
| --- | --- | --- |
| YTS | Funciona | Solo películas. Se usa el dominio `yts.gg` porque `yts.mx` no resuelve |
| LimeTorrents | Funciona | Generalista. Es el que suele dar los resultados con más semillas |
| Nyaa | Funciona | Solo anime y contenido asiático: para películas occidentales devuelve vacío |
| EZTV | Funciona | Solo series, y necesita identificar la serie en IMDb (lo hace solo) |
| MagnetDL | **Caído** | No responde (timeout en `.com`, DNS en `.mx`). El motor sigue activo: si vuelve, funcionará sin cambios |

### A.7 Correspondencia manual → app

Para que nada del manual se quede sin sitio y sea fácil mantenerlos juntos:

El manual está escrito **con la app primero** y el terminal como apéndice, así que este mapeo
sigue ese orden.

| Sección del manual | Dónde aparece en la app |
| --- | --- |
| ¿Qué es BitPuller? | Ayuda, primer bloque |
| Requisitos / Instalación | Ajustes → ruta del backend y "Comprobar conexión"; el resto, en el manual |
| La interfaz → Buscador y barra de resumen | Barra de búsqueda y línea de resumen (§5.1) |
| La interfaz → Lista de resultados | Tabla de resultados, insignias de calidad y orden (§5.1, §5.2) |
| La interfaz → Panel de detalle | Inspector derecho, "Copiar magnet" (§5.2) |
| La interfaz → Panel de diagnóstico | Panel plegable con estados, latencia y `motivo_salud` (§5.3) |
| La interfaz → Ajustes avanzados | Diálogo de ajustes: los ocho controles (§5.4) |
| La interfaz → Ayuda | El propio diálogo de ayuda, que reproduce estas secciones |
| La interfaz → Historial | Barra lateral de historial (§5.6) |
| La interfaz → Menú bar y atajo global | Icono de barra de menú, popover y ⌘⇧F (§5.6) |
| La interfaz → Exportar | Botón "Exportar" (§5.6) |
| La interfaz → Cancelar una búsqueda | Botón "Cancelar" junto al cronómetro (§4.4, §5.5) |
| Cómo leer los resultados | Glosario de A.2 (etiquetas y ayudas emergentes) |
| Cómo interpreta tu búsqueda | Ayuda, bloque de comportamiento |
| Filtro de relevancia | Ayuda + ajuste "No descartar por relevancia" |
| Estados y errores de la app | Los estados de error por código de salida (§4.3) y A.4 |
| Estado de los índices | Panel de diagnóstico (§5.3) y A.6 |
| Solución de Problemas | A.4 y pantalla de ayuda (los siete casos) |
| Consejos de uso | Ayuda, bloque final (A.5) |
| Uso por terminal (apéndice) | No va en la app: es la vía avanzada del mismo backend |
| Estructura del proyecto / Mapa del código / Recetas | No van en la app: son para quien mantiene el código |
| Nota legal | Ayuda, al pie |

### A.8 Orden de la pantalla de ayuda

1. Qué es VANTAGE (dos líneas).
2. Cómo buscar: los cinco ejemplos (A.3) y la nota de que se puede escribir con naturalidad.
3. Cómo leer los resultados: el glosario (A.2).
4. Qué hacer si algo falla: los siete casos (A.4).
5. Consejos (A.5) y estado de los índices (A.6).
6. Botón "Ver el manual completo" y la nota legal.
