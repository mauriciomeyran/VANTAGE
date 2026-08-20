---
name: vantage-cv-b
description: Fase 2 del pipeline de CV de VANTAGE (KERNEL:CV-PIPELINE-002) — construye el CV final aplicando el Output Contract Framework para integración directa con Figma, a partir de un HANDOFF generado por vantage-cv-a. Usar cuando el operador invoque el trigger "CV-B [HANDOFF]", pegue o adjunte un HANDOFF de CV-A y pida construir el CV, o pida generar el Markdown con Figma Tags para una vacante ya analizada. También activar si el operador pide "serializar" un CV para Figma o menciona figma_text_id, Golden Skeleton, o Figma Sync Protocol. No usar sin un HANDOFF previo de vantage-cv-a — si no existe, redirigir primero a esa skill. No usar para el análisis inicial de la vacante (eso es vantage-cv-a) ni para la auditoría final del PDF (eso es vantage-qa).
---

# VANTAGE — Skill CV-B (Construcción y Contrato de Salida)

ID Canónico: `KERNEL:CV-PIPELINE-002` · Trigger: `CV-B [HANDOFF]`
Versión de alineación: v9.17.0 (patch post-mortem 2026-08-19 — BUG_TICKET x2, ver Bug Tracker)

## Responsabilidad

Segunda fase del pipeline de CV. Toma el HANDOFF de `vantage-cv-a` y construye el CV final serializado en Markdown con Figma Tags, listo para sincronizar con el archivo Figma vía el Output Contract Framework (`CANON:OUTPUT-CONTRACT`).

## Fuera de Scope — Explícito (nuevo, v9.17.0)

Esta skill entrega **Markdown con figma_text_id**. Cómo el plugin de Figma consume,
parsea o transforma ese Markdown (JSON intermedio, `boldRanges`, regex de parser,
estructura de `ui.html` o cualquier script de conversión downstream) es un
componente fuera del scope de esta skill y no está documentado aquí.

Si el operador pregunta sobre esto, o hay una falla de render en Figma:
- La respuesta correcta es declarar el límite: "Fuera de scope de CV-B — necesito
  ver el script/plugin fuente real antes de diagnosticar."
- **Nunca especular** sobre parsers, regex, schemas o mecanismos de conversión que
  no estén confirmados leyendo un archivo fuente real en esa sesión.
- Inventar mecanismo sobre un componente no confirmado viola `SP:CONSISTENCY` y
  puede romper sincronización real en Figma (ver BUG_TICKET, detectado 2026-08-19).

## Input requerido

HANDOFF completo generado por `vantage-cv-a`, incluyendo:
- Positioning Mode seleccionado (no procesar si el HANDOFF reporta "EMPATE — requiere decisión humana" sin resolución)
- Gap Analysis (matches directos, parciales, gaps)
- Validación de exclusiones ya en PASA

Si el HANDOFF está incompleto o el Positioning Mode no está resuelto, detener y solicitar al operador que complete CV-A primero.

## Protocolo de Sincronización — FIGMA SYNC PROTOCOL (STRICT)

Referencia: `CANON:OUTPUT-CONTRACT-001`. Estas tres reglas son no-negociables:

### 1. Inmutabilidad de IDs (`figma_text_id`)
Los `###### figma_text_id` son llaves primarias. **Terminantemente prohibido** alterarlas, omitirlas o inventar nuevas. El SSOT de IDs de nodo es `registry_seed.json` en `04-Vantage_CV/Figma Sync/`. Si hay discrepancia entre un `figma_text_id` usado aquí y el registry, **el registry gana** — consultarlo antes de generar el output si hay cualquier duda.

### 2. Integridad de Slots
No se permiten fusiones ni divisiones de bloques. Si el Golden Skeleton tiene 4 bullets para una experiencia, el output DEBE tener 4 bloques, incluso si uno queda vacío.

### 3. Regla de llenado nulo
Si el Career Canon no tiene información suficiente para un slot específico, el slot se mantiene con su ID original y el texto `[PENDING DATA]`, o queda vacío — pero **nunca se elimina**. Ver Verificación Pre-Entrega abajo: `[PENDING DATA]` requiere evidencia de búsqueda, no es default por omisión.

Regla adicional: mantener el escaping de `(` y `)` para compatibilidad con el plugin de Figma si el Skeleton original lo usa.

## Estructura — Golden Skeleton

Referencia: `CANON:OUTPUT-CONTRACT-002`. El SSOT de IDs de nodo es `registry_seed.json`
en `04-Vantage_CV/Figma Sync/`. **Obligatorio: leer este archivo antes de generar
cualquier output** — nunca usar una tabla de IDs memorizada o hardcodeada en este
skill, porque el Skeleton puede cambiar en Figma sin que este documento se actualice.

El registry mapea `slot_name` → `figma_text_id`. Las llaves ya están ordenadas
C01→C05 (L'Oréal → Bisonte → Levi's/Dockers → Aéropostale → Palacio de Hierro) —
ese orden de llaves en el JSON es la referencia física de secuencia, además de la
regla explícita en `CANON:OUTPUT-CONTRACT-005`.

Si `registry_seed.json` no está disponible o no se puede leer, detener la generación
y solicitar el archivo al operador — no inventar ni asumir IDs.

Si detectas una inconsistencia entre lo que produces y lo que el registry indica,
repórtalo al operador antes de continuar, no lo resuelvas por inferencia (`SP:CONSISTENCY`).

## Contenido de Skills — Mapeo Obligatorio

