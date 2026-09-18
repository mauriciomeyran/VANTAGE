---
name: vantage-cv-b
description: Fase 2 del pipeline de CV de VANTAGE (KERNEL:CV-PIPELINE-002) — construye el CV final aplicando el Output Contract Framework para integración directa con Figma, a partir de un HANDOFF generado por vantage-cv-a. Usar cuando el operador invoque el trigger "CV-B [HANDOFF]", pegue o adjunte un HANDOFF de CV-A y pida construir el CV, o pida generar el Markdown con Figma Tags para una vacante ya analizada. También activar si el operador pide "serializar" un CV para Figma o menciona figma_text_id, Golden Skeleton o Figma Sync Protocol. No usar sin un HANDOFF previo de vantage-cv-a — si no existe, redirigir primero a esa skill. No usar para el análisis inicial de la vacante (eso es vantage-cv-a) ni para la auditoría final del PDF (eso es vantage-qa).
---

# VANTAGE — Skill CV-B (Construcción y Contrato de Salida)

ID Canónico: `KERNEL:CV-PIPELINE-002` · Trigger: `CV-B [HANDOFF]`
Versión de alineación: v10.2.0 — Auto-Verificación Mecánica Obligatoria (2026-09-05)

## Nota de refactor (por qué existe esta versión)

v10.1.1 confiaba la Verificación Pre-Entrega al mismo turno que generaba el
contenido — el agente redactaba y auditaba en el mismo aliento, y declaraba
`PASS` en el footer sin correr un chequeo real contra el texto ya escrito.
Batch de septiembre 2026 (CV-B "Confidencial VM Manager"): 8 rondas de
corrección post-entrega detectadas por el operador, ninguna capturada por la
Verificación Pre-Entrega v10.1.1 pese a que el skill ya prohibía explícitamente
la mayoría de los fallos (idioma mixto, política de serialización, síntesis
multi-hecho). El fallo no fue de especificación — fue de **auditoría
autodeclarada sin evidencia mecánica**.

Este refactor no agrega reglas de estilo nuevas al contenido; convierte la
Verificación Pre-Entrega de un checklist narrado a un conjunto de gates
mecánicos con criterio de PASS/FAIL basado en patrón detectable sobre el
texto ya generado — el mismo método que ya gobierna la Auditoría de Identidad
(conteo/membership/secuencia), extendido a estilo, idioma y tiempo verbal.

## Responsabilidad

Segunda fase del pipeline de CV. Toma el HANDOFF de `vantage-cv-a` y construye
el CV final serializado en Markdown con Figma Tags, listo para sincronizar con
el archivo Figma vía el Output Contract Framework (`CANON:OUTPUT-CONTRACT`).

## Invariante de sesión

**Cero prosa en el chat.** Esta skill no conversa sobre la construcción del CV
en el cuerpo del mensaje. El único output permitido es un archivo `.md`
descargable que contenga el CV completo. Cualquier explicación, aclaración o
duda va dentro del propio archivo, no como texto de chat adicional.

Excepción: si el HANDOFF está incompleto, el Positioning Mode no está resuelto,
o un Gate de Auto-Verificación Mecánica falla y requiere input humano, se puede
preguntar al operador. Una vez resuelto, el resultado sigue siendo solo el
archivo.

## Fuera de scope

Esta skill entrega **Markdown con figma_text_id**. Cómo el plugin de Figma
consume, parsea o transforma ese Markdown está fuera del scope de CV-B y no se
especula sobre ello.

- Ante una falla de render en Figma, declarar: `Fuera de scope de CV-B —
  necesito ver el script/plugin fuente real antes de diagnosticar.`
- El formato exacto del tag (`###### [figma_text_id](2:4)`, con corchetes y
  sin escapar `#`) sí está dentro de scope: se copia carácter por carácter
  desde el Golden Skeleton vigente, nunca se reconstruye de memoria.

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
omitirlos o inventar nuevos. El SSOT de IDs de nodo es `registry_seed.json` en
`04-Vantage_CV/Figma Sync/`; ante discrepancia, el registry gana.

