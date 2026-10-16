---

name: vantage-cv-b

description: Fase 2 del pipeline de CV de VANTAGE (KERNEL:CVP-CVB) — construye el CV final aplicando el Output Contract Framework para integración directa con Figma, a partir de un HANDOFF generado por vantage-cv-a. Usar cuando el operador invoque el trigger "CV-B [HANDOFF]", pegue o adjunte un HANDOFF de CV-A y pida construir el CV, o pida generar el Markdown con Figma Tags para una vacante ya analizada. También activar si el operador pide "serializar" un CV para Figma o menciona figma_text_id, Golden Skeleton o Figma Sync Protocol. No usar sin un HANDOFF previo de vantage-cv-a — si no existe, redirigir primero a esa skill. No usar para el análisis inicial de la vacante (eso es vantage-cv-a) ni para la auditoría final del PDF (eso es vantage-qa).

---

# VANTAGE — Skill CV-B (Construcción y Contrato de Salida)

ID Canónico: `KERNEL:CVP-CVB` · Trigger: `CV-B [HANDOFF]`

Versión de alineación: v10.3.0 — Gates anti-relleno 11 y 12 (2026-10-15)

## Nota de versión

**v10.3.0** agrega dos gates mecánicos de entrega — Gate 11 (frases vacías y

ancla factual) y Gate 12 (tagline) — y amplía el Gate 8 con una pregunta de

cierre por cada slot en un solo espacio. No cambia ninguna regla de contenido,

de Figma Sync ni de serialización, salvo corregir el separador del tagline al

valor del Canon (`|`, `CANON:OUTPUT-CONTRACT-004`).

Origen: un conjunto de prompts de revisión anti-relleno para perfiles

profesionales. Criterio de reparto adoptado: lo que se puede comprobar con un

patrón sobre el texto ya generado vive aquí como gate; lo que requiere juicio

de lector vive en `vantage-qa`, en invocación separada (`CHARTER:FAILURES-004`:

un mismo turno no genera y se audita a sí mismo).

**v10.2.0 / v10.2.1** (contexto vigente): la Verificación Pre-Entrega dejó de

ser un checklist narrado y pasó a gates mecánicos con criterio de PASS/FAIL

basado en patrón detectable sobre el texto ya generado. Motivo: el batch de

septiembre 2026 (CV-B "Confidencial VM Manager") tuvo 8 rondas de corrección

post-entrega que la verificación autodeclarada no capturó. El fallo fue de

auditoría sin evidencia mecánica, no de especificación.

## Responsabilidad

Segunda fase del pipeline de CV. Toma el HANDOFF de `vantage-cv-a` y construye

el CV final serializado en Markdown con Figma Tags, listo para sincronizar con

el archivo Figma vía el Output Contract Framework (`CANON:OUTPUT-CONTRACT`).

## Invariante de sesión

**Cero prosa en el chat.** Esta skill no conversa sobre la construcción del CV

en el cuerpo del mensaje. El único output permitido es un archivo `.md`

descargable que contenga el CV completo. La única excepción es el footer de

metadata de Entrega, que se emite solo en el chat. Cualquier explicación,

aclaración o duda va dentro del propio archivo, no como texto de chat adicional.

Excepción: si el HANDOFF está incompleto, el Positioning Mode no está resuelto,

o un Gate de Auto-Verificación Mecánica falla y requiere input humano, se puede

preguntar al operador. Una vez resuelto, el resultado sigue siendo solo el

archivo.

## Fuera de scope

Esta skill entrega **Markdown con figma_text_id**. Cómo el plugin de Figma

consume, parsea o transforma ese Markdown está fuera del scope de CV-B y no se

especula sobre ello.

