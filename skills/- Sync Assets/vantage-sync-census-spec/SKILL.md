---
name: vantage-sync-census-spec
description: Edita de forma determinista la estructura CENSUS_SPEC dentro de Layer_1/scripts/generate_census.py para dar de alta IDs marcados como "huérfanos (en docs, fuera de spec)" en el reporte de vcensus. Usar cuando el operador pida "sincronizar Census Spec", "registrar IDs huérfanos en el spec" o similar, o cuando un reporte reciente de vcensus muestre IDs huérfanos fuera de CENSUS_SPEC que requieran alta. No aplica a la sincronización de SCRIPT LIBRARY (ver vantage-sync-script-library) ni SKILL LIBRARY (ver vantage-sync-skill-library) — es exclusivo de la estructura interna CENSUS_SPEC del propio generador de Census.
---

## Convención de anuncio (KERNEL:DOCUMENTATION-005)

- Apertura: `SYNCING CENSUS SPEC...`
- Cierre: `CENSUS SPEC SYNCED`

## Manejo de cero candidatos

Si el reporte de `vcensus` no muestra IDs bajo "huérfanos (en docs, fuera de spec)", no hay nada que escribir — reportar "Census Spec ya está en sync" y cerrar sin Dry Run ni edición de archivo.

## Contexto operativo

Esta skill NO reemplaza `vcensus` — lo consume. `vcensus` es de solo lectura (compara los IDs referenciados en los nueve documentos fundacionales contra la lista `CENSUS_SPEC` hardcodeada en `generate_census.py`). Un ID "huérfano (en docs, fuera de spec)" es un ID que ya existe en un documento vivo (con su ancla, sección y nombre reales) pero que el generador de Census todavía no conoce — por lo tanto no aparece en la tabla renderizada del ID CENSUS. Esta skill es la mitad de escritura: toma esa lista de huérfanos y decide qué entrada nueva inyectar en `CENSUS_SPEC`, dónde, y con qué contenido exacto.

**Archivo objetivo:** `Layer_1/scripts/generate_census.py`, estructura `CENSUS_SPEC` (lista de diccionarios, uno por bloque documental: KERNEL, MANUAL, CANON, SP, ALIASES, BRIEF, etc.). Cada entrada de ID sigue el formato:

```python
{"id": "PREFIX:KEY", "seccion": "NN.N", "nombre": "Título de la sección"}
```

## Contrato de Cero Inferencia (obligatorio)

Antes de proponer cualquier inyección, para cada ID huérfano se necesitan tres datos confirmados contra el documento fuente vivo (no memoria, no el propio reporte de vcensus como única fuente):

1. **ID exacto** (`PREFIX:KEY`, formato canónico mayúsculas, sin `§`).
2. **Número de sección** (`seccion`, formato `NN` o `NN.N` consistente con las entradas vecinas del mismo bloque).
3. **Nombre/título** (`nombre`, tal como aparece en el heading real del documento).

Si cualquiera de los tres no es evidente por inspección directa del documento fuente (vía `notion-fetch` o export ya presente en la sesión), **detener y preguntar al operador** — nunca inferir número de sección por interpolación ni inventar un nombre a partir del ID. Esto aplica incluso si el patrón parece obvio por analogía con entradas cercanas.

## Fase de Detección

1. Ejecutar o recibir el reporte más reciente de `vcensus`. Si tiene más de ~5 minutos de antigüedad en la sesión, volver a correrlo.
2. Extraer la lista bajo "huérfanos (en docs, fuera de spec)". Ignorar cualquier otra categoría del reporte (huérfanos "fuera de docs" son un problema inverso, no de esta skill).
3. Si la lista está vacía → cerrar por manejo de cero candidatos (ver arriba).

## Fase de Mapeo

1. Para cada ID huérfano, identificar el bloque de `CENSUS_SPEC` correspondiente según su prefijo:

| Prefijo | Bloque en CENSUS_SPEC |
|---|---|
| `KERNEL:` | KERNEL |
| `MANUAL:` | MANUAL |
| `CANON:` | CANON |
| `SP:` | SYSTEM PROMPT |
| `ALIASES:` | ALIASES |
| `BRIEF:` | NAVIGATION BRIEF |

Si un ID trae un prefijo que no está en esta tabla, detener y preguntar al operador — no crear un bloque nuevo sin confirmación explícita (riesgo de fragmentar `CENSUS_SPEC` con una categoría fantasma).