### 2. Integridad de slots

No se permiten fusiones ni divisiones de bloques. Si el Golden Skeleton tiene
cuatro bullets para una experiencia, el output debe conservar cuatro bloques,
incluso cuando uno quede vacío. Slot Integrity gobierna el conteo de bloques,
no limita a un solo hecho del Canon por slot.

### 3. Regla de llenado nulo

Si el Career Canon no ofrece información suficiente para un slot, conservar el
ID original y usar `[PENDING DATA]` o dejar el contenido vacío; nunca eliminar
el slot. `[PENDING DATA]` solo es válido después de intentar Match Transferible
Obligatorio y fallar.

### 4. Escaping

El formato exacto del tag es: `###### [figma_text_id](N:N)` donde:
- `######` : exactamente 6 caracteres hash, sin espacios
- `[figma_text_id]` : literal "figma_text_id" entre corchetes
- `(N:N)` : el ID numérico del registry entre paréntesis
- **PROHIBIDO**: cualquier variación como `[N:N](N:N)`, `[N:N|](N:N)`, espacios
  adicionales, o caracteres especiales en el label

Replicar el escaping de `(` y `)` únicamente si el Golden Skeleton vigente lo
usa. Nunca normalizar ni modificar por preferencia.

### 5. Distinctiveness Rule

Cada bullet de Experience responde al Gap Analysis del HANDOFF activo
(`fit_gaps`, `JD_keywords_top6`), no a una plantilla fija por Positioning Mode.

### 6. Match Transferible Obligatorio

Antes de marcar un slot como `[PENDING DATA]`, intentar reencuadrar un hecho
disponible del Career Canon bajo terminología relevante al JD activo, incluso
si no existe coincidencia literal con `JD_keywords_top6`. `[PENDING DATA]`
solo aplica cuando ningún hecho del Canon, directo o reencuadrado, es
transferible al eje temático de la vacante.

Anti-overselling gobierna por separado y tiene prioridad: no reencuadrar ni
sintetizar un hecho si afirma una responsabilidad que el JD contradice
activamente. Match Transferible no autoriza inventar ni elevar ownership.

- Válido: `coordiné ejecución visual 17 tiendas + 12 corners` →
  `coordinación de ejecución visual multi-punto de venta` para un JD regional.
- Inválido: `lideré 3 coordinadoras directas` reencuadrado para un JD
  individual contributor explícito.

Un reencuadre nunca puede subir el nivel de ownership del hecho original.
Verbos permitidos cuando corresponden al Canon: coordinar, supervisar, alinear,
colaborar con, dar seguimiento a. Verbos de ownership pleno — dirigir,
gestionar end-to-end, desarrollar desde concepto, poseer, liderar el
desarrollo de — solo se usan si existen literalmente en el Canon.

## Estructura Golden Skeleton

Referencia: `CANON:OUTPUT-CONTRACT-002`. Antes de generar cualquier output,
leer `registry_seed.json` vigente. Nunca usar una tabla de IDs memorizada o
hardcodeada en esta skill.

El registry mapea `slot_name` a `figma_text_id`; sus llaves ordenadas C01→C05
constituyen la referencia física de secuencia, además de la regla explícita en
`CANON:OUTPUT-CONTRACT-005`.

Si el registry no está disponible o no se puede leer, detener la generación y
solicitarlo al operador. No inventar ni asumir IDs.

## Densidad por síntesis multi-hecho — Regla de Elegibilidad de Etiqueta

Cuando el Canon contiene múltiples datos relacionados y transferibles para un
mismo slot, sintetizarlos en un bullet denso:

```text
**[Etiqueta temática en bold]:** [Hecho 1 del Canon]; [Hecho 2 relacionado],
[Hecho 3 relacionado si aplica].
```

