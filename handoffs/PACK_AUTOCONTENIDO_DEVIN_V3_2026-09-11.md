# ENTREGA ÚNICA — Paquete autocontenido sesión Devin V3 (Tracker refactor)

**Serial:** DEVIN-20260911-03 · **Fecha:** 2026-09-11 · **De:** Mauricio Meyrán vía auditoría Arena · **Para:** Devin (chat nuevo, sin contexto previo)
**Repo:** `mauriciomeyran/VANTAGE` · **`main` verificado:** `467af9c8bdef1b120ba1fba095a35931624f6236` · **Lectura:** este archivo es TODO tu contexto. Si algo no está aquí, decide con el criterio del pack y regístralo como pregunta abierta (§D5). Prohibido pedir contexto adicional en tiempo real.

## Orden de lectura y tarea en un párrafo

Lee §0 → A → B → C → D. Tu tarea: implementar el **delta V3 (F1–F15, §B)** sobre tu diseño V2. V3 se entrega como **diseño ejecutable**: secciones corregidas + cada sketch de código como archivo real importable en tu rama + `pytest` corrido con output. Si V3 sale limpio, se aprueba implementación. Nada a `main` (tú abres PR, Mau mergea), nada a Notion de producción.

## §0 — PASO 0 OBLIGATORIO: entorno antes que nada

0.1. Ejecutar y pegar output literal en tu handoff:
`git fetch origin main && git rev-parse origin/main && git log --oneline -1 origin/main`
0.2. El SHA debe ser `467af9c8…` o descendiente fast-forward. Si diverge, parar y reportar.
0.3. Rama FRESCA desde ese SHA: `git checkout -b devin/<nombre-nuevo> <SHA>`. Pegar comando + output.
0.4. **Prohibido** basar trabajo o mergear `devin/plan-refactor-tracker-v2` (@`56a9f35`, linaje pre-Sep-10, delta vs main 311 archivos/−687K). Solo lectura de referencia: `git fetch origin devin/plan-refactor-tracker-v2 && git show FETCH_HEAD:handoffs/PLAN_REFACTOR_TRACKER_V2_2026-09-11.md`.
0.5. Handoff sin transcript §0 = rechazo automático (R1).

## §A — CANON TÉCNICO (condensado vinculante; lo no decidido aquí y no pedido en §B no se rediseña)

**A1 Objetivo + prohibiciones.** Reemplazo completo del pipeline Tracker (ingesta→scoring→gate→cleanup→terminales) gobernado por un solo mapa de flujo. Prohibido: entradas nuevas a listas existentes, fases numeradas nuevas, "sincronizar" el fork Dashboard (se RETIRA), dos writers con semántica divergente. Aceptación global: cada transición de Status tiene exactamente un gate, exactamente una lista de protección, y respeta ediciones manuales recientes como máxima prioridad.
**A2 Mapa único.** Un módulo (`tracker_flow.py`, `Layer_1/scripts/`): enums cerrados (desconocido→REVIEW+WARN, jamás operativo); matriz `(origen,evento)→destino`; predicado único `is_mutable` consultado por TODOS los writers; UN gate de archivo `(razón,evidencia,actor,timestamp)` + escritura atómica `{Status,Next_Action,Gate_Decision,Notas+=}` con `generate_archive_notes()` una sola vez; orden: protección-manual → terminalidad → elegibilidad → cómputo.
**A3 Vocabularios DECIDIDOS (Title Case, inamovibles; resuelve F8: el enum ES post-migración).** Status (12): `Objetivo, Exploratorio, Por Revisar, Postulando, Postulado, En Proceso, Negociando, Sin Respuesta, Contratado, Expirada, Rechazado, Retirado`. Next_Action (9): `Optimizar, Seguimiento, Preparación Entrevista, Revisión, Investigar, Post-Mortem, Archivar, Reparar URL, Verificar JD`. Gate_Decision (SCREAMING, excepción técnica): `CREATE, BLOCKED, APPLIED, REJECTED, REVIEW, EXPIRADA`. `Status=Archivar` no existe; `Holding` vacía=vacía (sin placeholder); `fetch_status`+`Fetch` fusionados; `Source_Type` sin trailing space; fantasmas (`Repetida, RAW, Nueva`, `filled`, `Fuente` legacy) podados con migración fila-por-fila.
**A4 Decisiones locked (implementar como se enuncia).** Ventana atómica con orden freeze→merge→patch; híbrido B7 (auto en operativas no-tocadas, propose-log idempotente en humanas/vivas, consumidor tidy + APROBAR_WRITE); `normalize_record()` como frontera obligatoria shapes-API→plano (F1); UN camino `evaluate→propose/execute→archive_gate` (F2); UNA definición de "tocado-por-humano" = autor-humano + tiempo (F3); diff sobre plano con tipos preservados (F4); regla manual `HUMANO(cualquier→cualquier dentro del enum)=válido` (F6); gate REVIEW `Por revisar` diseñado de verdad o reversión explícita a opción-(b) (F7); `is_valid` cableado en `normalize_record` (F10); guard compuesta = field-block Class-B (semántica vigente) AND `is_mutable` (F11); survivor `Contratado` primero siempre (F12); `batch_operations` se RETIRA (no convertir); `consolidate` sin trash físico sin confirmación; `auto_archive.py` deprecado; `Aéropostale` no es hard block; seriales `HO-######`/`DEVIN-*`.
**A5 Restricciones standing (texto completo, vigentes).** Cero escritura/lectura-con-token-real a Notion de producción. Fixtures ≥15 filas + Notion fake; `pytest` sin red ni credenciales. Cero `input()` en pipeline. Cero secretos en repo. Cero daño a datos (update-in-place por `page_id`, ARCHIVO intacto, export pre-migración). PR lo abres tú, lo mergea Mau. Frases de conformidad obligatorias (§D6).

