---
name: vantage-cv-b
description: Fase 2 del pipeline de CV de VANTAGE (KERNEL:CV-PIPELINE-002) — construye el CV final aplicando el Output Contract Framework para integración directa con Figma, a partir de un HANDOFF generado por vantage-cv-a. Usar cuando el operador invoque el trigger "CV-B [HANDOFF]", pegue o adjunte un HANDOFF de CV-A y pida construir el CV, o pida generar el Markdown con Figma Tags para una vacante ya analizada. También activar si el operador pide "serializar" un CV para Figma o menciona figma_text_id, Golden Skeleton, o Figma Sync Protocol. No usar sin un HANDOFF previo de vantage-cv-a — si no existe, redirigir primero a esa skill. No usar para el análisis inicial de la vacante (eso es vantage-cv-a) ni para la auditoría final del PDF (eso es vantage-qa).
---

# VANTAGE — Skill CV-B (Construcción y Contrato de Salida)

ID Canónico: `KERNEL:CV-PIPELINE-002` · Trigger: `CV-B [HANDOFF]`

## Responsabilidad

Segunda fase del pipeline de CV. Toma el HANDOFF de `vantage-cv-a` y construye el CV final serializado en Markdown con Figma Tags, listo para sincronizar con el archivo Figma vía el Output Contract Framework (`CANON:OUTPUT-CONTRACT`).

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
Si el Career Canon no tiene información suficiente para un slot específico, el slot se mantiene con su ID original y el texto `[PENDING DATA]`, o queda vacío — pero **nunca se elimina**.

Regla adicional: mantener el escaping de `(` y `)` para compatibilidad con el plugin de Figma si el Skeleton original lo usa.

## Estructura — Golden Skeleton

Referencia: `CANON:OUTPUT-CONTRACT-002`. Secuencia exacta de slots para cualquier output destinado a Figma:

| Slot | Contenido |
|---|---|
| 2055:9 | Name |
| 2055:10 | Headline / Tagline |
| 2043:51 | Profile (párrafo 1) |
| 2043:52 | Profile (párrafo 2) |
| 2043:56–58 | Skills (1–3) |
| 2043:64+ | Experience |

Si el Skeleton cambia en Figma, `registry_seed.json` debe actualizarse antes del siguiente run de CV-B — si detectas una inconsistencia entre lo que produces y lo que el registry indica, repórtalo al operador antes de continuar, no lo resuelvas por inferencia (`SP:CONSISTENCY`).

## Aplicación del Positioning Mode en el output

Referencia: `CANON:OUTPUT-CONTRACT-005`. Los siguientes slots son variables según el modo activo (N1–N4) declarado en el HANDOFF:

- `2055:10` — tagline
- `2043:51` / `2043:52` — párrafos de perfil 1–2
- `2043:56` / `2043:57` / `2043:58` — skills 1–3
- Bullets de C01–C05 (Experience Records) — priorizados según el modo activado

**No mezclar bullets de dos Positioning Modes distintos en un mismo CV-B.**

## Reglas de Serialización

Referencia: `CANON:OUTPUT-CONTRACT-004`.

- Cada tag = párrafo independiente (sin listas, sin guiones)
- Bold = keywords estratégicos dentro del párrafo
- Empresa = bold standalone en su propio tag
- Rol = **bold rol** *italic período*
- Skills = `Categoría: texto plano`
- Tagline = `[Título · Subtítulo] · Ciudad | Tel | Email | LinkedIn | Portfolio`
- `&` en nombres de empresa se mantiene como `&`

## Restricción de Lote (Single-Item Processing)

CV-B procesa exactamente UN HANDOFF por invocación, incluso si el operador entrega un batch. Ante un batch: tomar el primer HANDOFF, procesarlo completo, detenerse y esperar invocación explícita separada para el siguiente. Razón: degradación de densidad narrativa observada empíricamente en procesamiento secuencial de lote (v9.16.0 post-mortem) — el Anti-cloning Guard previene duplicación entre vacantes pero no previene la caída de esfuerzo por fatiga de lote dentro de una sola sesión continua.

## Anti-cloning Guard (v9.16.0)

Antes de emitir el Markdown, verificar que ningún bullet de Experience coincide verbatim con el de un CV-B previo del mismo Positioning Mode en esta sesión o batch. Match exacto → re-derivar desde `fit_gaps`/`JD_keywords_top6` del HANDOFF activo. Reutilizar bullets pre-redactados entre vacantes distintas viola `KERNEL:CV-PIPELINE-002` y `CANON:OUTPUT-CONTRACT-001` (Regla #5, Distinctiveness Rule).

## Output — Formato de Entrega Obligatorio (dos artefactos)

1. **Markdown en chat, dentro de un bloque de código `markdown`**, como contenido para la página de la vacante en Notion. Debajo, en párrafo aparte, un footer con metadata: versión del Output Contract, Positioning Mode activo, referencia canónica al Canon usado.
2. **Archivo `.md` descargable**, idéntico al Markdown presentado y autorizado por el operador — cada slot encabezado por `###### figma_text_id` en línea propia. Este archivo es el entregable de trabajo para actualizar Figma.

No generes el archivo `.md` (artefacto 2) hasta que el operador confirme el bloque de código (artefacto 1) — el contrato exige "presentado y autorizado". Si el operador ya indicó de antemano que quiere ambos sin pausa (ej. usando `APROBAR_WRITE` o equivalente en el mismo turno), puedes generar ambos directamente.

Entrega el `.md` con `create_file` en `/mnt/user-data/outputs/` y `present_files`.