**Criterio de elegibilidad — nuevo, v10.2.0 (causa raíz del incidente
2026-09-05):** la etiqueta temática en bold es una anotación de síntesis, no
un titular decorativo. Antes de escribir una, correr esta prueba binaria:

> ¿Este bullet combina 2 o más hechos del Canon que, sin la etiqueta, no se
> leerían como pertenecientes a una misma categoría funcional?

- **SÍ** → la etiqueta es elegible. Escribirla.
- **NO** (el bullet ya es un solo hecho, o los hechos combinados son
  obviamente parte de la misma acción sin necesitar un nombre de categoría) →
  **prohibido** escribir la etiqueta. El bullet va en prosa corrida desde la
  primera palabra, sin `**Título:**` al inicio.

Un batch entero con etiqueta en cada bullet de Experience es evidencia de que
la regla se aplicó como plantilla, no como síntesis genuina — eso es
exactamente el patrón que este refactor corrige. Si más del 40% de los
bullets de Experience en un mismo CV-B llevan etiqueta, detener antes de
entregar y re-evaluar cada una contra la prueba binaria de arriba.

Reglas adicionales:
1. Cada hecho debe existir literalmente en el Canon; la síntesis combina datos
   reales, nunca interpola relaciones no documentadas.
2. La etiqueta bold nombra la categoría funcional real del conjunto de
   hechos — nunca repite como título lo que el primer verbo del bullet ya
   dice.
3. Un slot puede contener un hecho aislado sin etiqueta si es el único dato
   relevante — éste es el caso por defecto, no la excepción.
4. `[PENDING DATA]` solo aplica tras intentar el Match Transferible
   Obligatorio y documentar el fallo.

## Tiempo verbal por rol — nuevo, v10.2.0

Cada Experience Record (C01–C05) tiene una fecha de cierre en el Career Canon.

- **Rol con fecha de cierre en el pasado:** todos los verbos conjugados del
  bullet van en **pretérito** (dirigí, coordiné, definí, gestioné, construí,
  contribuí). Prohibido el presente narrativo (dirijo, coordino, defino,
  gestiono, colaboro) salvo que el verbo esté citando un hábito canónico
  intemporal explícitamente marcado como tal en el Canon (infrecuente — ante
  duda, usar pretérito).
- **Rol activo (sin fecha de cierre, o marcado como actual en el HANDOFF):**
  presente es válido y preferible para transmitir continuidad.
- Un CV-B con más de un rol nunca debe mezclar tiempos entre roles cerrados —
  todos los roles con fecha de cierre usan pretérito de forma uniforme.

## Contenido de skills

Los cinco slots de Skills deben mapear a las cinco categorías de
`CANON:SKILLS`:

- Estrategia Visual
- Operaciones & Finanzas
- Liderazgo & Training
- Stack Técnico
- Idiomas

Las cinco categorías requieren contenido antes de considerar completo el
CV-B. Match Transferible aplica también a estos slots. **A diferencia de
Experience, en Skills la etiqueta de categoría en bold (`**Estrategia
Visual:**`) es siempre obligatoria** — no está sujeta a la Regla de
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

## Reglas de serialización y formato — consolidado, v10.2.0

Referencia: `CANON:OUTPUT-CONTRACT-004`.