## §B — DELTA V3: F1–F15 ÍNTEGROS (implementar cada fix como se especifica)

- **F1. [SISTÉMICO] Frontera de normalización.** Todo `tracker_flow` asumía records planos pero el orquestador alimenta shapes API → ninguna protección disparaba; `_is_human_edit` comparaba dict vs set de strings. Fix: `normalize_record()` obligatoria al construir `memory_state` (plano `{Status:str,…}` + `last_edited_by_id` extraído); predicados operan solo sobre plano.
- **F2. Tres rutas de archivo → una.** Matriz sin llamadores + `execute_transition_with_propose_log` + `archive_gate` paralelos; `execute_transition` pisaba Notas y omitía campos. Fix: un solo camino `evaluate_transition → propose/execute → archive_gate`; `execute_transition` se elimina o delega; fases 3/7 del orquestador llaman a ese camino.
- **F3. Híbrido B7 roto + propose-log sin idempotencia.** Check time-only sin autor (PLAN:316) → writes del bot cuentan como humanos → nada auto-ejecuta. Fix: UNA definición (autor-humano+tiempo); skip si ya existe `[PROPOSE]` idéntica abierta; declarar go/no-go (corte bloqueado hasta poblar bot-IDs) o auto-discovery vía `users.me()` + IDs extra por config (recomendado).
- **F4. Crash en diff + diff-numérico eterno.** `extract_value(v)` con strings (PLAN:728) → `AttributeError`; write-through mezclaba shapes; Score `str vs number` → rewrite cada run. Fix: diff sobre plano normalizado con tipos preservados; `extract_value` acepta de verdad ambas shapes.
- **F5. Typo + listas paralelas.** `Status.RETRIRADO` (PLAN:82) impide importar. A2 redefine terminales como literales (PLAN:1098) y no usa `is_mutable`. Fix typo; A2 importa `PROTECTED_STATUSES` y delega.
- **F6. Matriz incompleta + regresión manual.** Sin productor de `Objetivo`-limpio; sin piernas a `Negociando/Sin respuesta/Contratado`, sin `En proceso→Rechazado`, sin `Exploratorio`; regla manual eliminada. Fix: piernas faltantes + pre-check `HUMANO(any→any en enum)=válido`.
- **F7. REVIEW-block claim-sin-código.** Q-1 describía un check inexistente, infactible con firma `(record,actor)`. Fix: diseña el gate (firma con `field` o fase que salta `Por revisar` + resolución `→Objetivo`) o revierte a opción-(b) explícitamente.
- **F8. Enum↔tabla literales distintos (corrupción).** `Por revisar`×7 vs `Por Revisar`§3.2 (igual `En proceso/Sin respuesta/Preparación entrevista`): PATCH-Title + writes-sentence = options duplicadas auto-creadas. Fix: un solo literal por valor (§A3); tabla/migración referencian miembros, no strings.
- **F9. Despliegue, 5 defectos.** (a) "Claude mergea vía MCP" (PLAN:884/886/1018) → Devin abre PR, Mau mergea. (b) Rama de código separada de rama de docs. (c) Orden freeze→merge→patch (§A4). (d) Rollback: sintaxis válida + `migrate_schema_properties.py --rollback` scripteado (restore reescribiendo valores viejos recrearía options duplicadas). (e) Disposición de filas en valores eliminados (`Status=Archivar`-rows→?; mapping `fetch_status{aggregator,career_page,filled}→Fetch`) — diseñar con mapping explícito.
- **F10. Enum sin enforcement (B11 vivo).** `is_valid` sin llamadores → desconocidos procesados como operativos. Fix: `normalize_record` valida; desconocido → REVIEW + skip + WARN.
- **F11. A4 regresión D-002.** Guard v2 solo record-level, pierde field-blocking Class-B. Fix: field-block (vigente) AND `is_mutable`; corregir anidamiento `{"properties":…}`.
- **F12. Survivor + dedup.** `Contratado` rankeado bajo `Sin respuesta` (PLAN:1079) → Contratado pierde. Fix: Contratado primero; keep-o-fix explícito sobre keyword-set/fuzzy thresholds; solo-no-survivors flaggeados.
- **F13. Rama stale, prohibido mergear.** `devin/plan-refactor-tracker-v2` cuelga de linaje pre-Sep-10 (delta 311/−687K). Implementación en rama fresca (§0); esa rama jamás se mergea.
- **F14. Patrón "corregido"-sin-contenido.** R6 "Aplicada" sin conteos/idempotencia; R7 "log movido" falso (sigue en `is_valid`, PLAN:77); B8-REVIEW; A2-guard. Fix procesal: tabla de trazabilidad `ítem → §/líneas exactas pusheadas`; claim sin cita = no revisado (§C2).
- **F15. A3/A5 delgados.** A3: `_move_to_archivo` "requiere confirmación" sin mecanismo (quién pide/concede/dónde espera); batch→RETIRAR (§A4). A5: exigir mapa cobertura `test↔celda/rama` (cuerpos en implementación); fake debe espejar `client.pages.update` o documentar adaptador.