2. Dentro del bloque, ubicar el punto de inserción respetando **orden numérico estricto de sección** (`seccion`) — no agregar al final del bloque por default. Si el nuevo ID cae entre dos secciones existentes (ej. nueva `03.7` entre `03.6` y `03.8`), insertar ahí.
3. Confirmar (por lectura directa del archivo, no memoria) el formato exacto de las entradas vecinas — comillas, espaciado, orden de claves (`id`, `seccion`, `nombre`) — para que la entrada nueva sea sintácticamente idéntica en estilo.

## Fase de Inyección

1. Releer el bloque relevante de `generate_census.py` inmediatamente antes de construir el `old_str`/patrón de `sed` — nunca reutilizar una lectura previa de la sesión si hubo alguna escritura intermedia al archivo.
2. Construir la entrada nueva:
   ```python
   {"id": "PREFIX:KEY", "seccion": "NN.N", "nombre": "Título"},
   ```
3. Insertar usando edición de archivo (`str_replace`/`sed`) ubicando como ancla la entrada inmediatamente anterior o posterior en la secuencia numérica del mismo bloque — nunca un patrón ambiguo que pueda matchear más de una posición en el archivo.
4. **Invisibilidad Estructural (MANUAL:PATCH-QUALITY / MANUAL:15):** la entrada inyectada debe ser indistinguible del resto de la lista — mismo estilo de comillas, misma indentación, misma coma final, sin comentarios explicativos inline, sin metadata de "agregado por Claude en fecha X". El objetivo es que un lector del archivo no pueda diferenciar líneas escritas a mano de líneas inyectadas por esta skill.
5. No tocar ninguna otra parte del script (lógica de extracción, requests de red, parsing de anclas) — el diff debe limitarse exclusivamente a líneas dentro de `CENSUS_SPEC`.

## Fase de Validación (GATE — obligatoria, no omitible)

1. `python3 -m py_compile Layer_1/scripts/generate_census.py` — debe salir sin error. Si falla, revertir la edición antes de continuar (no dejar el script en estado roto entre turnos).
2. Ejecutar `vcensus` de nuevo y confirmar que cada ID recién inyectado:
   - Ya no aparece en "huérfanos (en docs, fuera de spec)".
   - Aparece correctamente renderizado en la tabla del ID CENSUS con la sección y nombre esperados.
3. Si algún ID sigue apareciendo como huérfano tras la inyección, no reintentar a ciegas — inspeccionar el diff aplicado contra el patrón real que usa `vcensus` para matchear `CENSUS_SPEC` (posible mismatch de comillas, espacios, o clave mal escrita) antes de un segundo intento.
4. Solo tras Gate exitoso (py_compile limpio + vcensus confirma alta) se considera cerrada la fase de escritura.

## Protocolo de escritura (Dry Run → Aprobación → Ejecución)

Aunque el archivo objetivo es local (no Notion), esta skill sigue el mismo protocolo de aprobación que el resto de VANTAGE por tratarse de una edición estructural de infraestructura L0:

1. **Dry Run:** presentar al operador, por cada ID a inyectar, el diff propuesto exacto (bloque, línea de anclaje, contenido nuevo) — no ejecutar nada todavía.
2. Esperar variante válida de aprobación: `APROBAR_WRITE` · `APROBAR` · `SÍ` · `sí` · `YEP` · `yep`. Tokens inválidos (no proceder con estos): `Ok` · `Go` · `yes` · `YES`.
3. Ejecutar la inyección (Fase de Inyección).
4. Correr el Gate de Validación.
5. Cerrar con resumen: cuántos IDs se dieron de alta, en qué bloques, y cualquier huérfano que quedó pendiente por falta de confirmación del operador (Contrato de Cero Inferencia).

## Restricciones

- No modificar lógica de red, extracción de anclas, o cualquier función fuera de la lista literal `CENSUS_SPEC`.
- No inferir sección o nombre cuando no son evidentes en el documento fuente — preguntar (Contrato de Cero Inferencia).
- No crear bloques nuevos en `CENSUS_SPEC` para prefijos no listados sin confirmación explícita del operador.
- No dejar el script en estado no compilable entre turnos — cualquier fallo de `py_compile` se revierte antes de cerrar.
- No anotar ni comentar las entradas inyectadas de forma que se distingan del resto (Invisibilidad Estructural).

## Cierre de sesión standalone (KERNEL:DOCUMENTATION-009)

Si esta skill se ejecuta fuera de una sesión formal `vantage-session-open`/`close`, cerrar con resumen breve (IDs dados de alta, bloques tocados, resultado del Gate) antes de terminar el turno, consistente con el resto del protocolo VANTAGE.