| Elemento | Formato | Ejemplo |
|---|---|---|
| Tag Figma | `###### [figma_text_id](N:N)` | ver sección Escaping |
| Nombre completo (header) | Bold | `**MAURICIO MEYRÁN**` |
| Tagline (subtítulo bajo nombre) | Bold, idioma = `HANDOFF.idioma` | `**Gerente de VM · Liderazgo Estratégico**` |
| Título de sección (PERFIL, HABILIDADES, EXPERIENCIA, FORMACIÓN, CURSOS) | Bold | `**EXPERIENCIA PROFESIONAL**` |
| Nombre de empresa (Experience) | Bold standalone, propio tag | `**L'ORÉAL LUXE MÉXICO**` |
| Rol (Experience) | Bold rol + italic período, mismo o distinto tag según Skeleton | `**Coordinador de VM** *02/2025 - 03/2026*` |
| Bullets de Experience | Prosa corrida sin bullets manuales (`•`/`-`/`*`); etiqueta bold SOLO si pasa la Regla de Elegibilidad | ver sección Densidad |
| Métricas y cifras cuantificadas (KPIs, %, headcount) | Bold siempre, en cada aparición dentro de un bullet | `**+43% tráfico**`, `**17 subgerentes**`, `**270+ puntos de venta**` |
| Categoría de Skills | Bold siempre (obligatorio, no sujeto a Regla de Elegibilidad) | `**Estrategia Visual:** Definición y...` |
| Título de grado académico (licenciatura, diplomado) | Bold | `**Licenciatura en Artes Visuales**` |
| Año o período de formación/certificación | Italic siempre | `*2008 - 2012*`, `*2014*` |
| Institución (formación/certificación) | Texto plano | `Facultad de Artes y Diseño, UNAM` |

Reglas generales adicionales:
- Cada tag es un párrafo independiente, sin listas ni bullets manuales al
  inicio.
- Bold de keywords estratégicos dentro de un bullet de Experience se reserva
  para: (a) las `JD_keywords_top6` del HANDOFF cuando aparecen literalmente
  reflejadas en el hecho narrado, y (b) toda métrica cuantificada (ver tabla).
  No se pone bold decorativo fuera de estos dos casos.
- Mantener `&` en nombres de empresa.
- Replicar exactamente el escaping que muestre el Golden Skeleton para cada
  slot.

## Política de idioma

- `HANDOFF.idioma = ES`: CV-B íntegramente en español, salvo nombres propios,
  software y títulos oficiales de certificación o institución. Esto incluye
  el tagline (`2:5`) y cualquier slot de perfil o Experience — sin excepción
  por herencia de una versión anterior del documento en otro idioma.
- `HANDOFF.idioma = EN`: CV-B íntegramente en inglés bajo el mismo criterio.
- Si el idioma del cuerpo no coincide con `HANDOFF.idioma`, declarar
  `STATUS=BLOCKED_LANGUAGE_MISMATCH` y no generar el archivo.
- Al reutilizar o adaptar contenido de un CV-B previo (mismo o distinto
  batch), el idioma se reconcilia slot por slot antes de la Auto-Verificación
  Mecánica — nunca se asume que un slot heredado ya está en el idioma
  correcto solo porque el resto del documento lo está.

## Auto-Verificación Mecánica Obligatoria — nuevo, v10.2.0

Esta sección reemplaza la "Verificación Pre-Entrega" narrada de v10.1.1. Cada
gate se corre como una comprobación de patrón sobre el texto ya generado —
nunca como un juicio recordado de lo que se pretendía escribir. El resultado
de cada gate debe basarse en evidencia extraíble del documento (equivalente a
correr `grep`/regex sobre el archivo), no en la memoria de redacción del
turno que generó el contenido.

**Ningún gate puede declararse PASS sin haber sido ejecutado contra el texto
final.** Un footer que diga "PASS" sin que el gate correspondiente se haya
corrido realmente es una violación de esta skill, equivalente en severidad a
un ID de Figma inventado.

### Gate 1 — Formato y membership de tags (heredado de v10.1.1)
Extraer el ID entre paréntesis `(N:N)` de cada tag; validar membership exacta
contra `registry_seed.json`. Rechazar IDs inexistentes, convenciones mixtas de
tag, o el placeholder literal `figma_text_id` sin ID real. Validar label
exacto `[figma_text_id]`, ausencia de caracteres especiales prohibidos, y
ausencia de espacios entre `######` y `[`.

### Gate 2 — Integridad estructural (heredado de v10.1.1)
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
re-evaluar cada etiqueta contra la Regla de Elegibilidad antes de continuar —
no se declara PASS del gate hasta confirmar que cada etiqueta remanente
sintetiza 2+ hechos dispares.

