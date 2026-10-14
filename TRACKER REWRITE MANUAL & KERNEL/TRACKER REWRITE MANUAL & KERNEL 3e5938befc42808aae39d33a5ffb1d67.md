# TRACKER REWRITE MANUAL & KERNEL

Fecha de actualización: 2026-10-13 (PROPUESTA ARENA/DEFAULT — pendiente de DRY RUN + APROBAR_WRITE; sin handoff emitido)
Documentos hijos: V | PLAN DE TRABAJO (tareas) · V | RECONCILIATION LOG (eventos)
Regla de no-duplicación: esta página contiene ESTRUCTURA (proyectos, fases, checkpoints, grupos de consolidación, decisiones abiertas). El estado de cada tarea vive SOLO en el PLAN; los hechos fechados viven SOLO en el LOG; las decisiones estructurales mayores viven SOLO en el Charter (vía ticket CHARTER evaluado por CLAUDE/MAIN).

## 0 · Cómo usar esta página
- session-open: leer §3 Tablero y §5 Decisiones; no re-levantar diagnóstico (Fase 0/1 cerradas).
- session-close: el delta de tareas se registra en el PLAN (Estado/Evidencia/Verificado_Por) y el hecho en el LOG; aquí solo cambia el Tablero si cambió un checkpoint o una fase.
- Toda escritura al tracker: re-fetch previo → DRY RUN → APROBAR_WRITE → verificador distinto del ejecutor (NON-NEGOTIABLES-002/003).
- Etiquetas de procedencia en Evidencia/Notas: [V: <agente/terminal>, <fecha>] verificado · [D: <agente>] declarado sin verificación independiente.