## §C — CONTRATO DE VERIFICACIÓN (vinculante; prevalece en mecanismo)

**C1 Evidencia de ejecución pegada.** Por módulo nuevo/modificado: comando + output completo de `python3 -c "import <modulo>"`. Tracebacks íntegros + fix + re-ejecución. "Funcionó/verificado" sin output = sin valor; el ítem cuenta como NO resuelto. Todo sketch existe como archivo real en la rama.
**C2 Trazabilidad.** Una fila por hallazgo declarado resuelto: `| ID | archivo:línea(s) exactas | diff | evidencia |`. **Resuelto sin cita verificable = automáticamente NO resuelto.** Citas falsas invalidan la fila.
**C3 Tests reales.** Comando `pytest` + output completo (pass/fail/error). Tests citados = archivos existentes. Mapa `test↔ID(s)` obligatorio. Default: fakes, cero red.
**C4 Diffs reales.** Cambios vs V2 como `git diff` (pegado ≤200 líneas o archivos en rama). Prosa = epígrafe, nunca sustituto. "Conforme/ajustado" sin diff = nulo.
**C5 Rechazo automático (R1–R8).** R1 sin transcript §0 · R2 rama reusada/stale · R3 "resuelto" sin fila C2 · R4 evidencia parafraseada · R5 tests nombrados sin archivo/output · R6 "conforme" sin diff · R7 violación §A5 · R8 sin frases §D6 textuales.

## §D — ENTREGA Y CIERRE

**D1** Rama fresca §0; handoff de cierre como `handoffs/HANDOFF_DEVIN_V3_2026-09-11.md` en tu rama + PR contra `main` (lo mergea Mau).
**D2** Definición de hecho: F1–F15 implementados + C1–C4 completos. Si algo no cabe en una sesión: F1–F6+C completos como mínimo, resto como diseño detallado declarado abierto (no código a medias).
**D3** Referencias backup (solo si lo inlineado es insuficiente): `git fetch origin arena/01a08e60-vantage` → `CONTRATO_DEVIN_REFACTOR_TRACKER_2026-09-11.md` (alcance), `REREVIEW_DEVIN_V3_2026-09-11.md` (F1–F15 + contexto), `AUDITORIA_TRACKER_E2E_2026-09-11.md` (radiografía). Lo inlineado prevalece en caso de duda.
**D4** Nomenclatura: IDs canónicos B-/A-/R-/F- para trazabilidad; serial de tu handoff `DEVIN-20260911-NN` siguiente libre.
**D5** Preguntas abiertas (formato `Q-n: pregunta | decisión tomada | alternativas descartadas | dato de cierre | impacto si se revierte`): solo Q-G1 heredada (¿quién aprovisiona Notion no-prod para integración? default: no se propone, fakes) + las que surjan. No bloquean D2.
**D6 Frases de conformidad (textuales, ambas obligatorias):** "Ninguna escritura a Notion de producción fue realizada ni intentada en esta sesión." + "Declaro bajo el contrato DEVIN-20260911-02 que cada ítem marcado resuelto tiene cita archivo:línea, diff visible y evidencia de ejecución pegada; lo que no tenga las tres, no está resuelto."
