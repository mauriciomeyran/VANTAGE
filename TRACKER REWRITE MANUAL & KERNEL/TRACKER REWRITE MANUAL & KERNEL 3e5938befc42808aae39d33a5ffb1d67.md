# TRACKER REWRITE MANUAL & KERNEL

Versión: N/A
Status: Active
URL: https://app.notion.com/p/TRACKER-MANUAL-KERNEL-3e5938befc42808aae39d33a5ffb1d67?source=copy_link
Page ID: 3e5938befc42808aae39d33a5ffb1d67
Fecha de actualización: oct 12
Fecha de creación: 24 de septiembre de 2026 7:32

<aside>

**Antes de leer este Tracker:** este documento es el registro operativo de *cómo* se está ejecutando la reconciliación v10 (tareas, decisiones, auditorías, changelog).

El **por qué** de cada decisión estructural que aparece aquí — y los fracasos que ya se intentaron y no funcionaron — viven en `V | PROJECT CHARTER` (`CHARTER:DECISIONS`, `CHARTER:FAILURES`). Si una tarea de este Tracker te hace preguntar “¿por qué estamos haciendo esto así?”, la respuesta probablemente ya está en el Charter, no hay que reconstruirla desde cero.

Todo cambio al propio Charter se solicita vía ticket Task Tracker tipo `CHARTER`, evaluado por CLAUDE/MAIN (`SP:BOOTLOADER-002`) — nunca editado directamente desde este Tracker ni por ningún otro agente.

</aside>

# CONTEXTO

## Por qué esto hace sentido — el hilo completo de la semana