### Gate 6 — Bold de métricas
Extraer todo patrón numérico con `%`, `+`, o seguido de una palabra de
headcount/volumen (tiendas, reportes, países, puntos de venta, subgerentes,
supervisores, corners) dentro de bullets de Experience o del párrafo de
perfil. Confirmar que cada ocurrencia está envuelta en `**...**`. Cualquier
cifra cuantificada sin bold es FAIL.

### Gate 7 — Formato estructural consolidado
Confirmar contra la tabla de la sección "Reglas de serialización y formato":
título de sección en bold, nombre de empresa en bold, categoría de Skills en
bold, título de grado académico en bold, año/período de formación en italic,
tagline en bold e idioma correcto. Cualquier discrepancia es FAIL con el
`figma_text_id` exacto señalado.

### Gate 8 — Pendientes justificados (heredado de v10.1.1)
Por cada `[PENDING DATA]`, el footer debe declarar el hecho del Canon
evaluado, el reencuadre intentado y la causa del fallo.

### Gate 9 — Cross-check de sesión y Anti-cloning (heredado de v10.1.1)
Si el mismo `figma_text_id` tuvo contenido válido en un CV-B previo de la
misma sesión y ahora está en `[PENDING DATA]`, tratarlo como alerta de
probable omisión. Ningún bullet de Experience puede coincidir verbatim con un
CV-B previo del mismo Positioning Mode en la sesión o batch.

### Gate 10 — Integridad de code fences (heredado de v10.1.1)
Si el footer de metadata incluye bloques de código, verificar que los
delimitadores ``` estén correctamente emparejados.

### Reporte de gates en el footer

El footer de metadata debe listar los 10 gates con su resultado individual —
no un "Verificación Pre-Entrega: PASS" genérico. Formato mínimo:

```text
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
```

Un solo gate en FAIL bloquea la entrega — se corrige y se re-corren los 10
gates completos, no solo el que falló (una corrección puede romper un gate
que antes pasaba).

## Restricción de lote

CV-B procesa exactamente un HANDOFF por invocación. Si el operador entrega un
batch, procesar solo el primero, completar su ciclo y detener hasta recibir
una invocación separada para el siguiente.

## Nombre del archivo

Referencia: `KERNEL:NAMING-CONVENTION`.

```text
{YYYY}_{FirstName}_{LastName}_{Empresa}_{Rol}_CV-B.md
```

- `YYYY`: año de la sesión.
- `FirstName_LastName`: `Mauricio_Meyran`.
- `Empresa` y `Rol`: extraídos del HANDOFF y normalizados, con espacios
  convertidos a guiones bajos, sin acentos ni caracteres especiales.
- `CV-B`: fase fija.

Ejemplo: `2026_Mauricio_Meyran_Dior_VM_Trade_Coordinator_CV-B.md`.

Si falta empresa o rol, detener y solicitarlo; no usar placeholders.

## Entrega

Generar un único archivo `.md` descargable mediante `create_file`. No
renderizar el Markdown del CV en chat ni pedir confirmación adicional para
crear el artefacto.

El archivo debe incluir un footer de metadata con:

- Versión del Output Contract y de este skill.
- Positioning Mode activo.
- Referencia canónica al Canon usado.
- Reporte de los 10 gates (ver sección Auto-Verificación Mecánica).
- Justificación de cada `[PENDING DATA]`, si existe.

Después de crear el archivo, releerlo y verificar la codificación de
caracteres acentuados y `ñ`. Si hay corrupción, no entregar; reportar el error
antes de reintentar.

**Verificación post-generación adicional:**
1. Confirmar que no existen tags con formato incorrecto.
2. Verificar que no hay caracteres especiales prohibidos en los labels.
3. Validar la integridad de los code fences en el footer de metadata.
4. Ejecutar un diff final contra el Golden Skeleton para asegurar que solo
   cambió el contenido, no la estructura.