## 1 · Contexto (foto al 2026-10-13)
- Repo: origin/main = merge 23e1e1e (PR #27 fusionado) [D: CHATGPT, CHANGELOG v9.22.47]; espejo 16:17 CDMX = ce21153 con código warmup/T1–T4 en Layer_1/scripts/vantage-sync.py [V: lectura ARENA]. Worktree canónico en detached HEAD sobre origin/main; ramas locales main (7552499) y devin/vantage-sync-r4 (c0443fd) eliminadas con commits exclusivos sin destino; rama Copilot 5a37139 conservada local [D: CHATGPT]. origin por HTTPS (gh auth) [D: CHATGPT]. No existe .github/workflows (sin CI) [V: espejo].
- Notion: CHANGELOG v9.22.47 (16 entradas, límite 10 → rotación pendiente a V | CHANGELOG — ARCHIVO); SP/Census/Charter v9.22.46 → vversions --sync pendiente. Census regenerado 2026-10-13 01:56 CDMX sin KERNEL:OPS-INTERVIEW-SIMULATOR ni MANUAL:RUNTIME-INTERVIEW-SIMULATOR (altas de v9.22.46).
- L1: dry-run E2E Workday/Chanel con T11: 6 BLOCKED / 5 limpio / 0 REVIEW_NEEDED (LOG #100). Primer --apply autorizado 2026-10-12, no ejecutado (LOG #102); condición: T3.X rotado + suite L1 desde origin/main + dry-run reconfirmado + re-fetch de 5 registros. LinkedIn: normalizador accepted[] en main [V: espejo]; 9 queries v2.0 sin ejecutar.
- Seguridad: token con formato ntn_ sigue en Dashboard/archive/legacy_express_node/server.js:13 en main [V: espejo 16:17]; vigencia no probada.
- Frente sin filas: Interview Simulator (Artifact privado, no escribe en Notion/repo, no es fuente de verdad) [D: CLAUDE/MM v9.22.44; MISTRAL v9.22.46].

## 2 · Estructura del plan
### 2.1 Proyectos (dimensión "resultado"; etiquetas de plan, no IDs canónicos)
DOCS · GATE · WORKDAY · LINKEDIN · REPO · GOV · ISIM. Mientras el PLAN no tenga columna Proyecto (DEC-11), la etiqueta va al inicio de Notas como [PRJ:<etiqueta>][CG:<grupo>][CP:<checkpoint>].

### 2.2 Fases (mismas opciones del select; semántica precisada)
- Fase 0 — Diagnóstico. CERRADA. Reapertura solo si una línea base verificada (versión vigente, schema Tracker, script activo, estado Graph) resulta falsa. 3 filas Resuelto sin Verificado_Por → "cierre histórico" (DEC-13).
- Fase 1 — Correcciones puntuales. CERRADA. 5 filas Resuelto sin Verificado_Por → "cierre histórico" (DEC-13). Reapertura: misma regla que Fase 0.
- Fase 2 — Escritura normativa v10. ABIERTA.
  Objetivo: Kernel v10.4 sin residuos y Manual alineado (o v10 real, según DEC-02), Charter con tickets evaluados y aplicados.
  Entra: CG-01, CG-02, CG-03; resolución de ownership de los 4 campos (DEC-07). No entra: sync fundacional (Fase 3), código, ISIM features.
  Insumos: export vivo de Kernel/Manual, acta 2026-10-03, decisiones B1=A/B2/B3/D1, Charter v9.22.46, CHANGELOG .44–.47.
  Entregables: 3 pases únicos (Kernel, Manual, Charter) con DRY RUN + APROBAR_WRITE + verificación de actor distinto + entrada CHANGELOG cada uno.
  Criterio de salida: todas las filas Fase 2 en Resuelto con Verificado_Por ≠ ejecutor, o cerradas por decisión del operador registrada en el LOG. Cierre: el operador lo declara en §3 + entrada CHANGELOG. Reapertura: hallazgo normativo que exija editar Kernel/Manual más allá de un fix.
- Fase 3 — Consolidación y operación controlada. ABIERTA (en paralelo a Fase 2 por decisión del operador 2026-10-03; tensión con MILESTONES-004 registrada en DEC-09).
  Objetivo: (a) gate confiable y primer --apply (CP-3 → CP-1a); (b) LinkedIn E2E (CP-2); (c) repo línea base (CP-5); (d) sync fundacional único tras Fase 2 (CP-4b).
  Entra: CG-04…CG-09. No entra: redacción normativa.
  Criterio de salida: CP-1a, CP-2, CP-3, CP-4b, CP-5 satisfechos y MILESTONES-006/007 marcados en el Charter por el operador vía ticket. Reapertura: regresión en suite L1, hallazgo de seguridad, o divergencia main↔Notion detectada por vversions/vcensus.
- "Fase 4": no existe como opción del select; la usa CHANGELOG v9.22.44 para ISIM. Alta de opción = decisión del operador (DEC-08).

### 2.3 Checkpoints (evaluación de la propuesta CP-1…CP-4)
Orden real de dependencia: CP-3 → CP-1a → {CP-2, CP-1b} ; CP-4a → CP-4b ; CP-5 independiente salvo CG-06a (prerrequisito de CP-1a).
- CP-3 Gate Keeper funcional (precede a CP-1). Criterio: T3.A verde; paridad matcher↔hard_blocks.json (T3.I) verificada; exclusiones T11 (T3.O) alineadas con Manual §10; dry-run de ambos feeds sin falsos negativos sobre casos conocidos; decisión f9bb registrada. ↔ MILESTONES-007(b), DECISIONS-013/017.
- CP-1a Primer --apply controlado de Workday. Criterio: --apply acotado (5 registros) con re-fetch en Notion que confirme los registros creados y que Python escribió solo campos Class B/declarados; evidencia con fecha+commit en el Acta. ↔ MILESTONES-007(c).
- CP-1b Workday CANONICAL. Criterio: requisitos T3.J cumplidos (fila en registry, campo Tests, SHA re-anclado ≥ 318300a, evidence report verificado), T3.P resuelto o aceptado como limitación documentada, Acta/Brief rev3 verificados (T3.Q). ↔ sin hito propio (ticket CHARTER si se quiere).
- CP-2 LinkedIn operativo. Criterio propuesto (DEC-19 lo fija): 9 queries v2.0 ejecutadas en host del agente; envelope real por --file en dry-run E2E con registros válidos y archivo local sin escrituras a Notion (T3.N); brief LinkedIn rev3 verificado. --apply LinkedIn fuera de este CP. ↔ sin hito en Charter → ticket CHARTER (DEC-17).
- CP-4a Escritura v10 verificada = cierre de Fase 2 (CG-01 + CG-02 + CG-03 + pins/skills T2.G, T3.D). ↔ MILESTONES-002/003.
- CP-4b Sync fundacional único (CG-05: vcensus + registry + ALIASES + migración de citas legacy + vversions --sync + vgit + rotación CHANGELOG + T3.2). ↔ MILESTONES-004.
- CP-5 Repo línea base consolidada (nuevo). Criterio: main única local/remota, deltas con tag archive/, suite L1 verde desde origin/main, raíz y Archive/ según decisión por grupo (T3.Z), server.js retirado, invocación pytest canónica documentada (T3.T). ↔ MILESTONES-006.
Regla: tarea cerrada ≠ checkpoint satisfecho ≠ hito satisfecho ≠ fase cerrada. El hito lo marca solo el operador en el Charter.

### 2.4 Mapa de consolidación (grupos; detalle de tareas en el PLAN; trazabilidad en Registro de consolidación)
Principio: una lectura suficiente, una decisión consolidada, una intervención coherente, una verificación conjunta.
| Grupo | Resultado consolidado | Documento/sistema | Sustituye a | Prerrequisitos | Post-validación | Riesgo si se hace suelto |
|---|---|---|---|---|---|---|
| CG-01 Pase único KERNEL v10.4 | Kernel sin residuos (Dedup_Flag, B-09, ARCHIVEROS, 04.5 cifras/familias, layer_1_run.py, Match L417/446/692, ARC-L1 Career Sites, 4 modos→08.2, Hard Blocks 05/14.7, SCH-OWNERSHIP si DEC-07), §14.13 preservado | V \| KERNEL | T2.1, T2.O, T2.O-c, T2.D (parte Kernel), T2.H (parte Kernel), T2.N (verif. residual), T2.C (cierre) | DEC-01, DEC-07, respuesta P-01, grep de residuos sobre export vivo | 97 H/0 dup/0 refs colgantes; grep de residuos = 0; verificador ≠ ejecutor; entrada CHANGELOG | 5–7 ciclos de vversions/vgit y refs colgantes (patrón ya sufrido) |
| CG-02 Pase único MANUAL | 2a: alineación normativa (L64, L343-346 B2/B3; L890 Match; cifras B1=A; §10 exclusiones T11; texto "solo Terminal" B7; §21 tabla A/B si DEC-07; §9.6 preservado) · 2b: Manual v10 real + extracción Script/Skill Reference | V \| MANUAL (+ Script/Skill Reference) | T2.2b, T2.3b, T2.F, T2.H (Manual), T2.D (Manual), T2.G (texto), T3.O (doc), T3.D (texto) | DEC-01, DEC-02, CG-01 cerrado (citas) | 0 citas KERNEL:* legacy en Manual; verificador ≠ ejecutor; CHANGELOG | Re-escribir dos veces el mismo capítulo |
| CG-03 Ventana CHARTER | Un dictamen de CLAUDE/MAIN sobre todos los tickets pendientes → una aplicación del operador → una verificación | V \| PROJECT CHARTER (solo operador) | T2.CHARTER (residuo), T2.Q, T2.R (verif.), #107 colisión -013, T3.G decisión, borrador ISIM, hito LinkedIn, anotación MILESTONES-004/006 | DEC-06, DEC-09, DEC-17, DEC-18 | Re-fetch por actor distinto de MAIN; Census sin huérfanos CHARTER:*; CHANGELOG | Numeraciones en colisión y 4 escrituras al Charter |
| CG-04 Primer --apply controlado | MILESTONES-007(c) satisfecho | Terminal operador + Tracker (Class B) + Acta | T3.L, HO-000104.P3, (T3.X como gate), #102 | CG-06a terminado; dry-run reconfirmado 6/5; T3.O/T3.I sin cambios pendientes | Re-fetch de los 5 registros; 0 campos fuera de Class B; suite verde; LOG + CHANGELOG | --apply sobre main no verificado o con token vivo |
| CG-05 Sync fundacional único | Census/registry/ALIASES/pins coherentes con v10; migración de citas legacy (Manual 68, SP 11, Charter 3, Canon 1, Aliases 1; 23 skills; 19 scripts); vversions --sync; vgit; rotación CHANGELOG; T3.2 | Terminal operador + Notion | T3.1, T3.2, T3.Cb, (sync .47→.46), altas ISIM Census, rotación | CG-01, CG-02, CG-03 cerrados (o DEC-09 = sync de mantenimiento mínimo ahora) | vcensus 0 huérfanos sobre espejo actualizado; vversions sin FAIL; verificación cruzada T3.2 | Múltiples syncs parciales (MILESTONES-004) |
| CG-06a Seguridad + línea base mínima (sesión corta) | Token rotado; main local recreado desde origin/main; suite L1 desde origin/main; HO-000104.P2 reformulado | Terminal operador | T3.X (rotación), HO-000104.P2, HO-000104.P3, parte de T3.S (detached HEAD) | ninguno | `git status` en main tracking origin/main; pytest Layer_1 N passed registrado; token viejo revocado | vgit desde detached HEAD; --apply con token expuesto |
| CG-06b Repo línea base (decisiones por grupo) | main única; deltas (7552499, c0443fd, 5a37139, arena/d352bc18) con tag archive/ o descartados; raíz y Archive/ limpiados por grupo; server.js retirado; pytest canónico; deuda L4; Graph retirado si DEC-18; Raycast pausado/EXCLUDE_IDS | Repo (PR único o commits del operador) | T3.W (cierre), T3.Y (cierre), T3.Z, T3.T, T3.U, T3.G (código), T3.B, T3.S (cierre), HO-000104.P1, #101, #103, #106 | DEC-04, DEC-05, DEC-14, DEC-15, DEC-18; CG-03 (para T3.G) | `git branch -a` = main (+tags); suite verde; grep ntn_ = 0; docs sin rutas retiradas (DECISIONS-016) | 4–6 PRs de limpieza con conflictos |
| CG-07 LinkedIn E2E | 9 queries ejecutadas; envelope real por --file en dry-run; archivo local; hallazgos | Host del agente + Terminal | T3.M (cierre), T3.N (cierre), parte de T3.I, #61, #64 | Chromium en host; decisión A (solo accepted[]) vigente | Registros válidos = N; 0 escrituras Notion; LOG | Repetir setup del navegador por sesión |
| CG-08 Acta + Briefs rev3 | Acta de Operabilidad y briefs Workday/LinkedIn regenerados una sola vez con cifras de CG-04 y CG-07; verificación CS-VERIFY-L1-02 | Docs L1 / PROMPT_CANON | T3.K, T3.Q, T3.J (parte documental), #58, #59 | CG-04 y CG-07 terminados | CHATGPT verifica; registry con fila Career Sites | Regenerar el Acta tres veces |
| CG-09 Tracker y gobernanza | Aplicar esta reestructuración en un pase (PLAN+LOG+página); cerrar LOG superadas; Verificado_Por histórico; Orden; entrada CHANGELOG sesión 10-11→12; verificación de .45; triage Bug Tracker; pase NORM LOG/Bug Tracker | Tracker + Bug Tracker + CHANGELOG | T3.E, T3.D (skills), T2.K2, T2.O-b (sin fila), #20, #34, #99 | APROBAR_WRITE del operador sobre esta propuesta | Re-fetch por actor distinto; conteo de filas/estados = previsto | Deriva por tres agentes escribiendo sin pase común |
| CG-10 ISIM — registro de gobernanza | Decidir si entra al Tracker; ownership de 4 campos (→CG-01/02); decisión Charter (→CG-03); Census (→CG-05); re-score Axo, JD, Artifact redundante (operador) | Tracker / Kernel / Manual / Charter | pendientes de CL.44/.46 (sin filas) | DEC-07, DEC-08 | Filas creadas con IDs asignados por el operador o decisión de no registrar | Escrituras al Tracker desde un frente sin contrato |

Secuencia real: CG-06a → CG-04 ∥ CG-03 ∥ CG-01 → CG-07 → CG-02 → CG-08 → CG-06b → CG-05. CG-09 continuo (primera corrida = aplicar esta propuesta). CG-10 según DEC-08.

## 3 · Tablero
| Fase / CP | Estado | Última acción registrada | Próxima acción (grupo) |
|---|---|---|---|
| Fase 0 | CERRADA (cierre histórico pendiente DEC-13) | T0.1 verificado por GROK 2026-10-03 | Ninguna |
| Fase 1 | CERRADA (ídem) | HO-000066 pytest 178/13 | Ninguna |
| Fase 2 | ABIERTA — sin ejecutor asignado para Kernel/Manual | Charter DECISIONS-012–017 aplicado 2026-10-12 (LOG #105, sin verificador distinto) | DEC-01/DEC-02/DEC-07 → CG-01 (Kernel) y CG-03 (Charter) |
| Fase 3 · CP-3 Gate | EN CURSO — dry-run 6/5 (LOG #100) | T11 en main 2026-10-12 | Paridad T3.I + confirmar T3.O doc → CP-3 |
| Fase 3 · CP-1a --apply | BLOQUEADO por T3.X (decisión del operador) | Autorizado 2026-10-12 (LOG #102) | CG-06a → CG-04 |
| Fase 3 · CP-1b Workday CANONICAL | PENDIENTE | T3.J evidencia 2026-10-12 | CG-08 |
| Fase 3 · CP-2 LinkedIn | BLOQUEADO por B-R6 (queries no ejecutadas) | normalizador en main [V: espejo] | CG-07 |
| Fase 3 · CP-4b Sync único | PENDIENTE (deriva .47/.46; 2 IDs fuera de Census) | Census regenerado 2026-10-13 01:56 | DEC-09 → CG-05 |
| Fase 3 · CP-5 Repo | EN CURSO — PR #27 fusionado [D]; detached HEAD; deltas sin destino | HO-000104 (2026-10-13) | CG-06a (hoy) → CG-06b |
| GOV | PENDIENTE — esta propuesta sin aplicar; CHANGELOG 16 entradas | v9.22.47 (CHATGPT) | CG-09 |
| ISIM | SIN REGISTRO | v9.22.46 | DEC-08 → CG-10 |

## 4 · Bloqueos activos (detalle en LOG)
B-R1 token (LOG #97) · B-R2 sin ejecutor Kernel/Manual (PLAN T2.1/T2.2b/T2.3b) · B-R3 sin verificador distinto (LOG #105/#107; CL.45) · B-R4 ownership 4 campos (CL.44/.46) · B-R5 detached HEAD + commits exclusivos (LOG #110) · B-R6 queries LinkedIn (LOG #61/#64/#91).
Levantados o reformulados: SSH (LOG #92) · PR #27/3 implementaciones (LOG #103) · "CI" (HO-000104.P2) · MILESTONES-004 como freno general · T3.M código · T2.G pins · ubicación ARCHIVO.

## 5 · Decisiones pendientes del operador
Bloqueantes: DEC-01 ejecutor+verificador Kernel/Manual · DEC-02 alcance Manual (2a ahora / 2b después, o un solo pase v10) · DEC-03 confirmar orden CP-3→CP-1a y condición de desbloqueo f9bb/--apply · DEC-04 destino de deltas git (7552499, c0443fd, 5a37139, arena/d352bc18) y cierre T3.W · DEC-05 cierre T3.Y por HTTPS y reformulación HO-000104.P2 · DEC-06 numeración DECISIONS (T3.G, ISIM) por CLAUDE/MAIN en una ventana · DEC-07 ownership Interview/Interview_Date/Contacto/Notas · DEC-08 registrar ISIM en el Tracker · DEC-09 sync de mantenimiento antes del v10 completo · DEC-10 verificadores (incluye ¿ARENA verifica L1?) · DEC-19 criterio exacto de CP-2.
Diferibles: DEC-11 schema PLAN (Proyecto/Grupo/Checkpoint; opción COPIILOT→COPILOT) · DEC-12 semántica de Orden · DEC-13 cierre histórico sin verificador · DEC-14 grupos de T3.Z · DEC-15 pytest canónico / CI sí-no · DEC-16 mecanismo de rotación CHANGELOG · DEC-17 hito LinkedIn en Charter · DEC-18 retiro de Graph go/no-go.
(Definición completa, opciones y consecuencias: Parte 3 del entregable; al aplicarse, cada DEC resuelta se registra como fila LOG tipo Nota/Pendiente→Resuelto.)

## 6 · Nota de gobernanza
- Charter: ningún agente lo edita; propuestas = tickets CHARTER evaluados solo por CLAUDE/MAIN y aplicados solo por el operador.
- Python posee en exclusiva los campos Class B; el Interview Simulator no escribe en Notion ni en el repo y no es fuente de verdad (KERNEL §14.13).
- Un reporte de éxito de otro agente no cierra nada sin re-fetch independiente. Las entradas CHANGELOG .44/.45/.46/.47 son declaraciones hasta que un actor distinto verifique.
- Seriales solo por `allocate_vantage_serial.py next` o declaración del operador. ARENA está fuera del registro de identidades: cualquier handoff derivado de este trabajo se re-emite desde un agente registrado con parent_handoff al origen.
- Hard Blocks: única fuente Layer_1/config/hard_blocks.json (v1.1): L'Oréal, Levi's/Levi Strauss, El Palacio de Hierro; Dockers y Aéropostale NO son bloqueos.

## A · Anexo histórico — Auditoría KERNEL v10.1 / v10.2 / v10.3 (línea por línea)
Se conserva ÍNTEGRO y sin cambios el texto vigente de la página (secciones "KERNEL v10.1", "v10.2", "v10.3"). Acción propuesta: moverlo bajo un toggle "Histórico — no editar"; su contenido ya no es insumo de ninguna tarea abierta (el re-key v10.4 lo sustituyó, T2.N). No se reproduce aquí para no duplicarlo; el DRY RUN de CG-09 debe mostrar que el bloque se mueve, no se reescribe.