1. **El síntoma que arrancó todo (24-sep):** llegó un documento de auditoría externa con una “Cédula de Reconciliación” fabricada (`v9.21.40`, PASS sin fuente verificable). Eso no era un problema de KERNEL/MANUAL — era un problema de **cómo verificar diagnósticos externos**. De ahí nació la regla que gobernó todo lo demás: ningún hallazgo se acepta sin verificación 1:1 contra fuente primaria real (`CHARTER:DECISIONS-006`, `CHARTER:FAILURES-003`).
2. **Por qué Track Alpha/Track Beta, y por qué en paralelo:** la documentación y el código llevaban semanas divergiendo sin que nadie lo notara (`Dedup_Flag` select↔︎checkbox es el caso de referencia, `CHARTER:DECISIONS-007`). Corregir solo la norma sin verificar el código, o viceversa, es el patrón que ya falló antes (`CHARTER:DECISIONS-008`).
3. **Por qué tantos contratos de sesión con tantos agentes distintos** (Perplexity, Arena, Copilot, Mistral, Littlebird, Devin, GROK): cada uno aportó una pieza del mismo rompecabezas de verificación, con las mismas prohibiciones explícitas (cita verificable, nada de “PASS” sin evidencia) — `CHARTER:NON-NEGOTIABLES-003` y `005` en acción, repetidas veces.
4. **Por qué el Charter nació a media semana (29-sep):** el patrón de “saltar entre sesiones e instancias erosiona la continuidad” se volvió doloroso de forma concreta — la misma pregunta se le hizo a distintos agentes en distintos momentos sin que ninguno recordara la respuesta anterior. `CHARTER:MILESTONES-001` cierra esas preguntas con tabla de
evidencia, para que esto no vuelva a pasar.
5. **Por qué hubo que separar T2.2/T2.3 en sub-tareas (2-oct):** una nota de alineación puntual (28-sep, lote Perplexity) quedó registrada como si fuera el cierre completo de la redacción v10. Nadie mintió — fue una ambigüedad de “¿qué significa Resuelto aquí?” propagada sin cuestionarse. Variante gemela de `CHARTER:FAILURES-005` (documentación que describe un estado que ya no es cierto) — aquí no fue código retirado, fue una tarea compuesta tratada
como atómica.
6. **Por qué Fase 3 arrancó con T3.A antes que el resto (T3.A ya está Resuelto, 191 passed):** T3.A (protección de estados terminales) es prerequisito explícito de todo `-apply` futuro. Avanzar Fase 3 antes de cerrar T3.A violaría el mismo principio de “no escribir sobre premisas no verificadas” que motivó todo el proceso desde el punto 1.
7. **Estado:** checkout canónico `origin/main` en `23e1e1e`, limpio y sincronizado (ahead/behind `0/0`).
- **Limpieza local aplicada:** eliminadas `main` (`7552499`) y `devin/vantage-sync-r4` (`c0443fd`). Se preservó la rama local Copilot `mauriciomeyran/copilot-vantage-sync-warmup-validation` (`5a37139`) y las referencias remotas.
- **Verificación disponible:** `Layer_1/tests/test_vantage_sync.py` tuvo 65 tests pasados en una ejecución previa. No se confirmó CI post-merge ni se repitió la suite después de la limpieza.
- **Pendientes registrados en PLAN DE TRABAJO:** HO-000104.P1 decidir si rescatar o descartar commits exclusivos de ramas eliminadas; HO-000104.P2 confirmar CI de `23e1e1e`; HO-000104.P3 repetir suite desde `origin/main` si se requiere validación posterior al merge.
- **Registro de cierre:** [HO-000104 — Reconciliation Log](https://app.notion.com/p/HO-000104-Cierre-de-sesi-n-VANTAGE-Git-2026-10-13-3f8938befc428149a664d8b3f1907bae?pvs=21).

---

# PLAN DE TRABAJO

Plan de **3 Fases paralelas por tracks de trabajo**: **Track Alpha** (Normativo/KERNEL) y **Track Beta** (Operativo/Scripts/Código) corren en paralelo durante Fase 1 y 2, convergiendo en Fase 3.

```
FASE 1: CONVERGENCIA & CONGELAMIENTO (PARALELO)
├─ Track Alpha: Reconciliación de Contratos y Normas (KERNEL)
└─ Track Beta: Auditoría de Código, Schemas y Scripts (MANUAL / RUNTIME)
                                │
                                ▼
FASE 2: REESTRUCTURACIÓN Y DESACOPLAMIENTO (PARALELO)
├─ Track Alpha: Redacción de KERNEL v10 (Normativo estricto)
└─ Track Beta: Redacción de MANUAL v10 + Extracción de Referencias
                                │
                                ▼
FASE 3: SANIDAD, VALIDACIÓN & SYNC NOTION (CONSOLIDACIÓN)
└─ Track Único: Verificación de Paridad, Sync de vdoc/vsync y Deployment
```

[PLAN DE TRABAJO ](TRACKER%20REWRITE%20MANUAL%20&%20KERNEL/PLAN%20DE%20TRABAJO%20870e24ea86174b6abf509d27e8c82592.csv)

---

# TABLERO

<aside>

**Regla:** Esta sección se lee al abrir sesión y se actualiza al cerrar. Un hecho, un lugar:

- Tareas → PLAN
- Eventos y decisiones → LOG
- Defectos → Bug Tracker
- Cambios aplicados → Changelog

Nada pasa a Resuelto sin evidencia y sin verificación de un actor distinto del ejecutor. 

Al cierre de sesión, cada agente registra sus cambios aplicados en [V | CHANGELOG](https://app.notion.com/p/V-CHANGELOG-390938befc4280e7b429d7d730339353?pvs=21); el Tablero solo recibe una bullet-puntero con la versión.

</aside>

| Fase | Estado |
| --- | --- |
| 0 | Cerrada. 8 de 9 filas sin `Verificado_Por` (verificación independiente pendiente). |
| 1 | Cerrada. 8 de 9 filas sin `Verificado_Por` (verificación independiente pendiente). |
| 2 | **Kernel v10.3 + re-key v10.4 ya vivo** (97 IDs; export de 564 líneas). **T2.O aplicado** en el Kernel vivo (E1–E13, Changelog v9.22.32), pendiente de verificación independiente (ChatGPT); quedan T2.O-b (pase NORM, tabla de 12.1, cifra "8 auditados" de 04.5) y el Bloque B de CS-VERIFY-01c (T2.N). T2.2b/T2.3b Pendiente (paralelo autorizado). T2.CHARTER: dictamen emitido, falta confirmar DECISIONS-012. T2.D: Kernel aplicado por nombres (B1=A); faltan SP, Manual y la cifra "8 auditados" de 04.5. **Charter actualizado 2026-10-12** (DECISIONS-012 a 017, FAILURES-006, NON-NEGOTIABLES-010/011, MILESTONES-006/007; re-fetch verificado por MAIN): T2.R en progreso (falta verificador distinto), T2.CHARTER parcial (falta GATE-MUTABILITY), T2.Q en progreso (§6/§7 refrescados; falta sync del Census en Notion). Los 10 IDs nuevos ya están en CENSUS_SPEC (main). |
| 3 | T3.A Resuelto (191 passed; f9bb abierto). [T3.Ca](http://T3.Ca) Resuelto; T3.Cb Pendiente. **T3.1 en progreso** (el Census en Notion ya refleja los 26 IDs; faltan registry, ALIASES y citas legacy). **T3.G** (retiro de Graph) nuevo. T3.B Pendiente. T3.E en progreso. T3.R Resuelto (higiene Git P0); T3.S, T3.T y T3.U Pendientes (2026-10-10). HEAD remoto 2026-10-10 23:50 = `9fb1a23`. **Actualización 2026-10-12:** HEAD remoto = `7ec67bb` (PR #26 fusionado: T-3, T-5, T-6, T-11, T-12, T-13/13b); Layer_1 351 passed en la rama de Arena. T3.O en progreso (T11 aplicado; dry-run 6 BLOCKED / 5 limpio), T3.L en progreso (dry-run E2E hecho; falta el primer --apply), T3.S reabierto (3 worktrees de Copilot y ramas de agentes reaparecidas). Nuevas: T3.W (frente vantage-sync), T3.X (token expuesto), T3.Y (SSH), T3.Z (limpieza de la raíz de main). |

#### ÚLTIMA ACCIÓN

Oct 12, 26 (CLAUDE/MAIN · sesión 2026-10-11→12)

*Consolidación de ramas (9 archivadas con tag), PR #26 fusionado (T-3, T-5, T-6, T-11, T-12, T-13/13b), dry-run de Workday con T11 y actualización del Charter. El histórico formal vive en V | CHANGELOG; la entrada de esta sesión está pendiente de redactar. Este bloque solo resume y se actualizó a mano a partir de los adjuntos del 2026-10-12.*

- **Pendientes (actualizado 2026-10-12 CLAUDE/MAIN):**
1. **Token ntn_ expuesto** en Dashboard/archive/legacy_express_node/server.js:13: rotar y retirar el archivo (T3.X). Bloquea el primer --apply.
2. **Primer --apply de Workday** (autorizado por el operador, no ejecutado): desde main actualizado, tras confirmar el dry-run 6 BLOCKED / 5 limpio y con re-fetch en Notion (T3.L).
3. **SSH sin identidades** (T3.Y): cargar la llave o cambiar origin a HTTPS; mientras tanto vgit no puede empujar y el fetch falla en silencio.
4. **Frente vantage-sync:** elegir una sola implementación entre el PR #27, arena/d352bc18-vantage y el WIP de Copilot (T3.W); archivar devin/vantage-sync-r4 con tag.
5. **T3.S reabierto:** 3 worktrees de Copilot y ramas de agentes reaparecidas; hábito de poda tras cada sesión (ticket CHARTER si DECISIONS-016 lo requiere).
6. **Charter, pendientes de §7:** alta de los 10 IDs nuevos en el Census de Notion, citas KERNEL:GATE-MUTABILITY (T2.CHARTER), FAILURES-001 («KERNEL vigente» → hard_blocks.json), fila 3b del Hito 1 (T-6 ya está en main) y corregir DECISIONS-017 y el Hito 7(b) a «aplicada en main (PR #26)».
7. **Limpieza de la raíz de main y de Archive/** (T3.Z), decisión del operador por grupo.
8. **T3.I paridad levis matcher↔JSON** (no reabrir sin evidencia nueva); la re-promoción de LinkedIn va después, una sola vez (SHA del registry f7fa0513 vs matcher 5ee2c5bb).
9. Estrategia real de backup de Notion (notion_[backup.py](http://backup.py) inexistente), timeout de push en git_[sync.py](http://sync.py) (30 s) y destino de ~/Applications/VANTAGE.
10. Rotación del CHANGELOG vivo al ARCHIVO (13 entradas vs límite de 10) y entrada de esta sesión.
11. Residuo de redacción en MANUAL §8.1 (bloques «¿Qué es L4?» y «no quieres esperar al siguiente horario»).

Cerrados el 2026-10-11/12: 9 ramas archivadas con tag y borradas (incluidas #4, #6 y recovery/scope-bajo-gate), PR #26 fusionado, T11 aplicado (roles de tienda), binarios Dashboard/*.db fuera del índice (T3.V, según KM), Charter actualizado, W1–W3 escritos por KM.

---

#### **PRÓXIMA ACCIÓN**

1. **Operador:** rotar el token ntn_ (T3.X); después ARENA retira server.js de main.
2. **Operador:** resolver SSH (T3.Y), volver a main, confirmar el dry-run 6 BLOCKED / 5 limpio y ejecutar el primer --apply acotado (T3.L); MAIN verifica con re-fetch en Notion.
3. **Operador:** decidir el dueño del frente vantage-sync (T3.W) y archivar devin/vantage-sync-r4 (incluyendo el commit local c0443fd).
4. **KM:** reabrir T3.S (DRY RUN pendiente de APROBAR_WRITE) y registrar el cierre de F1 con evidencia fechada; después K2 (Tests = 31 passed), delta de K3 y K4.
5. **MAIN:** ticket CHARTER para DECISIONS-017 y Hito 7(b) («aplicada»), FAILURES-001 y fila 3b del Hito 1; confirmar KERNEL:GATE-MUTABILITY.
6. **ARENA (sesión nueva, contrato corto):** retirar server.js; sync del Census de Notion (nombres, orden y anchors) cuando el operador lo pida.
7. **Operador:** decidir T3.Z (raíz y Archive/), la política de poda tras cada sesión y la entrada de CHANGELOG.
8. T2.O: verificación independiente + T2.O-b (pase NORM).
9. T3.G: PR retiro Graph (separar entity index) → DECISIONS-018 (la 013 pasó a hard_blocks.json).
10. T3.B: f9bb levantado solo para el primer apply acotado; aliases vl1* sin evaluar.

#### **RESUELTOS**

- ~~Dedup_Flag~~ → checkbox confirmado y propagado.
- ~~PR #14~~ → mergeado `93c548e`; pytest 191 passed.
- ~~T2.2/T2.3 contradicción~~ → dividido (nota puntual Resuelta + trabajo real Pendiente).
- ~~Jerarquía de dedup~~ → L1>L2>L3 (código = norma; Kernel alineado).
- ~~Sync v9.22.29 + vgit~~ → PASS (operador + verificación GROK 2026-10-03).
- ~~Pin vantage-cv-b~~ → v10.2.1 / 2026-09-28 confirmado en SP vivo.
- ~~Hash del Charter~~ → el manifest usa otra base de hash (tampoco coincide para el Kernel); no es incidencia.
- ~~Kernel v9 residual~~ → movido a `Archive/Documentación/` (commit pendiente, T3.H).
- ~~T2.O (pase único del Kernel)~~ → aplicado 2026-10-04 (E1–E13); verificación independiente pendiente.
- ~~Referencias a layer_1_[run.py](http://run.py) en el Kernel~~ → corregidas en 03.4, 04.5, 05.8 y 06.13 con evidencia de Terminal.
- ~~Cifra de documentos «Census reconciliado»~~ → **reabierta**: el Census coincide, pero Kernel 04.5/14.3/14.4/12.3, SP y Manual siguen con cifras distintas. Ver T2.D.

**Resuelto 2026-10-10:**

- ~~PLAN-3F-3 (Dockers en EXCLUDED_SENDERS)~~ → retirado en efe8c3d; Layer_3 11 passed.
- ~~P0 de higiene Git~~ → 8a8fe6c: sqlite-memory.db* fuera del índice y en .gitignore, CSV retirado (T3.R).

**Resuelto 2026-10-11/12:**

- ~~Conteo de la suite (311 vs 315)~~ → 321 passed en main (Terminal 2026-10-11); 351 en la rama de Arena.
- ~~Ramas remotas vestigiales~~ → 9 archivadas con tag y borradas (2026-10-11); otras reaparecieron (T3.S reabierto).
- ~~#4 arena/01a00e43 y #6 arena/01a0c6c6~~ → borradas con tag archive/*.
- ~~recovery/scope-bajo-gate~~ → archivada sin integrar; la intención se cubrió con T11.
- ~~Hallazgo ALTA «CLEAN sin token»~~ → corregido en main (e58dce1), con test.
- ~~PR #26~~ → fusionado (7ec67bb).
- ~~T3.O, parte de código (roles de tienda)~~ → T11 en main; dry-run 6 BLOCKED / 5 limpio. Falta alinear Manual §10.
- ~~Contradicción de la línea 21 de hard_blocks.json~~ → T-12 en main.
- ~~Dry-run E2E Workday/Chanel~~ → ejecutado, sin escrituras en Notion.
- ~~Binarios Dashboard/*.db rastreados~~ → fuera del índice (T3.V, según KM); el contador SQLite sigue rastreado por decisión.
- ~~Charter~~ → actualizado el 2026-10-12 (DECISIONS-012 a 017, FAILURES-006, NON-NEGOTIABLES-010/011, MILESTONES-006/007).

#### **BLOQUEOS ACTIVOS**

- f9bb: el operador respondió 'Ok' a desbloquear --apply para el primer apply acotado de Workday (2026-10-12), condicionado a token rotado, main actualizado y dry-run 6 BLOCKED / 5 limpio. Para cualquier otro --apply no se definió alcance.
- **Token ntn_ expuesto** (T3.X): bloquea el primer --apply.
- SSH sin identidades (T3.Y): vgit no puede empujar.
- ARCHIVEROS: exclusión de `vversions --length` pendiente de ticket de código (T3.Cb); además `length_baseline.json` tiene CENSUS=0.
- bd46 / 4d08 siguen Abiertos (cierre exige verificador distinto).
- Verificación independiente pendiente: T2.N, T2.H, T2.I, T2.K, T2.K2, T3.E, T2.R, T3.O (parte de código) y las 8 filas Resuelto sin `Verificado_Por` de Fase 0/1.

#### **DECISIONES ABIERTAS**

- Snapshot de SQLite en el historial público (ae25caf): esquema sin filas, WAL sin examinar; sin reescritura de historia.
- Binarios: dashboard.db y dashboard_instances.db ya no se rastrean (T3.V); el contador SQLite sigue rastreado por decisión. Falta definir su política de commit o respaldo.
- DECISIONS-012: registrada en el Charter el 2026-10-12; falta confirmar explícitamente la razón y el descarte de v10.1/v10.2.
- DECISIONS-018 (retiro de Graph): se registra después de mergear el PR (la 013 pasó a hard_blocks.json).
- Dueño del frente vantage-sync: PR #27, arena/d352bc18-vantage o el WIP de Copilot (T3.W).
- Limpieza de la raíz de main y de Archive/ (T3.Z), incluido qué hacer con los CVs .indd en un repo público (D1).
- SSH o HTTPS para origin (T3.Y).
- Valor de cierre del Tasks Tracker (Hecho o Completado) para T2.R.
- Corpus Bloque 06: este Tablero lo da por retirado, pero las sesiones de MAIN y KM aún lo ven con Dockers y Aéropostale (por verificar).
- Hábito de poda de ramas y worktrees tras cada sesión (DECISIONS-016).
- Pin de `session-open`: v1.2.0 en la Skill Library de Notion, el repo dice v1.1.0.
- `Prioridad_Auto`: sin dueño confirmado.
- Kernel 06.13: confirmar si F3.5.1 es NAD vencido (la lista de causas se retiró del texto por falta de evidencia).
- Script Library: 6 scripts registrados; fix_cvb_tags.sh Deprecado (aceptado).

#### **CERRADAS**

- El repositorio permanece público (D1, 2026-10-10).
- Scope Bajo → BLOQUEADO también con Pivote + señal VM, como en PR #25; recovery/scope-bajo-gate (b5a4d2e) queda fuera de main (D4).
- No existe servidor de seriales; único modo = `vserial` por Terminal.
- Jerarquía de dedup = L1>L2>L3.
- Versión fundacional v9.22.30 (el Change Log está en v9.22.32 hasta el próximo `vversions --sync`).
- Perplexity y Mistral = MCP-Notion con fallback GitHub (decisión 2026-10-03; se escribe en T2.O).
- auto_archive.py deprecado (decisión 2026-10-03).
- T2.D: conjuntos nombrados, sin cifra suelta (B1=A, 2026-09-28).
- El objetivo del repo es «sin ramas vestigiales», no «sin histórico» (2026-10-11); el historial vive en tags `archive/<rama>`.
- Seriales: los emite el operador, operador único; sin riesgo de repetición (2026-10-11).
- Skills: rige el `.md` que el operador adjunta en el turno; las copias residentes no son riesgo (2026-10-12, DECISIONS-015).
- Roles de tienda sin alcance estratégico: bloqueados en la ingesta L1 (2026-10-11, DECISIONS-017).
- Dockers fuera de Hard Blocks; hard_blocks.json es la fuente ejecutable única (2026-10-07, DECISIONS-013).
- Se borran todas las ramas de Arena de la consolidación (2026-10-11).
- LinkedIn live queda fuera del primer apply; su navegador se ajusta en la app del agente, no en el repo (T10).

# RECONCILIATION LOG

[RECONCILIATION LOG](TRACKER%20REWRITE%20MANUAL%20&%20KERNEL/RECONCILIATION%20LOG%20087d7551088d4b8494144098f4f9199e.csv)

# NOTA DE GOBERNANZA

## Porque esta versión es más corta

La versión anterior de este documento incluía las auditorías completas de PERPLEXITY y CHATGPT en su totalidad (≈3,160 líneas de las ≈3,345 del documento). Esa prosa completa sigue existiendo y es consultable — vive archivada como fuente, no se perdió — pero no pertenece a la página operativa que alguien abre para saber “¿dónde estamos?”. Lo que sí
pertenece aquí es el veredicto accionable de ambas auditorías, porque es lo único que cambia una decisión de ejecución:

> **CHATGPT es el plan de construcción; PERPLEXITY es el informe de riesgos. Usa ambos: CHATGPT para decidir qué sección va a qué bloque, PERPLEXITY para validar que no estás moviendo una contradicción activa sin resolverla primero.**
> 

**Mapa de reescritura (de CHATGPT, resumen ejecutable):**

- KERNEL v10: 12 secciones — Propósito → Invariantes → Actores → Arquitectura (con Runtime elevado a 1er nivel, no enterrado en DOCUMENTATION) → Contrato de Datos → Gate Decision → CV Golden Rules → Naming Convention → Data Flow (sección central, no periférica) → Evolution (sin funcionar como archivo histórico) → Excepciones → Apéndices normativos mínimos.
- MANUAL v10: reestructurado por runbooks tácticos (Cuándo usar → Precondiciones → Entrada/Salida → Comando → Output esperado → Triage), ** Weekly Flow por objetivos (Discovery, Gate Evaluation, Recovery, CV, Housekeeping) en vez de calendario rígido, Script/Skill Glossary extraídos a `SCRIPT_REFERENCE`/`SKILL_REFERENCE` independientes.

**Los 10 riesgos de PERPLEXITY a validar antes de mover cada bloque** (no listados aquí en detalle — ver el documento de auditoría original archivado, o pedir a CLAUDE/MAIN que los recupere puntualmente cuando se vaya a tocar la sección correspondiente del rewrite).

Si necesitas releer el detalle completo de cualquiera de las dos auditorías (metodología, matriz sección-por-sección, hallazgos individuales), están archivadas en `[pendiente: operador define ubicación — sugerido: subpágina "AUDITS — Archivo" bajo este mismo Tracker, o en el propio repo bajo`Documentación/ARCHIVE/`]`.

# KERNEL V10

## AUDITORÍA LINEA POR LINEA

## 0. Declaración de alcance

Recibí **tres paquetes de importación** (v10.1, v10.2, v10.3) junto con el export fuente (`V | KERNEL.pdf`, tratado como insumo 1/Kernel.md). El prompt indica que normalmente se audita **una** variante, pero dado que las tres fueron entregadas como documentos de la conversación, audito **las tres por separado**, aplicando a cada una el checklist que le corresponde según la tabla de política de identidad. Ninguna de las tres omite su declaración de variante (las tres la declaran en el comentario HTML inicial) → no aplica el NO-GO bloqueante por "variante no declarada".

**Hallazgo transversal (afecta a v10.1, v10.2 y v10.3 por igual):** el capítulo `KERNEL:EXCEPTIONS` (bullets: Bypass de URL, Housekeeping sin APROBAR_WRITE, Graph/Backlinks=0, ARCHIVEROS, Resoluciones B-xx) **no tiene correspondencia verbatim en el export fuente entregado** (`V | KERNEL.pdf` termina en el capítulo 17 KERNEL:EVOLUTION, "Linaje Histórico", sin contenido posterior). No puedo determinar si esto proviene de una parte del export vivo no capturada en el PDF fuente o si es contenido sintetizado por el ensamblador. Se declara **NO VERIFICADO** (no se infiere fabricación, pero tampoco se certifica verbatim) — es el hallazgo que más pesa sobre el veredicto de las tres variantes.

**Segundo hallazgo transversal:** la referencia interna heredada "*(ver 05 OWNERSHIP, 10 CV-GOLDEN-RULES)*" dentro del bloque verbatim de `01.1 KERNEL:PURPOSE-001` / `02.1 KERNEL:INV-LIST` queda con numeración legacy sin resolver en **las tres** variantes. Esto está *declarado* explícitamente como pendiente de un pase NORM futuro (notas de cabecera de cada paquete), por lo que no es un defecto oculto, pero confirmo que el pase NORM es un prerrequisito real antes de considerar el documento "navegable" por número.

---

## VARIANTE v10.1

### Veredicto: **GO CON OBSERVACIONES**

### Tabla de hallazgos

| # | Severidad | Ubicación | Descripción | Evidencia |
| --- | --- | --- | --- | --- |
| 1 | OBSERVACIÓN | Cap. 02 KERNEL:INVARIANTS | El wrapper nuevo "02 KERNEL:INVARIANTS" embebe verbatim el capítulo legacy "02 KERNEL:FAIL-PHILOSOPHY" conservando su numeración ORIGINAL (02, 02.1, 02.2) — se produce colisión de número de capítulo (dos "02" en niveles distintos) y una subsección sin formato NN.M coherente con su capítulo contenedor, lo que tensiona la propia "Regla de Bloque Único"/Matriz Tipográfica que el mismo paquete reproduce verbatim en el cap. 08. | Export: `02 KERNEL:FAIL-PHILOSOPHY` (capítulo propio) vs Paquete: `02 KERNEL:INVARIANTS` ... `02 KERNEL:FAIL-PHILOSOPHY` anidado como si fuera subsección. |
| 2 | OBSERVACIÓN (crítica si T2.2b/T2.3b no se ejecutan) | PAQUETE OPERATIVO, Secc. E (STAGE) | 5 IDs del export quedan con contenido reducido a "regla de 1 línea" dentro del KERNEL importable, con el contenido completo diferido a documentos que **aún no existen** (SKILL_REFERENCE T2.3b, MANUAL:LAZY-LOAD T2.2b): `DOCUMENTATION-005`, `-010`, `-017`, `CONTEXT-INFRASTRUCTURE-001`, `-002`. Mientras esos documentos no se creen, el sistema vivo pierde el detalle operativo completo (tabla de verbos, tabla Skill/Gate, patrón Sandbox, triaje MCP). | Paquete cap.12: "03.5 Convencion de Anuncio de Skills - ... Tɑblɑ de verbos: SKILL_REFERENCE (T2.3b)." vs Export 03.5: tabla completa de 13 skills con verbos. |
| 3 | NO VERIFICADO | Cap. 11 KERNEL:EXCEPTIONS | Ver hallazgo transversal — capítulo entero sin trazabilidad verbatim al export entregado. | — |
| 4 | OBSERVACIÓN (declarada) | Múltiples | Referencias numéricas internas ("ver 09.1", "ver 05 OWNERSHIP, 10 CV-GOLDEN-RULES") permanecen en numeración legacy, inconsistentes con la nueva numeración de capítulos-wrapper (01-12) hasta el pase NORM. | Declarado en cabecera del propio paquete. |
| 5 | OBSERVACIÓN | PAQUETE OPERATIVO, Secc. A | Migraciones declaradas correctamente ("contenidos staged en el paquete, no perdidos") — buena práctica de disclosure, mitiga parcialmente el hallazgo #2. | — |

### Identidad (Check C — huérfanos)

- **Huérfanos reales: 0.** Todo ID del export aparece en la zona importable (verbatim, con numeración legacy preservada) o está cubierto por el mapa de redirección (Sección D).
- **Casos especiales a vigilar:** `KERNEL:CONTEXT-INFRASTRUCTURE-001/002` quedan redirigidos **fuera** del KERNEL hacia `MANUAL:LAZY-LOAD` (documento que no existe aún) — técnicamente cubierto por el mapa, pero es una redirección de salida total, no una renumeración interna.

### Verbatim estricto

Verificado por muestreo (secciones OWNERSHIP→ACTORS, ARCHITECTURE-L1..L4, SCHEMA-001..009, GATE-DECISION-001..013, CV-GOLDEN-RULES-001..006, CV-PIPELINE-001..003): el texto coincide palabra por palabra con el export, incluyendo una referencia cruzada aparentemente heredada ("sistema de hyperlinks (KERNEL:DOCUMENTATION-011)") que se preserva fielmente tal como está en el export (no es un error introducido por el paquete).

### Suma de tamaños

El paquete importable es **más pequeño** que el export en el volumen correspondiente a los 5 IDs reducidos a "regla de 1 línea" (hallazgo #2) — explicado como migración intencional, no truncamiento silencioso.

[KERNEL_v10_1_import](https://app.notion.com/p/KERNEL_v10_1_import-3ee938befc428109948dc1c3c9c4d022?pvs=21)

---

## VARIANTE v10.2

### Veredicto: **GO CON OBSERVACIONES**

### Tabla de hallazgos

| # | Severidad | Ubicación | Descripción | Evidencia |
| --- | --- | --- | --- | --- |
| 1 | NO VERIFICADO | Cap. 16 KERNEL:EXCEPTIONS | Hallazgo transversal — sin trazabilidad al export. | — |
| 2 | OBSERVACIÓN (declarada) | Múltiples | Referencias numéricas legacy sin resolver (igual que v10.1), pendiente de pase NORM. Correctamente anotado en cabecera. | — |
| 3 | OBSERVACIÓN menor | Transición cap. 14→15→16 | El capítulo 15 (EVOLUTION) no muestra un encabezado Roman explícito propio en el flujo de texto — queda implícitamente bajo "IV. GOBIERNA DOCUMENTAL" junto con HYPERLINKS/DOC-OPS antes de que "V. EXCEPCIONES" abra solo para el capítulo 16. Temáticamente EVOLUTION encaja mal bajo "Gobierna Documental". No rompe el conteo de 5 partes/16 capítulos, pero es una categorización forzada. | Texto fluye "...14.12 KERNEL:OPS-SERIAL" → "15 KERNEL:EVOLUTION" → luego "V. EXCEPCIONES" recién antes del cap.16. |
| 4 | POSITIVO (sin hallazgo) | Todo el documento | A diferencia de v10.1, v10.2 **no** diferiere contenido a documentos externos — `CONTEXT-INFRASTRUCTURE-001/002` se integra íntegro (verbatim) como subsecciones 08.3/08.4 del nuevo capítulo DATA-FLOW; `DOCUMENTATION-005/010/017` se integran completos en 14.10/14.11/14.9 (tabla de verbos y tabla Skill/Gate completas, no resumidas). | Verificado contra cap. 14 completo. |

### Identidad (Check C — huérfanos)

- **Huérfanos: 0.** Cobertura completa verificada contra el mapa numérico (Sección D) — muestreo de filas (09.1-09.13→06.1-06.13; 12.1-12.3→09.1-09.3; 03.16/17/18/19→14.8/14.9/12.3/14.12) coincide exactamente con el contenido real.
- IDs canónicos PREFIX:KEY preservados intactos en el 100% de la muestra revisada.

### Verbatim estricto

Excepción declarada para v10.2 (headings renumerados pero ID en la misma línea) cumplida en el 100% de la muestra (ej. "06.12 KERNEL:DEDUP-LAYER-UPGRADE", "09.1 KERNEL:CV-PIPELINE-001"). Sin parafraseo detectado en los bloques verbatim muestreados.

[KERNEL_v10_2_import](https://app.notion.com/p/KERNEL_v10_2_import-3ee938befc4281b18345db8ab59efe79?pvs=21)

---

## VARIANTE v10.3

### Veredicto: **GO CON OBSERVACIONES**

### Tabla de hallazgos

| # | Severidad | Ubicación | Descripción | Evidencia |
| --- | --- | --- | --- | --- |
| 1 | NO VERIFICADO | Cap. 16 KERNEL:EXCEPTIONS | Hallazgo transversal — sin trazabilidad al export. | — |
| 2 | OBSERVACIÓN | PAQUETE OPERATIVO, Secc. C | Fila de la tabla de migración usa la etiqueta ficticia **"DOCUMENTATION-019"**, KEY que no existe en el export (la posición 03.19 del export es literalmente `KERNEL:HANDOFF-SERIAL`, no `DOCUMENTATION-019`). No genera huérfano real porque `HANDOFF-SERIAL → OPS-SERIAL` está correctamente listado por separado en la misma tabla y en la Sección E, pero es un error de rotulado que puede confundir a quien reconstruya el Census manualmente. | Sección C: "DOCUMENTATION-005 / -010 / -019 → OPS-ANNOUNCE / OPS-GATES / OPS-SERIAL" (no existe KEY DOCUMENTATION-019 en el export). |
| 3 | OBSERVACIÓN menor | PAQUETE OPERATIVO, Secc. C, fila "Capitulos disueltos sin alias" | La fila mezcla capítulos legacy genuinamente disueltos (DOCUMENTATION, SCHEMA, TRACKER-SCHEMA, CONTEXT-INFRASTRUCTURE, GATE-DECISION, CV-PIPELINE, CV-GOLDEN-RULES) con nombres de capítulos **nuevos** de v10.2/v10.3 (DATA-CONTRACT, HYPERLINKS, DOC-OPS) que nunca existieron en el export y por tanto no son "disueltos" sino "nuevos sin legado 1:1". Redacción confusa, no afecta integridad de datos. | — |
| 4 | OBSERVACIÓN (declarada) | Múltiples | Mismas referencias numéricas legacy sin resolver que v10.1/v10.2 (exentas explícitamente del mandato de re-key porque no usan prefijo "KERNEL:"). | "(ver 05 OWNERSHIP, 10 CV-GOLDEN-RULES)" sin prefijo KERNEL:, consistente con la nota de referencias del propio paquete. |
| 5 | POSITIVO (sin hallazgo) | Re-keying general | Muestreo extenso (SCH-DEDUP-GUARD, ARC-L4, ARC-L1, FAIL, GATE-REVIEW, OPS-IMPACT, FLOW-WRITE, FLOW-CTX-SCOPE/ROUTE, GATE-MUTABILITY, GATE-AUDIT-LIVE) confirma re-key consistente y sin residuales de patrón legacy con prefijo "KERNEL:". | — |

### Identidad (Check C — variante v10.3, prueba inversa)

- **(1) Cero residuales:** confirmado por muestreo exhaustivo — no se detectó ningún KEY con patrón legacy (`DOCUMENTATION-NNN`, `SCHEMA-NNN`, `GATE-DECISION-NNN`, `TRIGGER-NNN`, `OWNERSHIP`, `FAIL-PHILOSOPHY`, `CONTEXT-INFRASTRUCTURE`, `CV-PIPELINE`, `CV-GOLDEN-RULES-`, `DOC-CONTRACT`, `DATA-FLOW`, `PURPOSE-001`, `HANDOFF-SERIAL`, `NAMING-CONVENTION`, `DEDUP-LAYER-UPGRADE`) con prefijo `KERNEL:` en la zona importable. **Excepción confirmada y aceptable:** menciones numéricas sueltas sin prefijo KERNEL: (ej. "05 OWNERSHIP") permanecen, pero están fuera del alcance del mandato de re-key (son referencias numéricas, cubiertas por la nota de "pase NORM pendiente").
- **(2) Cobertura de migración:** sustancialmente completa en Secciones C y E, con la salvedad del rótulo fantasma "DOCUMENTATION-019" (hallazgo #2) — no genera huérfano real porque el KEY verdadero (HANDOFF-SERIAL) sí está cubierto en ambas tablas.
- **KEYS sin alias:** ninguno detectado (0 huérfanos reales).

[KERNEL_v10_3_import](https://app.notion.com/p/KERNEL_v10_3_import-3ee938befc428119b590dad1405e7ae1?pvs=21)

## Respuesta a las decisiones de diseño (aplica a las tres, con matices)

**1. ¿Política de identidad coherente con la regla de bloque único?**

- v10.2 y v10.3: **Sí**, coherencia plena — cada `###` declara su ID (original o re-keyed) en la misma línea, sin excepciones decorativas detectadas.
- v10.1: **Parcialmente**. La preservación de numeración legacy para subsecciones embebidas dentro de capítulos-wrapper renumerados genera al menos un caso (cap. 02 INVARIANTS conteniendo el capítulo legacy "02 FAIL-PHILOSOPHY") donde la jerarquía de encabezados choca con la propia Matriz Tipográfica Congelada que el documento reproduce verbatim. Es una tensión de diseño, no una violación catastrófica, pero merece corrección en el próximo ciclo.

**2. ¿Las absorciones de capítulos son completas y sin contradicción?**
Sí, en las tres variantes. PURPOSE-001+FAIL→INVARIANTS, OWNERSHIP→ACTORS, SCHEMA+TRACKER-SCHEMA→DATA-CONTRACT se verificaron completas por muestreo, sin reglas contradictorias introducidas en las prosas de capítulo nuevas.

**3. ¿Quedan referencias colgantes a destinos que cambiaron?**
Sí, en las tres. Las referencias numéricas tipo "ver 09.1", "ver 05 OWNERSHIP, 10 CV-GOLDEN-RULES" quedan apuntando a numeración legacy no resuelta. Está **declarado como pendiente de pase NORM** en los tres paquetes — no es un hallazgo oculto, pero es un prerrequisito operativo real antes de dar por "navegable" el documento importado.

**4. ¿La prosa nueva del ensamblador introduce alguna norma que contradiga el legado?**
No se detectaron contradicciones normativas. El contenido del capítulo EXCEPTIONS (nuevo en las tres variantes) es consistente con decisiones ya documentadas en otras secciones (Bypass, Graph=0, Session Ledger) — el problema no es contradicción sino **trazabilidad** (ver hallazgo transversal #1). La gramática nueva de v10.3 (NAM-ID-GRAMMAR, 12.5) es compatible con la Matriz Tipográfica heredada, sin conflicto detectado.

---

## Conclusión

Ninguna de las tres variantes presenta un NO-GO bloqueante (variante declarada en las tres, cero huérfanos reales, mapas de migración/alias sustancialmente completos). Las tres reciben **GO CON OBSERVACIONES**, condicionado a:

1. **Verificar contra el export vivo real** (no el PDF entregado) el origen del capítulo `KERNEL:EXCEPTIONS` antes de publicar — es el hallazgo de mayor severidad potencial en las tres variantes.
2. v10.1: resolver la colisión de jerarquía cap.02/FAIL-PHILOSOPHY y confirmar fecha de ejecución de T2.2b/T2.3b antes de que el contenido reducido a 1 línea quede huérfano de facto.
3. v10.2: aclarar la ubicación temática de EVOLUTION dentro de las 5 partes.
4. v10.3: corregir el rótulo "DOCUMENTATION-019" y la fila de "capítulos disueltos" en el PAQUETE OPERATIVO antes de usarla como insumo de Census/alias.
5. Las tres: ejecutar el pase NORM de referencias numéricas antes de considerar el documento completamente autoconsistente.