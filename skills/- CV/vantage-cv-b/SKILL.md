---
name: vantage-cv-b
description: Fase 2 del pipeline de CV de VANTAGE (KERNEL:CV-PIPELINE-002) — construye el CV final aplicando el Output Contract Framework para integración directa con Figma, a partir de un HANDOFF generado por vantage-cv-a. Usar cuando el operador invoque el trigger "CV-B [HANDOFF]", pegue o adjunte un HANDOFF de CV-A y pida construir el CV, o pida generar el Markdown con Figma Tags para una vacante ya analizada. También activar si el operador pide "serializar" un CV para Figma o menciona figma_text_id, Golden Skeleton, o Figma Sync Protocol. No usar sin un HANDOFF previo de vantage-cv-a — si no existe, redirigir primero a esa skill. No usar para el análisis inicial de la vacante (eso es vantage-cv-a) ni para la auditoría final del PDF (eso es vantage-qa).
---

# VANTAGE — Skill CV-B (Construcción y Contrato de Salida)

ID Canónico: `KERNEL:CV-PIPELINE-002` · Trigger: `CV-B [HANDOFF]`
Versión de alineación: v10.1.0 — **SANDBOX-ONLY REFACTOR** (2026-09-03)

## Nota de refactor (por qué existe esta versión)

Las versiones v9.16–v9.17 acumularon 3 parches reactivos, cada uno corrigiendo un
síntoma aislado sin modelo unificado:
1. v9.16 — Anti-cloning Guard (síntoma: bullets duplicados entre vacantes)
2. v9.17 — Fuera de Scope + Verificación Pre-Entrega (síntoma: especulación sobre
   plugin Figma; bullets manuales y `[PENDING DATA]` sin evidencia)
3. Hallazgo de sesión 2026-08-21 — comparación de batch real (Zegna, Walmart,
   Dior, LaPieza vs. Servicios Andrei/Moygo, mismo batch): la Verificación
   Pre-Entrega v9.17.0 exige justificar cada `[PENDING DATA]` con evidencia de
   búsqueda, pero no exige *intentar* llenar el slot primero — el resultado
   observado fue `[PENDING DATA]` como opción "segura y auditable" en vacantes
   con match no-literal, mientras que en el mismo batch (Andrei/Moygo, N2) el
   modelo sí reencuadró todo el Canon sin excepción, llegando a 24/24 slots.

Los síntomas comparten causa raíz: **el skill nunca tuvo un modelo explícito
de "cuánto contenido incluir" NI de "cuándo un hecho no-literal cuenta como
transferible"**. Este refactor reemplaza los parches reactivos por dos reglas
unificadas, ambas ya ratificadas en `CANON:OUTPUT-CONTRACT-001` (puntos 5 y 6):
Síntesis Multi-Hecho (densidad por slot) y Match Transferible Obligatorio
(cuándo un slot puede tener contenido).

v10.1.0 añade el modo sandbox-only: todo el procesamiento corre internamente
y el único output es el archivo `.md` descargable, sin render intermedio en chat.

## Responsabilidad

Segunda fase del pipeline de CV. Toma el HANDOFF de `vantage-cv-a` y construye
el CV final serializado en Markdown con Figma Tags, listo para sincronizar con
el archivo Figma vía el Output Contract Framework (`CANON:OUTPUT-CONTRACT`).

## Invariante de Sesión — Sandbox-only

**Cero prosa en el chat.** Esta skill no conversa sobre la construcción del CV
en el cuerpo del mensaje. El único output permitido es un archivo `.md`
descargable que contenga el CV completo. Cualquier explicación, aclaración o
duda va dentro del propio archivo, no como texto de chat adicional.

Excepción: si el HANDOFF está incompleto, el Positioning Mode no está resuelto,
o la Verificación Pre-Entrega detecta un bloqueo que requiere input humano, sí se
puede preguntar al operador — pero una vez resuelto, el resultado sigue siendo
solo el archivo.

## Fuera de Scope — Explícito

Esta skill entrega **Markdown con figma_text_id**. Cómo el plugin de Figma
consume, parsea o transforma ese Markdown (JSON intermedio, `boldRanges`,
regex de parser, `ui.html`, o cualquier script de conversión downstream) es
un componente fuera del scope de esta skill y no está documentado aquí.