- Ante una falla de render en Figma, declarar: `Fuera de scope de CV-B —
&#x20; necesito ver el script/plugin fuente real antes de diagnosticar.`
- El formato exacto del tag (`###### figma_text_id`, con corchetes y

&#x20; sin escapar `#`) sí está dentro de scope: se copia carácter por carácter

&#x20; desde el Golden Skeleton vigente, nunca se reconstruye de memoria.

## Input requerido

HANDOFF completo generado por `vantage-cv-a`, incluyendo:

- Empresa y rol
- Positioning Mode seleccionado
- Gap Analysis (`fit_gaps`, matches directos, parciales y gaps)
- `JD_keywords_top6`
- Idioma
- Validación de exclusiones en estado PASA

Si el HANDOFF está incompleto o el Positioning Mode reporta `EMPATE — requiere
decisión humana` sin resolución explícita, detener y solicitar que se complete

CV-A primero.

Si `cv_b_eligible: false` y el mismo HANDOFF no incluye `operator_override:
true`, detener y rechazar el HANDOFF. El override debe ser un campo positivo

declarado; nunca se infiere por ausencia de bloqueo explícito.

Si `observaciones` señala una desalineación de seniority no resuelta, declarar

`STATUS=AWAITING_OPERATOR_ANGLE` y detener. No elegir un ángulo por default ni

inferir resolución entre turnos.

## Protocolo Figma Sync

Referencia: `CANON:OUTPUT-CONTRACT-001`. Los puntos siguientes son no

negociables.

### 1. Inmutabilidad de IDs

Los `###### figma_text_id` son llaves primarias. Está prohibido alterarlos,

omitarlos o inventar nuevas. El SSOT de IDs de nodo es `registry_seed.json`

(ubicación de referencia histórica: `04-Vantage_CV/Figma Sync/`; también

disponible vía Google Drive o adjunto directo del operador en el chat — leer

la copia más reciente disponible por cualquiera de estas vías, nunca asumir

que solo existe en la ruta local); ante discrepancia, el registry gana.

### 2. Integridad de slots

No se permiten fusiones ni divisiones de bloques. Si el Golden Skeleton tiene

cuatro bullets para una experiencia, el output debe conservar cuatro bloques,

incluso cuando uno quede vacío. Slot Integrity gobierna el conteo de bloques,

no limita a un solo hecho del Canon por slot.

### 3. Regla de llenado nulo

Si el Career Canon no ofrece información suficiente para un slot, conservar el

ID original y escribir un solo carácter espacio; nunca eliminar el slot, usar

`[PENDING DATA]` ni dejar un string vacío en el `.md` final. El slot en un solo

espacio solo se permite después de intentar Match Transferible Obligatorio y

fallar.

### 4. Escaping

El formato exacto del tag es: `###### figma_text_id` donde:

- `######` : exactamente 6 caracteres hash, sin espacios
- `[figma_text_id]` : literal "figma_text_id" entre corchetes
- `(N:N)` : el ID numérico del registry entre paréntesis
- **PROHIBIDO**: cualquier variación como `N:N`, `N:N|`, espacios

&#x20; adicionales, o caracteres especiales en el label

Replicar el escaping de `(` y `)` únicamente si el Golden Skeleton vigente lo

usa. Nunca normalizar ni modificar por preferencia.

### 5. Distinctiveness Rule

Cada bullet de Experience responde al Gap Analysis del HANDOFF activo

(`fit_gaps`, `JD_keywords_top6`), no a una plantilla fija por Positioning Mode.

### 6. Match Transferible Obligatorio

Antes de dejar un slot en un solo espacio, intentar reencuadrar un hecho

disponible del Career Canon bajo terminología relevante al JD activo, incluso

si no existe coincidencia literal con `JD_keywords_top6`. `[PENDING DATA]`

no se usa: el slot queda en un solo espacio únicamente cuando ningún hecho del

Canon, directo o reencuadrado, es transferible al eje temático de la vacante.

Anti-overselling gobierna por separado y tiene prioridad: no reencuadrar ni

sintetizar un hecho si afirma una responsabilidad que el JD contradice

activamente. Match Transferible no autoriza inventar ni elevar ownership.

- Válido: `coordiné ejecución visual 17 tiendas + 12 corners` →

&#x20; `coordinación de ejecución visual multi-punto de venta` para un JD regional.

- Inválido: `lideré 3 coordinadoras directas` reencuadrado para un JD

&#x20; individual contributor explícito.

Un reencuadre nunca puede subir el nivel de ownership del hecho original.

Verbos permitidos cuando corresponden al Canon: coordinar, supervisar, alinear,

colaborar con, dar seguimiento a. Verbos de ownership pleno — dirigir,

gestionar end-to-end, desarrollar desde concepto, poseer, liderar el

desarrollo de — solo se usan si existen literalmente en el Canon.

## Estructura Golden Skeleton

Referencia: `CANON:OUTPUT-CONTRACT-002`. Antes de generar cualquier output,

leer `registry_seed.json` vigente — desde el Career Canon en Notion

(`CANON:OUTPUT-CONTRACT-003` mantiene una copia embebida de referencia,

BASELINE 2026-09-19), Google Drive, o el adjunto más reciente que el operador

haya compartido en la sesión. Nunca usar una tabla de IDs memorizada o

hardcodeada en esta skill.

El registry mapea `slot_name` a `figma_text_id`; sus llaves ordenadas C01→C05

constituyen la referencia física de secuencia, además de la regla explícita en

`CANON:OUTPUT-CONTRACT-005`.

Si el registry no está disponible o no se puede leer, detener la generación y

solicitarlo al operador. No inventar ni asumir IDs.

## Densidad por síntesis multi-hecho — Regla de Elegibilidad de Etiqueta

Cuando el Canon contiene múltiples datos relacionados y transferibles para un

mismo slot, sintetizarlos en un bullet denso:

```
**[Etiqueta temática en bold]:** [Hecho 1 del Canon]; [Hecho 2 relacionado],
[Hecho 3 relacionado si aplica].
```

**Criterio de elegibilidad (v10.2.0, causa raíz del incidente 2026-09-05):** la

etiqueta temática en bold es una anotación de síntesis, no un titular

decorativo. Antes de escribir una, correr esta prueba binaria:

> ¿Este bullet combina 2 o más hechos del Canon que, sin la etiqueta, no se
> 

> leerían como pertenecientes a una misma categoría funcional?
> 
- **SÍ** → la etiqueta es elegible. Escribirla.
- **NO** (el bullet ya es un solo hecho, o los hechos combinados son

&#x20; obviamente parte de la misma acción sin necesitar un nombre de categoría) →

&#x20; **prohibido** escribir la etiqueta. El bullet va en prosa corrida desde la

&#x20; primera palabra, sin `**Título:**` al inicio.

Un batch entero con etiqueta en cada bullet de Experience es evidencia de que

la regla se aplicó como plantilla, no como síntesis genuina. Si más del 40% de

los bullets de Experience en un mismo CV-B llevan etiqueta, detener antes de

entregar y re-evaluar cada una contra la prueba binaria de arriba.

Reglas adicionales:

1. Cada hecho debe existir literalmente en el Canon; la síntesis combina datos

&#x20;  reales, nunca interpola relaciones no documentadas.

1. La etiqueta bold nombra la categoría funcional real del conjunto de

&#x20;  hechos — nunca repite como título lo que el primer verbo del bullet ya

&#x20;  dice.

1. Un slot puede contener un hecho aislado sin etiqueta si es el único dato

&#x20;  relevante — éste es el caso por defecto, no la excepción.

1. Un slot queda en un solo espacio únicamente tras intentar el Match

&#x20;  Transferible Obligatorio y documentar el fallo.

## Tiempo verbal por rol

Cada Experience Record (C01–C05) tiene una fecha de cierre en el Career Canon.

- **Rol con fecha de cierre en el pasado:** todos los verbos conjugados del

&#x20; bullet van en **pretérito** (dirigí, coordiné, definí, gestioné, construí,

&#x20; contribuí). Prohibido el presente narrativo (dirijo, coordino, defino,

&#x20; gestiono, colaboro) salvo que el verbo esté citando un hábito canónico

&#x20; intemporal explícitamente marcado como tal en el Canon (infrecuente — ante

&#x20; duda, usar pretérito).

- **Rol activo (sin fecha de cierre, o marcado como actual en el HANDOFF):**

&#x20; presente es válido y preferible para transmitir continuidad.

- Un CV-B con más de un rol nunca debe mezclar tiempos entre roles cerrados —

&#x20; todos los roles con fecha de cierre usan pretérito de forma uniforme.

## Contenido de skills

Los cinco slots de Skills deben mapear a las cinco categorías de

`CANON:SKILLS`:

- Estrategia Visual
- Operaciones y Finanzas
- Liderazgo y Training
- Stack Técnico
- Idiomas

Las cinco categorías requieren contenido antes de considerar completo el

CV-B. Match Transferible aplica también a estos slots. A diferencia de

Experience, en Skills la etiqueta de categoría en bold (`**Estrategia
Visual:**`) es siempre obligatoria — no está sujeta a la Regla de

Elegibilidad de Etiqueta de la sección anterior, porque aquí la categoría es

estructural del slot, no una síntesis opcional de contenido.

## Positioning Mode

Referencia: `CANON:OUTPUT-CONTRACT-005`. El Positioning Mode N1–N4 declarado

en el HANDOFF gobierna tagline, perfil, skills y el énfasis de los bullets de

Experience. No modifica el orden ni la existencia de slots: Experience

conserva siempre C01→C05.

No mezclar bullets de dos Positioning Modes en un mismo CV-B. El modo

determina énfasis y ángulo; la disponibilidad de contenido la determina Match

Transferible Obligatorio.

## Reglas de serialización y formato

Referencia: `CANON:OUTPUT-CONTRACT-004`.

| Elemento | Formato | Ejemplo |  |  |
| --- | --- | --- | --- | --- |
| Tag Figma | `###### figma_text_id` | ver sección Escaping |  |  |
| Nombre completo (header) | Bold | `**MAURICIO MEYRÁN**` |  |  |
| Tagline (subtítulo bajo nombre, `2:5`) | Bold, idioma = `HANDOFF.idioma`, separador de barra vertical (|) | `**Gerente de VM | Liderazgo Estratégico**` |  |  |
| Título de sección (PERFIL, HABILIDADES, EXPERIENCIA, FORMACIÓN, CURSOS) | Bold | `**EXPERIENCIA PROFESIONAL**` |  |  |
| Nombre de empresa (Experience) | Bold standalone, propio tag | `**L'ORÉAL LUXE MÉXICO**` |  |  |
| Rol (Experience) | Bold rol + italic período, mismo o distinto tag según Skeleton | `**Coordinador de VM** *02/2025 - 03/2026*` |  |  |
| Bullets de Experience | Prosa corrida sin bullets manuales (`•`/`-`/`*`); etiqueta bold SOLO si pasa la Regla de Elegibilidad | ver sección Densidad |  |  |
| Métricas y cifras cuantificadas (KPIs, %, headcount) | Bold siempre, en cada aparición dentro de un bullet | `**+43% tráfico**`, `**17 subgerentes**`, `**270+ puntos de venta**` |  |  |
| Categoría de Skills | Bold siempre (obligatorio, no sujeto a Regla de Elegibilidad) | `**Estrategia Visual:** Definición y...` |  |  |
| Título de grado académico (licenciatura, diplomado) | Bold | `**Licenciatura en Artes Visuales**` |  |  |
| Año o período de formación/certificación | Italic siempre | `*2008 - 2012*`, `*2014*` |  |  |
| Institución (formación/certificación) | Texto plano | `Facultad de Artes y Diseño, UNAM` |  |  |

Reglas generales adicionales:

- Cada tag es un párrafo independiente, sin listas ni bullets manuales al

&#x20; inicio.

- Bold de keywords estratégicos dentro de un bullet de Experience se reserva

&#x20; para: (a) las `JD_keywords_top6` del HANDOFF cuando aparecen literalmente

&#x20; reflejadas en el hecho narrado, y (b) toda métrica cuantificada (ver tabla).

&#x20; No se pone bold decorativo fuera de estos dos casos.

- Mantener `&` en nombres de empresa.
- Replicar exactamente el escaping que muestre el Golden Skeleton para cada

&#x20; slot.

## Política de idioma

- `HANDOFF.idioma = ES`: CV-B íntegramente en español, salvo nombres propios,

&#x20; software y títulos oficiales de certificación o institución. Esto incluye

&#x20; el tagline (`2:5`) y cualquier slot de perfil o Experience — sin excepción

&#x20; por herencia de una versión anterior del documento en otro idioma.

- `HANDOFF.idioma = EN`: CV-B íntegramente en inglés bajo el mismo criterio.
- Si el idioma del cuerpo no coincide con `HANDOFF.idioma`, declarar

&#x20; `STATUS=BLOCKED_LANGUAGE_MISMATCH` y no generar el archivo.

- Al reutilizar o adaptar contenido de un CV-B previo (mismo o distinto

&#x20; batch), el idioma se reconcilia slot por slot antes de la Auto-Verificación

&#x20; Mecánica — nunca se asume que un slot heredado ya está en el idioma

&#x20; correcto solo porque el resto del documento lo está.

## Lista de frases vacías (Gates 11a y 12)

Lista de trabajo para detectar relleno genérico. Aplica por idioma según

`HANDOFF.idioma`. La coincidencia ignora mayúsculas y acentos, y cubre género y

número (apasionado/a/os/as). Las listas de `vantage-cv-b` y `vantage-qa` son

**idénticas**: un cambio a una exige el mismo cambio en la otra, en el mismo

turno, hasta que exista un archivo de configuración compartido (decisión del

operador; no crear ubicaciones nuevas por iniciativa propia,

`CHARTER:NON-NEGOTIABLES-011`).

**ES:** apasionado por · pasión por · orientado a resultados · proactivo ·

dinámico · ayudo a · transformando · amplia experiencia · sólida experiencia ·

gran experiencia · historial probado · probada trayectoria · líder nato ·

visionario

**EN:** passionate about · passion for · results-driven · results-oriented ·

proactive · dynamic · I help · transforming · extensive experience · solid

experience · proven track record · team player · self-starter

Excepción de Canon (solo Gate 11a): una frase de la lista **no** es hit si

aparece literal en el Career Canon, en el idioma activo, dentro de

`CANON:PROFILE-001/002` o de los Experience Records `CANON:EXPERIENCE-001` a

`-005`. El Canon es la fuente de verdad y CV-B no lo corrige. El footer declara

cada exención usada (frase + ID de Canon). El Gate 12 no admite esta excepción.

Nota de calibración: "responsable de" no está en la lista porque aparece en

bullets ya aprobados en Figma (ejemplo Levi's/Dockers en esta misma skill). Es

un verbo funcional, no relleno; lo cubre la prueba de ancla del Gate 11b.

## Auto-Verificación Mecánica Obligatoria

Cada gate se corre como una comprobación de patrón sobre el texto ya generado —

nunca como un juicio recordado de lo que se pretendía escribir. El resultado de

cada gate debe basarse en evidencia extraíble del documento (equivalente a

correr `grep`/regex sobre el archivo), no en la memoria de redacción del turno

que generó el contenido.

Ningún gate puede declararse PASS sin haber sido ejecutado contra el texto

final. Un footer que diga "PASS" sin que el gate correspondiente se haya

corrido realmente es una violación de esta skill, equivalente en severidad a

un ID de Figma inventado.

**Dos niveles de resultado.** Un **FAIL** bloquea la entrega. Una **ALERTA** no

bloquea, pero se reporta en el footer con los `figma_text_id` exactos (Gate 5 y

Gate 11b).

### Gate 1 — Formato y membership de tags

Extraer el ID entre paréntesis `(N:N)` de cada tag; validar membership exacta

contra `registry_seed.json`. Rechazar IDs inexistentes, convenciones mixtas de

tag, o el placeholder literal `figma_text_id` sin ID real. Validar label

exacto `[figma_text_id]`, ausencia de caracteres especiales prohibidos, y

ausencia de espacios entre `######` y `[`.

### Gate 2 — Integridad estructural

Validar conteo, membership, unicidad y secuencia exacta contra el Golden

Skeleton.

### Gate 3 — Idioma

Escanear el cuerpo completo del documento (excluyendo nombres propios,

software e instituciones) contra una lista de palabras-función del idioma

opuesto a `HANDOFF.idioma` (para ES: "the", "and", "with", "for", "managed",

"ensuring", "leadership", "team", "of", "in" como conjunto mínimo). Cualquier

ocurrencia fuera de una excepción declarada es FAIL. Reportar el slot exacto

(`figma_text_id`) donde se detectó.

### Gate 4 — Tiempo verbal por rol

Para cada Experience Record con fecha de cierre en el pasado, escanear sus

bullets contra una lista de verbos en primera persona presente prohibidos

(defino, dirijo, coordino, colaboro, gestiono, lidero, desarrollo, construyo,

contribuyo, superviso, y sus variantes). Cualquier ocurrencia en un rol

cerrado es FAIL. El rol activo (sin fecha de cierre) queda exento.

### Gate 5 — Elegibilidad de etiquetas bold en Experience

Contar cuántos bullets de Experience inician con `**[Categoría]:**`. Si el

conteo supera el 40% del total de bullets de Experience, marcar ALERTA y

re-evaluar cada etiqueta contra la Regla de Elegibilidad antes de continuar — no se declara PASS del gate hasta confirmar que cada etiqueta remanente sintetiza 2+ hechos dispares.

### Gate 6 — Bold de métricas

Extraer todo patrón numérico con `%`, `+`, o seguido de una palabra de headcount/volumen (tiendas, reportes, países, puntos de venta, subgerentes, supervisores, corners) dentro de bullets de Experience o del párrafo de perfil. Confirmar que cada ocurrencia está envuelta en `**...**`. Cualquier cifra cuantificada sin bold es FAIL.

### Gate 7 — Formato estructural consolidado

Confirmar contra la tabla de la sección "Reglas de serialización y formato": título de sección en bold, nombre de empresa en bold, categoría de Skills en bold, título de grado académico en bold, año/período de formación en italic, tagline en bold, con separador `|` e idioma correcto. Cualquier discrepancia es FAIL con el `figma_text_id` exacto señalado.

### Gate 8 — Pendientes justificados y pregunta de cierre

Por cada slot que quede en un solo espacio, el footer debe declarar el hecho del Canon evaluado, el reencuadre intentado y la causa del fallo.

**Pregunta de cierre (v10.3.0):** por cada uno de esos slots, el footer añade una pregunta al operador, formulada como **pregunta de existencia** sobre un dato que cerraría el slot — por ejemplo, "¿Existe un dato de alcance para C03 que no esté en el Canon?". Nunca como sugerencia de contenido ni como texto propuesto. Si el operador responde que sí, el camino es `KERNEL:CANON-UPDATE`, no inventar. La pregunta va solo en el footer del chat, nunca dentro del `.md`, y no bloquea la entrega.

### Gate 9 — Cross-check de sesión y Anti-cloning

Si el mismo `figma_text_id` tuvo contenido válido en un CV-B previo de la misma sesión y ahora está en un solo espacio, tratarlo como alerta de probable omisión. Ningún bullet de Experience puede coincidir verbatim con un CV-B previo del mismo Positioning Mode en la sesión o batch.

### Gate 10 — Integridad de code fences

Si el footer de metadata incluye bloques de código, verificar que los delimitadores de triple backtick estén correctamente emparejados.

### Gate 11 — Relleno y ancla factual (v10.3.0)

**Alcance del escaneo:** tagline (`2:5`), párrafos de perfil (`2:9`, `3:13`, `2:10`) y bullets de Experience. Quedan fuera Skills, contacto, nombres de empresa, roles, períodos, formación y certificaciones.

**11a — Frases vacías (FAIL).** Buscar en el alcance cada frase de la "Lista de frases vacías" del idioma activo. Cada ocurrencia es FAIL con el `figma_text_id` y la frase exactos, salvo que aplique la excepción de Canon (ver la sección de la lista). El footer reporta el conteo de hits y las exenciones usadas.

**11b — Ancla y alcance (ALERTA, no FAIL).** No es FAIL porque varios bullets del Canon no llevan cifra ni nombre propio, y CV-B no puede inventar datos que el Canon no tiene.

- *Ancla:* toda oración de perfil y todo bullet de Experience debe contener al menos un dígito, o un nombre propio (marca, país, proyecto, herramienta o institución). Sin ancla → ALERTA con el `figma_text_id`.
- *Alcance:* todo bullet de Experience debe contener un dígito o una palabra de unidad de alcance (tiendas, países, puntos de venta, POS, reportes, proveedores, marcas, corners, subgerentes, supervisores, coordinadoras; EN: stores, countries, points of sale, POS, reports, vendors, brands, corners, assistant managers, supervisors, coordinators). Sin alcance → ALERTA.
- "Resultado" no se evalúa aquí: no es detectable con un patrón. Lo cubre QA.
- Ante una ALERTA, el bullet se re-evalúa contra el Canon. Solo se reescribe si el Canon aporta el dato faltante; si no, se conserva y se reporta.

### Gate 12 — Tagline (v10.3.0)

Sobre el tagline `2:5` (bold, separador `|`):

- **Longitud:** máximo 12 palabras, contando todos los tokens separados por espacios y excluyendo el separador `|` y símbolos sueltos. El tope de 12 es el valor inicial de v10.3.0. Si un tagline ya aprobado en Figma lo excede, no se cambia el tope por iniciativa propia: reportar al operador.
- **Palabras prohibidas:** ninguna de la "Lista de frases vacías". Sin excepción de Canon.
- **Sin emojis** (cualquier carácter del bloque Unicode Extended_Pictographic).

Cualquier incumplimiento es FAIL con el conteo y el `figma_text_id` (`2:5`).

### Reporte de gates en el footer

El footer de metadata debe listar los 12 gates con su resultado individual — no un "Verificación Pre-Entrega: PASS" genérico — más una línea final de alertas. Formato mínimo:

```
Gate 1 (Tags/Membership): PASS
Gate 2 (Integridad estructural): PASS
Gate 3 (Idioma): PASS
Gate 4 (Tiempo verbal): PASS
Gate 5 (Elegibilidad etiquetas): PASS — 2/24 bullets con etiqueta (8%)
Gate 6 (Bold de métricas): PASS
Gate 7 (Formato estructural): PASS
Gate 8 (Pendientes justificados): N/A — 0 ocurrencias
Gate 9 (Cross-check/Anti-cloning): PASS
Gate 10 (Code fences): PASS
Gate 11a (Frases vacías): PASS — 0 hits; exenciones: 1 (proven track record, CANON:PROFILE-002)
Gate 11b (Ancla/alcance): ALERTA — 2 slots: 2:36 (sin alcance), 2:51 (sin ancla)
Gate 12 (Tagline): PASS — 7 palabras
ALERTAS: 3 (Gate 11b: 2:36, 2:51; Gate 5: ninguna)
```

Un solo gate en FAIL bloquea la entrega — se corrige y se re-corren los 12 gates completos, no solo el que falló (una corrección puede romper un gate que antes pasaba). Una ALERTA no bloquea.

## Restricción de lote

CV-B procesa exactamente un HANDOFF por invocación. Si el operador entrega un batch, procesar solo el primero, completar su ciclo y detener hasta recibir una invocación separada para el siguiente.

## Nombre del archivo

Referencia: `KERNEL:NAM-OUTPUT`.

```
{YYYY}_{FirstName}_{LastName}_{Empresa}_{Rol}_CV-B.md
```

- `YYYY`: año de la sesión.
- `FirstName_LastName`: `Mauricio_Meyran`.
- `Empresa` y `Rol`: extraídos del HANDOFF y normalizados, con espacios convertidos a guiones bajos, sin acentos ni caracteres especiales.
- `CV-B`: fase fija.

Ejemplo: `2026_Mauricio_Meyran_Dior_VM_Trade_Coordinator_CV-B.md`.

Si falta empresa o rol, detener y solicitarlo; no usar placeholders.

## Entrega

Generar un único archivo `.md` descargable mediante `create_file`. No renderizar el Markdown del CV en chat ni pedir confirmación adicional para crear el artefacto.

El footer de metadata NUNCA va dentro del `.md` importable. Se entrega solo en el chat, con:

- Versión del Output Contract y de este skill.
- Positioning Mode activo.
- Referencia canónica al Canon usado.
- Reporte de los 12 gates y la línea de ALERTAS (ver sección Auto-Verificación Mecánica).
- Justificación y pregunta de cierre de cada slot en un solo espacio, si existe.

Después de crear el archivo, releerlo y verificar la codificación de caracteres acentuados y `ñ`. Si hay corrupción, no entregar; reportar el error antes de reintentar.

**Verificación post-generación adicional:**

1. Confirmar que no existen tags con formato incorrecto.
2. Verificar que no hay caracteres especiales prohibidos en los labels.
3. Validar la integridad de los code fences en el footer de metadata.
4. Ejecutar un diff final contra el Golden Skeleton para asegurar que solo cambió el contenido, no la estructura.
5. Ejecutar `verify_md.py` sobre el `.md`; 0 issues obligatorio antes de presentar. Los Gates 11 y 12 los ejecuta CV-B sobre el texto; no se declaran "verificados por script" mientras `verify_md.py` no los implemente.