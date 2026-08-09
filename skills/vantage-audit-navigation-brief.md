---
name: vantage-audit-navigation-brief
description: Audita si cambios documentales en fundacionales o altas/bajas de ID canónico requieren parches de armonía en el Navigation Brief u otros documentos, automatizando el Impact Assessment Contract (BRIEF:07.1). Activar ante peticiones de "audit brief" o tras confirmar un write (post APROBAR_WRITE) a fundacionales sin evaluación de impacto. Emite veredicto binario PASS o UPDATE REQUIRED con nodos afectados. Es de solo lectura; nunca escribe en Notion. Para ejecutar parches resultantes, invocar vantage-documentacion-transversal-propuesta. No usar para: auditoría de CV/PDF (vantage-qa), sincronizar Script/Skill Library, alta de IDs huérfanos en CENSUS_SPEC (vantage-sync-census-spec — esta skill solo señala cuándo invocarla), ni para verificar lockstep de versión (verify_versions.py).
---

# VANTAGE — Audit Navigation Brief

Linter de arquitectura documental. Cruza los cambios de la sesión actual contra la Matriz de Dependencias de `BRIEF:CROSS-DEPENDENCIES` ([BRIEF:07](https://app.notion.com/p/3a3938befc4280089e90ec435c01f50d#3af938befc428125baaceb22b3acfed3)) y emite un veredicto binario sobre si la navegación documental sigue siendo válida. Es de solo lectura: reporta hallazgos, nunca parchea.

**Por qué es solo lectura:** el Impact Assessment (BRIEF:07.1) es un contrato de diagnóstico, no de remediación — mezclar diagnóstico con escritura arriesgaría aplicar un parche antes de que el operador vea el mapa completo de nodos afectados. Separar ambas fases (como ya hace el protocolo de documentación transversal) preserva la Golden Rule de VANTAGE de nunca escribir sin `APROBAR_WRITE` sobre un plan ya visto.

## Invariante crítica

Prohibido generar Canon estratégico nuevo o inferir nuevas reglas de negocio/autoridad documental ([KERNEL:PURPOSE-001](https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7#3af938befc4281c49ef9e1a931655091)). Ante cualquier relación de dependencia no cubierta explícitamente por `BRIEF:CROSS-DEPENDENCIES`, escalar a decisión humana — no asumir ni extender la matriz por analogía.

## Cuándo se activa

- El operador pide explícitamente "auditar Navigation Brief", "audit brief", "AUDIT-BRIEF", o pregunta si un cambio reciente rompe la navegación documental.
- Modo derivado (no bloqueante): durante cualquier otra tarea de la sesión, si se detecta una escritura confirmada (`APROBAR_WRITE` ya ejecutado) sobre `KERNEL:*`, `MANUAL:*`, `CANON:*`, `SP:*`, `ALIASES:*`, IDs canónicos, Tracker Schema o Runtime — señalar el gap y ofrecer correr la auditoría antes de cerrar sesión.

No se activa sobre cambios propuestos aún no escritos (DRY RUN sin `APROBAR_WRITE`) — la auditoría evalúa estado post-escritura, no hipótesis.

## Alcance y ownership

Respeta estrictamente:
- **Jerarquía de capas** ([KERNEL:ARCHITECTURE-L4](https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7#112a181a8573420888342840865da012)) — esta skill opera en L0/L1 (observabilidad y verificación documental), nunca ejecuta ni valida Runtime (L2) ni Pipeline (L3).
- **Ownership de namespaces** (`KERNEL:SCHEMA-004`) — no reclasifica ni reasigna qué documento es SSOT de qué dominio; solo lee la Matriz de Autoridad ([BRIEF:02](https://app.notion.com/p/3a3938befc4280089e90ec435c01f50d#3af938befc4281039f28e60fd49760af)) tal como está escrita.

## Protocolo de ejecución

Al activarse, declarar: `AUDITING NAVIGATION...`

### Paso 1 — Fase de Ingesta
Identificar los IDs canónicos (`KERNEL:ID`, `MANUAL:ID`, `CANON:ID`, `SP:ID`, `ALIASES:ID`) modificados o creados en la sesión actual, exclusivamente a partir de:
- Writes confirmados en esta conversación (post write-back verification), o
- El Session Ledger / Changelog si la sesión fue reabierta tras un handoff.

Nunca inferir cambios no confirmados por escritura real en Notion.

Si no hay cambios identificables en la sesión, reportarlo y detener la ejecución — no hay nada que auditar.

### Paso 2 — Cruce de Dependencias
Fetch en vivo de `BRIEF:CROSS-DEPENDENCIES` ([BRIEF:07](https://app.notion.com/p/3a3938befc4280089e90ec435c01f50d#3af938befc428125baaceb22b3acfed3)) — nunca desde memoria de sesión. Aplicar la matriz fila por fila contra los IDs del Paso 1:

| Origen del cambio | Evaluar | Acción mínima |
|---|---|---|
| Kernel | Manual, Navigation Brief, System Prompt | Revisar contratos afectados |
| Manual | Navigation Brief | Verificar que la navegación siga siendo válida |
| Career Canon | CV Skills, Output Contracts | Validar consistencia del pipeline CV |
| Tracker Schema | Runtime, Manual | Verificar compatibilidad del esquema |
| Aliases | Runtime, Resolver Registry | Regenerar índices si aplica |
| Runtime | ID Census | Regenerar artefactos de observabilidad |
| IDs (alta/baja) | ID Census | Ejecutar `vcensus` |
| Bootstrap / System Prompt | Navigation Brief | Validar estrategia de recuperación |
| Estructura documental | Master Index | Actualizar inventario |

Si el cambio implica alta o baja de un ID canónico (no solo edición de contenido de un ID existente), exigir regeneración del ID Census como condición — citar [BRIEF:07](https://app.notion.com/p/3a3938befc4280089e90ec435c01f50d) y [KERNEL:DOCUMENTATION-008](https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7#3af938befc4281d788e5c96f99f3b6e8) (Sincronización Obligatoria del ID Census). Si `vcensus` reporta IDs bajo "huérfanos (en docs, fuera de spec)" — el ID ya existe en el documento vivo pero `generate_census.py` aún no lo conoce — señalar `vantage-sync-census-spec` como el skill que ejecuta esa alta en `CENSUS_SPEC`; esta skill no la invoca ni la sustituye, solo la referencia como siguiente paso.

### Paso 3 — Análisis de Impacto (checklist BRIEF:07.1)
Para cada dependencia disparada en el Paso 2, responder explícitamente las seis preguntas del Impact Assessment Contract ([BRIEF:CROSS-DEPENDENCIES-001](https://app.notion.com/p/3a3938befc4280089e90ec435c01f50d#3af938befc428192b694d940e25e003f)):
1. ¿Qué documentos pueden verse afectados?
2. ¿Qué contratos deben verificarse?
3. ¿Es necesaria una actualización documental?
4. ¿Debe regenerarse algún artefacto de Runtime?
5. ¿Debe ejecutarse una validación adicional?
6. ¿Se requiere sincronización (`vsync_doc`, `vversions`, `vcensus`)?

Adicionalmente, evaluar si el cambio afecta directamente:
- La **Matriz de Autoridad** ([BRIEF:02](https://app.notion.com/p/3a3938befc4280089e90ec435c01f50d#3af938befc4281039f28e60fd49760af)) — ¿algún dominio cambió de SSOT?
- Los **Dominios** ([BRIEF:05](https://app.notion.com/p/3a3938befc4280089e90ec435c01f50d#3af938befc42813eb510e8fec88ffe37)) — ¿algún dominio (Housekeeping, Core Assets, Discovery, Gate Logic, CV Pipeline) ganó o perdió un componente?

Si la respuesta a cualquiera de estas dos últimas preguntas es afirmativa, marcarlo como hallazgo de **alta prioridad** — un cambio de autoridad o dominio nunca es cosmético.

### Paso 4 — Veredicto de Auditoría
Emitir uno de dos veredictos, sin intermedios:

- **`PASS`** — La navegación sigue siendo válida. Ningún nodo de `BRIEF` requiere parche. (Aplica incluso si hubo cambios, siempre que ninguno dispare una fila de la matriz de dependencias, o si las dependencias disparadas ya estaban satisfechas antes del cierre de sesión.)
- **`UPDATE REQUIRED`** — Listar cada nodo que necesita parche de armonía, en formato:
  - `[Documento]:[ID exacto o sección]` — descripción de 1 línea del gap detectado.

Cerrar siempre con la misma línea de transición, sin importar el veredicto: *"Esta auditoría es solo-lectura. Para ejecutar los parches listados, invocar `vantage-documentacion-transversal-propuesta`."*

Al finalizar, declarar: `NAVIGATION AUDIT FINISHED`

## Restricciones

- **No escribe en Notion.** Ni en el Navigation Brief, ni en ningún documento fundacional, ni en el Changelog. El resultado es un reporte para que el operador decida.
- **No ejecuta DRY RUN.** Esta skill no es parte del protocolo de escritura; si el veredicto es `UPDATE REQUIRED`, la transición explícita es a `vantage-documentacion-transversal-propuesta` (Fase 1 de mapeo) y de ahí, tras `APROBAR_WRITE`, a `vantage-documentacion-transversal-implementacion`.
- **No infiere nuevas relaciones de dependencia.** La matriz de `BRIEF:07` es en sí misma parte del Canon del sistema — extenderla por analogía sería crear una regla de negocio nueva sin autoría humana, exactamente lo que la Invariante Crítica prohíbe. Si un cambio no encaja en ninguna fila pero intuitivamente "parece" requerir revisión de otro documento, señalarlo como **duda escalada** — no como hallazgo — y preguntar al operador si debe tratarse como precedente para ampliar la matriz (lo cual, de aprobarse, es en sí mismo un cambio a `BRIEF:07` y dispara su propia auditoría).
- **No sustituye `verify_versions.py`.** La verificación de versión en lockstep de los nueve documentos fundacionales es un proceso distinto (ver [SP:VERSION-CHECK-TOOL](https://app.notion.com/p/37b938befc4280019b9bfcf81130d274#3af938befc428191acd1e6a71d7f5cc4)); esta skill asume que la sincronización de versión ya es correcta y audita solo dependencias de contenido/estructura.

## Salida de este skill

Exclusivamente:
1. Bloque de Ingesta (Paso 1): IDs auditados.
2. Bloque de Cruce de Dependencias (Paso 2): filas de la matriz disparadas.
3. Bloque de Análisis de Impacto (Paso 3): las seis preguntas respondidas + Matriz de Autoridad/Dominios.
4. Veredicto (Paso 4): `PASS` o `UPDATE REQUIRED` con lista de nodos.

Nunca contenido de parche, nunca escritura, nunca DRY RUN.

## Gestión de hallazgos pendientes

Si el veredicto es `UPDATE REQUIRED` y el operador no invoca de inmediato `vantage-documentacion-transversal-propuesta`, registrar en **Tasks Tracker** (`d2a65ca1-6a35-465d-bcff-b0d82dddd549`):
- Título: `[DOC] Audit Brief — UPDATE REQUIRED: [descripción breve]`.
- Prioridad: Alta si involucra Matriz de Autoridad o Dominios; Media en cualquier otro caso.
- IDs relacionados: los nodos listados en el veredicto.
- Contexto: qué cambio originó la auditoría y qué dependencias quedaron sin resolver.

Revisar el Tracker al abrir sesión (`vantage-session-open`) para no perder auditorías `UPDATE REQUIRED` pendientes.