- Si el operador pregunta sobre esto, o hay una falla de render en Figma:
  declarar el límite ("Fuera de scope de CV-B — necesito ver el script/plugin
  fuente real antes de diagnosticar") y no especular.
- El **formato exacto del tag** (`###### [figma_text_id](2:4)`, con corchetes,
  sin escapar el `#`) SÍ está dentro de scope — se copia carácter por
  carácter desde el Golden Skeleton vigente en Notion, nunca se reconstruye
  de memoria. Cualquier desviación de este formato es una regresión, no una
  mejora — no se introduce sin confirmar contra la fuente Notion en la misma
  sesión.

## Input requerido

HANDOFF completo generado por `vantage-cv-a`, incluyendo:
- Positioning Mode seleccionado (no procesar si el HANDOFF reporta "EMPATE — requiere decisión humana" sin resolución)
- Gap Analysis (matches directos, parciales, gaps)
- Validación de exclusiones ya en PASA

Si el HANDOFF está incompleto o el Positioning Mode no está resuelto, detener y solicitar al operador que complete CV-A primero.

## Protocolo de Sincronización — FIGMA SYNC PROTOCOL (STRICT)

Referencia: `CANON:OUTPUT-CONTRACT-001`. Los seis puntos son no-negociables:

### 1. Inmutabilidad de IDs (`figma_text_id`)
Los `###### figma_text_id` son llaves primarias. **Terminantemente prohibido** alterarlas, omitirlas o inventar nuevas. El SSOT de IDs de nodo es `registry_seed.json` en `04-Vantage_CV/Figma Sync/`. Si hay discrepancia, **el registry gana**.

### 2. Integridad de Slots
No se permiten fusiones ni divisiones de bloques. Si el Golden Skeleton tiene 4 bullets para una experiencia, el output DEBE tener 4 bloques, incluso si uno queda vacío. Slot Integrity gobierna **conteo de bloques**, no densidad de contenido dentro de cada bloque — no limita a un solo hecho del Canon por slot (ver Densidad por Síntesis Multi-Hecho, abajo).

### 3. Regla de llenado nulo
Si el Career Canon no tiene información suficiente para un slot específico, el slot se mantiene con su ID original y el texto `[PENDING DATA]`, o queda vacío — pero **nunca se elimina**. Esta regla ahora se subordina a la regla 6 (Match Transferible Obligatorio, abajo): `[PENDING DATA]` es el resultado de haber *intentado* reencuadrar y fallado, no un default por ausencia de match literal.

### 4. Markdown Escaping
Mantener el escaping de `(` y `)` para compatibilidad con el plugin de Figma si el Skeleton original lo usa.

### 5. Distinctiveness Rule
El lenguaje de cada bullet de Experience responde al Gap Analysis específico del HANDOFF activo (`fit_gaps`, `JD_keywords_top6`), no a una plantilla fija por Positioning Mode.

### 6. Match Transferible Obligatorio (v10.0.0 — `CANON:OUTPUT-CONTRACT-001` punto 6)
Antes de marcar un slot como `[PENDING DATA]`, **intentar reencuadrar** un hecho disponible del Career Canon bajo terminología relevante al JD activo, aunque no exista coincidencia literal con `JD_keywords_top6`. `[PENDING DATA]` solo aplica cuando ningún hecho del Canon, ni siquiera reencuadrado, es transferible al eje temático de la vacante (ej. un JD 100% ajeno a disciplina VM, como Data Analytics/Space Planning digital sin ningún paralelo de ejecución visual).

**Anti-overselling sigue gobernando por separado y tiene prioridad:** un hecho no se reencuadra ni se sintetiza si afirma una responsabilidad que el JD contradice activamente (ej. liderazgo de equipo en un JD individual contributor explícito). Match Transferible no es licencia para sobrevender — es licencia para expresar un hecho real bajo otro ángulo.

**Ejemplos de referencia** (`CANON:OUTPUT-CONTRACT-001`):
- Válido: "coordiné ejecución visual 17 tiendas + 12 corners" (C05) → "coordinación de ejecución visual multi-punto de venta" para un JD regional sin mención literal de Palacio de Hierro.
- Inválido: "lideré 3 coordinadoras directas" (C03) reencuadrado de cualquier forma para un JD individual contributor explícito — Anti-overselling bloquea independientemente del reencuadre.

**Este es el comportamiento default**, no una excepción condicionada a Score, Tier o Positioning Mode. Ante duda genuina sobre si un hecho es transferible o constituye overselling, declarar el criterio aplicado en el footer (ver Verificación Pre-Entrega, punto 2) en vez de omitir por defecto.

## Estructura — Golden Skeleton

Referencia: `CANON:OUTPUT-CONTRACT-002`. El SSOT de IDs de nodo es `registry_seed.json`
en `04-Vantage_CV/Figma Sync/`. **Obligatorio: leer este archivo antes de generar
cualquier output** — nunca usar una tabla de IDs memorizada o hardcodeada en este
skill.

El registry mapea `slot_name` → `figma_text_id`. Las llaves ya están ordenadas
C01→C05 — ese orden es la referencia física de secuencia, además de la regla
explícita en `CANON:OUTPUT-CONTRACT-005`.

Si el registry no está disponible o no se puede leer, detener la generación y
solicitar el archivo al operador — no inventar ni asumir IDs.

## Densidad por Síntesis Multi-Hecho

**Técnica confirmada** (validada contra siete CV-B previos ya aprobados en
Figma: Dolce & Gabbana, Nike NSW, Montblanc, Liverpool, La Europea,
Confidencial Retail Lead, Cartier — y contra Servicios Andrei/Moygo N2 en el
batch más reciente, único CV-B del batch con 0 `[PENDING DATA]`):

```
**[Etiqueta temática en bold]:** [Hecho 1 del Canon]; [Hecho 2 relacionado],
[Hecho 3 relacionado si aplica].
```

Ejemplo real (Levi's/Dockers, aprobado en Figma):
> **Gestión de red mixta:** Responsable del estándar visual en 22 puntos de
> venta en México (10 O&O, 6 comisionadas, 6 franquicias) y supervisión
> estratégica en 6 países de LATAM; lideré 3 coordinadoras con reporte
> directo y 3 con línea punteada.

Este es **comportamiento default**: cuando el Canon tiene múltiples datos
 disponidos y relacionados (directos o transferibles vía la regla 6) para el
slot de una compañía, se sintetizan en un solo bullet denso bajo una
etiqueta temática — en vez de repartirlos en fragmentos separados o dejarlos
fuera.

### Regla de síntesis
1. Cada hecho incluido debe existir literalmente en el Canon — la síntesis
   combina datos reales, nunca interpola ni infiere conexiones no
   documentadas.
2. La etiqueta bold nombra la categoría funcional real del conjunto de
   hechos que sigue.
3. Un slot puede quedarse con un solo hecho (sin etiqueta, prosa simple) si
   el Canon solo tiene un dato relevante y aislado — la síntesis no se
   fuerza rellenando con contenido de bajo valor.
4. `[PENDING DATA]` aplica solo tras aplicar la regla 6 (Match Transferible
   Obligatorio) y confirmar que no hay ningún hecho, ni directo ni
   reencuadrado, utilizable.

## Contenido de Skills — Mapeo Obligatorio

Los 5 slots de Skills deben mapear a las 5 categorías de `CANON:SKILLS`:
Estrategia Visual, Operaciones & Finanzas, Liderazgo & Training, Stack
Técnico, Idiomas. Las 5 categorías deben tener contenido antes de considerar
el CV-B completo — la regla 6 (Match Transferible) aplica igual aquí.

## Aplicación del Positioning Mode en el output

Referencia: `CANON:OUTPUT-CONTRACT-005`. Slots variables según el modo activo
(N1–N4) declarado en el HANDOFF: tagline (`2:5`), párrafos de perfil, skills,
y densidad/énfasis de bullets de Experience — priorizados según el modo, pero
**Experience conserva siempre la secuencia C01–C05, sin excepción**. El
Positioning Mode determina *énfasis y ángulo*, no si un slot recibe
contenido — esa decisión la gobierna la regla 6, aplicada uniformemente
independientemente del modo activo.

**No mezclar bullets de dos Positioning Modes distintos en un mismo CV-B.**

## Reglas de Serialización

Referencia: `CANON:OUTPUT-CONTRACT-004`.

- Cada tag = párrafo independiente (sin listas, sin guiones, sin bullets
  manuales `•`/`-`/`*` al inicio de párrafo)
- Bold = keywords estratégicos dentro del párrafo
- Empresa = bold standalone en su propio tag
- Rol = **bold rol** *italic período*
- Skills = `Categoría: texto plano`
- Tagline = `[Título · Subtítulo] · Ciudad | Tel | Email | LinkedIn | Portfolio`
- `&` en nombres de empresa se mantiene como `&`
- Escaping de paréntesis en texto: replicar exactamente lo que muestre el
  Golden Skeleton vigente para ese slot

## Verificación Pre-Entrega — Obligatoria (Sandbox)

Esta verificación corre internamente en sandbox antes de la escritura del
archivo. No se presenta como output intermedio en chat.

Antes de escribir el `.md`, correr y no proceder si falla:

1. **Formato de tag:** extraer el ID **entre paréntesis** `(N:N)` de cada
   línea de tag vía regex, ignorando el contenido del label entre corchetes.
   Verificar membresía exacta de ese ID en `registry_seed.json`. Rechazar
   si: (a) el ID entre paréntesis no existe en el registry, (b) hay más de
   una convención de tag distinta en el mismo archivo o batch, o (c) el
   label es el placeholder literal `figma_text_id` sin ID real ni
   corchetes — eso sí es bloqueante (bug de plantilla, no cosmético). El
   contenido del label (ej. `2:28|`) no forma parte del ID validado.
2. **Scan de bullets manuales:** ningún párrafo dentro de un tag empieza con
   `•`, `-`, `*` o número seguido de punto.
3. **Scan de `[PENDING DATA]` con evidencia de reencuadre intentado:** por
   cada ocurrencia, el footer declara explícitamente (a) qué hecho(s) del
   Canon se evaluaron para ese slot, (b) qué intento de reencuadre se hizo
   bajo la regla 6, y (c) por qué el reencuadre falló — distinguiendo entre
   "ausencia real en Canon", "Anti-overselling" (el reencuadre generaría un
   claim que el JD contradice), o "mismatch de disciplina total" (el eje
   temático del slot no tiene ningún paralelo posible con el JD, ej. VM vs.
   Data Analytics). Una entrada de `[PENDING DATA]` sin este detalle es una
   entrega incompleta.
4. **Cross-check de slot contra batch de sesión:** si el mismo
   `figma_text_id` tiene contenido válido en un CV-B previo de la sesión y el
   nuevo output es `[PENDING DATA]`, tratarlo como alerta de probable omisión
   y re-verificar contra la regla 6 antes de aceptar el pendiente.

## Restricción de Lote (Single-Item Processing)

CV-B procesa exactamente UN HANDOFF por invocación, incluso en batch. Tomar
el primero, procesarlo completo, detenerse y esperar invocación explícita
para el siguiente.

## Anti-cloning Guard

Antes de emitir el Markdown, verificar que ningún bullet de Experience
coincide verbatim con el de un CV-B previo del mismo Positioning Mode en esta
sesión o batch. Match exacto → re-derivar desde `fit_gaps`/`JD_keywords_top6`
del HANDOFF activo, o desde el mismo pool de match transferible con distinto
ángulo. Dos HANDOFFs de match fuerte pueden legítimamente converger en el
mismo dato subyacente del Canon (Tier 1/match literal) — el Anti-cloning
Guard exige diferenciación de *redacción*, no prohíbe reusar el mismo hecho.

## Output — Naming Convention del Archivo (KERNEL:FILE-NAMING-001)

El nombre del archivo `.md` debe seguir estrictamente el formato del Kernel:

```
{YYYY}_{FirstName}_{LastName}_{Empresa}_{Rol}_CV-B.md
```

Donde:
- `YYYY`: Año de la sesión (ej. `2026`).
- `FirstName_LastName`: `Mauricio_Meyran` (fijo, del Career Canon).
- `Empresa`: Nombre de la empresa extraído del HANDOFF (`empresa`), normalizado (espacios → underscores, sin caracteres especiales).
- `Rol`: Título del rol extraído del HANDOFF (`rol`), normalizado (espacios → underscores, sin caracteres especiales).
- `Phase`: `CV-B` (fijo para esta skill).

Ejemplo canónico:
- `2026_Mauricio_Meyran_Dior_VM_Trade_Coordinator_CV-B.md`

Si algún campo (empresa o rol) no está disponible al momento de la entrega, detener y solicitar al operador — no inferir ni usar placeholders.

## Output — Formato de Entrega (único artefacto)

**Un único artefacto:** archivo `.md` descargable, generado directamente tras
la Verificación Pre-Entrega interna. No se presenta markdown en chat ni se
espera confirmación del operador antes de escribir el archivo — el único output
de chat es la notificación de entrega.

El archivo debe incluir el footer de metadata obligatorio: versión del Output
Contract, Positioning Mode activo, referencia canónica al Canon usado, y
detalle de Verificación Pre-Entrega punto 3 para cada `[PENDING DATA]`.

Generar el archivo con `create_file`, **nombrándolo según la Naming Convention
de arriba**, guardarlo en `/mnt/user-data/outputs/`, y presentarlo con
`present_files`. No agregues explicación adicional en el chat fuera del propio
archivo — el mensaje de chat que acompaña la entrega debe ser mínimo (una línea,
sin resumen del contenido).

### Verificación de Encoding (post-escritura)

Después de `create_file`, releer con `view` antes de `present_files` y
confirmar que los caracteres acentuados y ñ se muestran correctamente
("MEYRÁN", "L'ORÉAL", "AÉROPOSTALE"). Si hay corrupción, no entregar —
reportar antes de reintentar.