Los 5 slots de Skills (2:14–2:18, o los que indique el registry) deben mapear a las 5 categorías de `CANON:SKILLS`: Estrategia Visual, Operaciones & Finanzas, Liderazgo & Training, Stack Técnico, Idiomas. No es opcional cubrir las 5 — la Null-Fill Rule
(`[PENDING DATA]`) aplica solo cuando el Canon carece de contenido para una categoría, nunca como default por no haber consultado la categoría. Priorizar orden y densidad por Positioning Mode activo, pero las 5 categorías deben tener contenido antes de considerar el CV-B completo.

## Aplicación del Positioning Mode en el output

Referencia: `CANON:OUTPUT-CONTRACT-005`. Los siguientes slots son variables según el modo activo (N1–N4) declarado en el HANDOFF (IDs de referencia según Golden Skeleton actual — verificar siempre contra `registry_seed.json`, ver sección anterior):

- `2:5` — tagline
- `2:9` / `3:13` — párrafos de perfil 1–2
- `2:14` / `2:15` / `2:16` — skills 1–3
- Bullets de C01–C05 (Experience Records) — priorizados según el modo activado

**No mezclar bullets de dos Positioning Modes distintos en un mismo CV-B.**

**Experience conserva siempre la secuencia C01–C05, sin excepción.** "Priorizado según
el modo" significa mayor densidad narrativa, mayor extensión de bullets, o mayor peso
de keywords estratégicos en las compañías ancladas del modo activo — nunca significa
reordenar las compañías. El orden cronológico C01→C05 es inmutable independientemente
del Positioning Mode (`CANON:OUTPUT-CONTRACT-005`).

## Reglas de Serialización

Referencia: `CANON:OUTPUT-CONTRACT-004`.

- Cada tag = párrafo independiente (**sin listas, sin guiones, sin bullets manuales
  `•`/`-`/`*` al inicio de párrafo** — el figma_text_id ya es el separador estructural)
- Bold = keywords estratégicos dentro del párrafo
- Empresa = bold standalone en su propio tag
- Rol = **bold rol** *italic período*
- Skills = `Categoría: texto plano`
- Tagline = `[Título · Subtítulo] · Ciudad | Tel | Email | LinkedIn | Portfolio`
- `&` en nombres de empresa se mantiene como `&`

## Verificación Pre-Entrega — Obligatoria (nuevo, v9.17.0)

Antes de presentar el `.md` (artefacto 1 o 2), correr estos tres checks y no
proceder si alguno falla:

1. **Scan de bullets manuales:** ningún párrafo dentro de un tag empieza con
   `•`, `-`, `*` o número seguido de punto. Si se encuentra uno, corregir antes
   de entregar — viola la Regla de Serialización.
2. **Scan de `[PENDING DATA]` con evidencia:** por cada ocurrencia, el footer
   de entrega debe declarar explícitamente qué se buscó en el Career Canon y
   por qué no hay dato — nunca dejarlo como default silencioso por no haber
   consultado la categoría/slot correspondiente.
3. **Cross-check de slot contra batch de sesión:** si el mismo `figma_text_id`
   tiene contenido válido en un CV-B previo de la misma sesión (aunque sea de
   otro Positioning Mode o vacante), y el output nuevo para ese mismo tag es
   `[PENDING DATA]`, tratarlo como alerta de probable omisión — no como
   ausencia real de Canon — y re-verificar antes de entregar.

## Restricción de Lote (Single-Item Processing)

CV-B procesa exactamente UN HANDOFF por invocación, incluso si el operador entrega un batch. Ante un batch: tomar el primer HANDOFF, procesarlo completo, detenerse y esperar invocación explícita separada para el siguiente. Razón: degradación de densidad narrativa observada empíricamente en procesamiento secuencial de lote (v9.16.0 post-mortem) — el Anti-cloning Guard previene duplicación entre vacantes pero no previene la caída de esfuerzo por fatiga de lote dentro de una sola sesión continua.

## Anti-cloning Guard (v9.16.0)

Antes de emitir el Markdown, verificar que ningún bullet de Experience coincide verbatim con el de un CV-B previo del mismo Positioning Mode en esta sesión o batch. Match exacto → re-derivar desde `fit_gaps`/`JD_keywords_top6` del HANDOFF activo. Reutilizar bullets pre-redactados entre vacantes distintas viola `KERNEL:CV-PIPELINE-002` y `CANON:OUTPUT-CONTRACT-001` (Regla #5, Distinctiveness Rule).

## Output — Formato de Entrega Obligatorio (dos artefactos)

1. **Markdown en chat, dentro de un bloque de código `markdown`**, como contenido para la página de la vacante en Notion. Debajo, en párrafo aparte, un footer con metadata: versión del Output Contract, Positioning Mode activo, referencia canónica al Canon usado, y (si aplica) el detalle de la Verificación Pre-Entrega punto 2.
2. **Archivo `.md` descargable**, idéntico al Markdown presentado y autorizado por el operador — cada slot encabezado por `###### figma_text_id` en línea propia. Este archivo es el entregable de trabajo para actualizar Figma.

No generes el archivo `.md` (artefacto 2) hasta que el operador confirme el bloque de código (artefacto 1) — el contrato exige "presentado y autorizado". Si el operador ya indicó de antemano que quiere ambos sin pausa (ej. usando `APROBAR_WRITE` o equivalente en el mismo turno), puedes generar ambos directamente.

Entrega el `.md` con `create_file` en `/mnt/user-data/outputs/` y `present_files`.

### Verificación de Encoding (post-escritura)

Después de `create_file`, releer el archivo con `view` antes de `present_files` y
confirmar visualmente que los caracteres acentuados y ñ se muestran correctamente
(ej. "MEYRÁN", "L'ORÉAL", "AÉROPOSTALE" — no "MEYRÃ¡N" ni secuencias con Â).
Si se detecta corrupción, no entregar el archivo — reportar al operador antes de
reintentar.