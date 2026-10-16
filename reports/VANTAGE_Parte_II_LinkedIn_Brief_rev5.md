# Parte II. VANTAGE TECHNICAL BRIEF

## LinkedIn Search & Identity Pipeline — rev. 5 (2026-10-16)

  ------------------------------------------------------------------------------------
  Field                               Value
  ----------------------------------- ------------------------------------------------
  Contract ID                         **`PromptA-v2.0+linkedin`**. `v1.0` es solo el
                                      `prompt_version` del feed baseline del
                                      2026-10-04.

  Registry status                     `CANONICAL` según PROMPT_CANON (Notion),
                                      promovido 2026-10-05. **El Implementation SHA
                                      registrado (`f7fa0513…`) ya no corresponde al
                                      contenido del matcher en `HEAD`** (§4.1). Estado
                                      de Notion no re-leído en esta revisión: la
                                      verificación local usa un data source simulado.

  Primary implementation              `Layer_1/scripts/linkedin_identity_matcher.py`
                                      (blob en `HEAD`: `88df0c45…`, ya **no**
                                      `e7e2459c…` como en `f7fa0513`).

  Integration                         `Layer_1/scripts/feed_processor.py` +
                                      `layer_1_orchestrator.py --file <feed.json>`.
                                      El normalizador v2.0 **está en `main`**, no por
                                      el commit aislado `1e6ec75e…` (objeto colgante)
                                      sino por `e3a3348`.

  Validation references               `CS-HERMES-L1-02-R1` (contenido original del
                                      2026-10-09, recuperable en `e3a3348`; el archivo
                                      actual en esa ruta fue sobrescrito — §6.1).
                                      Suite reproducida: **311** en el árbol de
                                      `1e6ec75e…`; **396** en `HEAD`.

  Document status                     rev. 5 incorpora una auditoría independiente
                                      contra fuentes primarias en `HEAD`
                                      `e61be89` (2026-10-16). Corrige T3.I a
                                      **cerrado**, resuelve CS-HERMES-L1-03 y retira
                                      límites de evidencia que ya no aplican. No
                                      demuestra adquisición LinkedIn v2.0 en vivo ni
                                      producción.
  ------------------------------------------------------------------------------------

### Convención de estados de evidencia (nueva en rev. 5)

- **[V]** Verificado en esta revisión contra fuente primaria del repositorio.
- **[R]** Reportado por otra fuente; no re-verificado aquí (p. ej. Notion, sesión de
  agente, escritura externa).
- **[S]** Superado: una revisión posterior del repo contradice lo afirmado en rev. 4.

---

## 1. Purpose

Apply deterministic VANTAGE rules to vacancies discovered on LinkedIn:
employer identity, blocked-employer detection, acceptance, exclusion,
provenance, deduplication, structured feed production and downstream
normalization. Acquisition and identity matching are separable. The
matcher is not browser automation. **[V]** — arquitectura y separación de
responsabilidades se sostienen en el código de `HEAD`.

## 2. Architecture

LinkedIn acquisition → structured feed → `linkedin_identity_matcher.py`
→ candidate/rejection classification → feed → `feed_processor.py` →
normalized VANTAGE records. The browser environment is not the authority
on employer identity. The integration changes the downstream normalizer,
not the matcher's identity logic. **[V]** para el tramo matcher →
`feed_processor.py` → records. El tramo de adquisición no tiene evidencia
de ejecución v2.0 (§11).

## 3. Identity states

`BLOCKED` (strong match against the blocked set), `NOT_BLOCKED`,
`AMBIGUOUS` (overlap with a blocked identity but insufficient to block),
`UNRESOLVED` (identity cannot be resolved reliably). Uncertainty is
never silently converted into a match. `NOT_BLOCKED` is a matcher state;
accepted feed jobs use `status=candidate` and `blocked_company=null`.

**[V]** Los cuatro estados existen en `MatchStatus`
(`linkedin_identity_matcher.py:75-81`) y las transiciones de
`match_employer()` respetan el orden documentado: evidencia ausente →
`UNRESOLVED`; identidad normalizada idéntica → `BLOCKED`; solapamiento
parcial → `AMBIGUOUS` (nunca `BLOCKED`); resto → `NOT_BLOCKED`.
**[V]** En el baseline v1.0, los 12 candidatos tienen
`status="candidate"` y `blocked_company=None`; ningún registro usa
`NOT_BLOCKED` como estado de feed.

Terminology: `BLOCKED` here means **employer hard-blocked**. In Workday
it means acquisition blocked; in the Kernel it names a `Gate_Decision`;
in ingestion it may describe a record excluded by a role rule. Always
qualify it.

## 4. Blocked employer set

Operator decision 2026-10-07: L'Oréal (all variants), Levi's / Levi
Strauss (aliases `levi strauss`, `levi strauss & co`, `levis`,
`levi's`), and El Palacio de Hierro. **Dockers is removed** from
`Layer_1/config/hard_blocks.json`, the single executable source. The
JSON is v1.1 and was applied, tested and committed on 2026-10-08.

**[V]** `hard_blocks.json` declara `"version": "1.1"`, contiene 13
aliases (7 de L'Oréal, 4 de Levi's/Levi Strauss, 2 de El Palacio de
Hierro), **no contiene `dockers`**, y su nota interna registra
"Dockers fuera de Hard Blocks desde 2026-10-07 (decisión del operador)".
El archivo se tocó por última vez en `7df7579` y antes en `5b8e245`
(auto-sync 2026-10-08).

### 4.1 Corrección: el binding SHA del contrato está obsoleto **[S]**

rev. 4 afirma (§4) que *"The matcher and LINKEDIN-RULES-002 §2 have a
separate set that still includes Dockers. This divergence remains open
under T3.I. The matcher was not changed in this integration."*

La segunda parte era cierta para el commit aislado `1e6ec75e…`, pero
**el matcher sí fue modificado después**, en `main`:

| Revisión | Blob de `linkedin_identity_matcher.py` | ¿Contiene `"Dockers"` en `BLOCKED_EMPLOYERS`? |
|---|---|---|
| `f7fa051` (SHA registrado en PROMPT_CANON) | `e7e2459ca3e1e8f598938e14b275c4576dd4b228` | **Sí** (línea 52) |
| `7c4a170` "Align Dockers hard-block policy with config and tests" | `d69f399efde1d42d4b63166deb4a6416f1e22b79` | No |
| `5ee2c5b` (limpieza + paridad) y `HEAD` `e61be89` | `88df0c45a4f9475e32b4a128f1d7c4ee8c1eb4f8` | No |

`BLOCKED_EMPLOYERS` en `HEAD` contiene exactamente cuatro identidades
canónicas: `L'Oréal`, `Levi Strauss`, `Levi's`, `El Palacio de Hierro`.

**Consecuencia de gobernanza no resuelta.** El propio diagnóstico T3.I
advertía: *"Cualquier cambio al matcher invalida ese binding SHA→path y
exige re-promoción del operador (nueva fila/versión en PROMPT_CANON con
nuevo Implementation SHA)."* El cambio se aplicó sin re-promoción
registrada. **[V]** `test_prompt_canon.py:26` sigue fijando
`LINKEDIN_SHA = "f7fa0513d591a1dbf5c2cf30851e82803d9816e5"` y
`test_i20_linkedin_row_passes` sigue pasando, porque `verify_provenance_git()`
(`verify_versions.py:888-908`) sólo comprueba que el SHA resuelve en Git y
que `git show <SHA>:<path>` devuelve contenido no vacío — **nunca compara
ese contenido con el de `HEAD`**. La suite, por diseño, no puede detectar
este desajuste.

**Acción requerida (operador):** nueva fila/versión en PROMPT_CANON con
Implementation SHA correspondiente a `88df0c45…` (o al commit que
contiene el matcher vigente), o revertir el matcher. Mientras no se haga,
el contrato `CANONICAL` apunta a una implementación que ya no es la
vigente.

### 4.2 T3.I — cerrado

**[V]** El parche propuesto por Arena fue aplicado y verificable:

- `7c4a170` "Align Dockers hard-block policy with config and tests"
  (2026-10-09 12:13, cherry-pick de `bbfd3e3…`) elimina `"Dockers"` del
  matcher y ajusta los 2 tests que lo codificaban.
- `5ee2c5b` (2026-10-09 16:37) añade `Layer_1/tests/test_matcher_hard_blocks_parity.py`
  (4 pruebas): Dockers ausente en ambas fuentes; cada alias del JSON
  cubierto por el matcher; cada identidad del matcher presente en el
  JSON; Aéropostale no es Hard Block.
- Las 4 pruebas de paridad pasan en `HEAD`.

**Residual, no verificable aquí:** `LINKEDIN-RULES-002 §2` vive en Notion
y su re-sincronización requiere escritura del operador. **[R]** No se
releyó Notion en esta revisión.

## 5. Why identity matching exists

Substring matching is insufficient: a vacancy can mention another
company as retailer, channel, client, partner or previous employer.
Validated case: Benefit Cosmetics mentioning El Palacio de Hierro as a
channel was not blocked. `employer identity ≠ arbitrary company-name
occurrence`. By contrast, `hard_block_gate.py` used by Career Sites is a
case-insensitive substring match; gate semantics remain a separate issue.

**[V]** El caso está en la fuente primaria, no sólo en el reporte: el
baseline `2026-10-04_linkedin.json` incluye
`data_quality_warnings[BLOCKED_COMPANY_CLARIFICATION]` sobre *Benefit
Cosmetics 4474550128*, que ejecuta VM en El Palacio de Hierro y Sephora,
con impacto "No activa rechazo. Confirmado: la.company es Benefit
Cosmetics." El matcher separa `channel_fields()` (brand, retail_channel,
client, distribution_partner) de `observed_employer`.

## 6. Validation

-   Matcher: 27 tests were reported passing in the prior evidence
    report. **[V]** — 27 tests existen y pasan en el matcher, tanto en
    `1e6ec75e…` como en `HEAD`. **Matiz nuevo:** el conteo es idéntico,
    pero el archivo de tests cambió (`7c4a170` ajustó `test_m07` y
    `test_m10b` para reflejar la salida de Dockers).
-   Earlier full Layer_1 suite: 259 tests in the original acta; 282 at
    commit `a67d5fa` after 23 PROMPT_CANON tests were added. **[R]**
    consistente con `handoffs/Brief LinkedIn : PROMPT_CANON.md` §7
    (23/23 y 282/282) y §8; `a67d5fa` existe en Git (2026-10-05 07:51).
    **[V]** `test_prompt_canon.py` sigue teniendo 23 pruebas.
-   Integration suite: 311 tests passed **before** commit `1e6ec75`,
    according to Hermes. **[V]** — reproducido de forma independiente
    sobre el árbol exacto de `1e6ec75e…`: `311 passed` (15 archivos de
    test; 4 de los 19 archivos actuales aún no existían allí:
    `test_active_search_hard_blocks`, `test_hard_blocks_notes`,
    `test_matcher_hard_blocks_parity`, `test_vantage_sync`).
-   No post-commit suite run is claimed here. **[S]** — ya existe corrida
    post-commit: **396 passed** en `HEAD` `e61be89` (19 archivos),
    ejecutada en esta revisión. El crecimiento de +85 respecto de 311 se
    reparte así: `test_vantage_sync` +65, `test_gate_logic` +6,
    `test_matcher_hard_blocks_parity` +4, `test_hard_blocks_notes` +4,
    `test_active_search_hard_blocks` +3, `test_profile_fit` +3.
-   Matcher correctness and acquisition coverage are separate
    dimensions. **[V]** — el propio evidence report corrió el matcher
    v2.0 *sobre los 12 candidatos del baseline v1.0*, no sobre
    `accepted[]` de una adquisición v2.0 (§11).

### 6.1 El reporte de validación citado fue sobrescrito **[S]**

`reports/CS-HERMES-L1-02-R1_verification_report.md` **hoy** contiene una
auditoría forense de consumo de tokens del bootstrap (fechada
2026-10-13, sesión `20261013_154811_d458a0`) con **cero menciones** de
LinkedIn, T3.M, `feed_processor`, `matcher` o 311. Fue sobrescrita por el
auto-sync `7efbd37` (2026-10-13, ±660 líneas).

El contenido **original** —el que la rev. 4 cita como referencia de
validación— fue añadido por `e3a3348` (2026-10-09, 287 líneas) y sigue
recuperable:

```
git show e3a3348:reports/CS-HERMES-L1-02-R1_verification_report.md
```

Ese original sí es el reporte de integración: veredicto
`READY_FOR_OPERATOR_APPROVAL`, `311 passed in 54.80s`, worktree
`VANTAGE-verify-arena` en `e58dce1`, rama Arena
`origin/arena/d6fd1928-vantage` @ `69dbcf2`, merge staged sin commit,
sin push, sin `--apply`, sin escrituras en Notion.

**Riesgo documental:** una referencia de validación de un contrato
CANONICAL fue destruida por un auto-sync y no hay protección de ruta.
Conviene que los reportes de evidencia citados por un contrato sean
inmutables o versionados por nombre.

## 7. Feed structure

The historical v1.0 baseline has top-level `jobs`, `audit_log`, and
`search_summary`. Its record fields include `title`, `company`,
`location`, `apply_url`, `job_id`, `jd`, `source_type`, `source`,
`seniority`, `work_mode`, `industry`, `cdmx_location`, `excluded_term`,
`blocked_company`, `rejection_reason`, and `status`. Population depends
on acquisition and classification.

**[V]** Claves reales del baseline (`2026-10-04_linkedin.json`):
`prompt_variant`, `prompt_version`, `generated_at`, `candidate`,
`search_summary`, `audit_log`, `jobs`, `rejected_jobs`,
`not_evaluated`, `search_metadata`, `data_quality_warnings`. Los campos
de registro listados existen todos, más `posted_date`,
`platform_signals` y (en rechazados) `prompt_a_rejection_detail` /
`prompt_a_rejection_reason`. `prompt_version` = `PromptA-v1.0+linkedin`
**[V]**, `prompt_variant` = `A-weekly-unified-linkedin`.

The v2.0 contract instead requires `accepted[]`, `reroute[]`,
`rejected[]`, and `not_evaluated[]`. The v2.0 normalizer does not treat
the baseline `jobs` envelope as v2.0. **[V]** — un envelope v1.0 sigue
lanzando `ValueError` con el prefijo de error original.

## 8. Candidate lifecycle

Discovery → identity resolution → eligibility/exclusion → accepted
candidate, or rejection with metadata preserved. In downstream
ingestion, only v2.0 `accepted[]` is ingested. `reroute[]` remains
available for review and belongs to another search family. `rejected[]`
and `not_evaluated[]` are not ingested.

**[V]** implementado y probado en `feed_processor.py`
(`_LINKEDIN_V2_ARRAYS`, `normalize_linkedin_v2_envelope`) y cubierto por
`test_feed_processor_linkedin_v2.py` (20 pruebas). El mapeo de campos
(`employer_identity`→`company`, `location_observed`→`location`,
`url`→`apply_url`, `source`/`source_type`="linkedin") vive en la rama
v2.0 y no altera los alias globales.

Dos precisiones que la rev. 4 no registraba:

- **La rama v2.0 se evalúa al final.** `normalize_envelope()` prueba
  `results_by_source` → `listings` → `consolidated_results` → lista →
  recién entonces `is_linkedin_v2_envelope()`. Hay una prueba explícita
  (`test_regression_existing_shapes_take_precedence_over_v2_keys`) que
  fija esa precedencia. Es correcto para no romper fuentes existentes,
  pero un envelope v2.0 que además traiga `listings` **no** se trataría
  como v2.0.
- **La validación es todo-o-nada.** Cualquier item inválido de
  `accepted[]` lanza `ValueError` citando `job_id`; no hay ingesta
  parcial (`test_no_partial_ingestion_on_error`).

## 9. Integration — status 2026-10-16 (rev. 5)

The original defect was that `feed_processor.normalize_envelope()`
rejected both the baseline v1.0 envelope and the canonical v2.0 LinkedIn
envelope.

### T3.M decision and implementation

**[V]** El normalizador soporta el schema v2.0 e ingesta sólo
`accepted[]`. Conserva `reroute[]` en el feed/archivo sin ingestión y
excluye `rejected[]` y `not_evaluated[]`. El envelope debe aportar los
cuatro arrays como listas y una clave `contract` o `schema`
(`is_linkedin_v2_envelope`). Los `accepted` se validan contra
`status == "ACCEPTED"`, campos string requeridos `url`, `title`,
`employer_identity`, y `location_observed` (vacío si ausente, error si no
es string). `jd` no-string se normaliza a `""`. 20 pruebas pasan.

### T3.N decision and integration

**[V]** `archive_dryrun_notion()` retorna temprano salvo que
`VANTAGE_ARCHIVE_DRYRUN_NOTION == "1"` (`feed_processor.py:1371`); el
flag `--archive-notion` setea esa variable (`:1439`, `:1448-1450`). Las
4 pruebas de `test_archive_dryrun_notion_optin.py` pasan y verifican
cero llamadas a la API de Notion sin opt-in. Default local-only: **[V]**
a nivel de código. Ausencia de escrituras reales durante la sesión de
integración: **[R]** (sin `NOTION_TOKEN` ni `APROBAR_WRITE` no es
re-verificable retroactivamente).

### Commit y estado Git

**[V]** El commit aislado existe y coincide exactamente con lo reportado:

| Verificación | Resultado |
|---|---|
| `1e6ec75e335511be148ff92518a1cf298e615cf6` existe | Sí |
| Parent | `e58dce183d2f0e8ee79c3bd5bb7210912de6396c` ✅ coincide |
| Archivos / inserciones / borrados | 9 / 1 026 / 1 ✅ coincide |
| Push | No — no está en ninguna rama remota |
| Contenido en `main` | Sí, pero vía `e3a3348`, no vía este commit |
| ¿Ancestro de `HEAD`? | **No.** Objeto colgante: ninguna rama lo contiene |

**Hallazgo nuevo y relevante:** `1e6ec75e…` no es un commit "aislado
pendiente"; es un **objeto colgante superado**. El mismo changeset entró
a `main` por `e3a3348` ("feat(feed-processor): add dry-run tests, notion
opt-in validation, and session artifacts", 2026-10-09 12:21, parent
`7c4a170`), que contiene los mismos 9 archivos **más** el reporte R1
original. 7 de los 9 archivos siguen presentes e idénticos en `HEAD`;
2 fueron eliminados deliberadamente por `5ee2c5b` (el dry-run con falso
negativo y el hallazgo obsoleto).

Estado actual del repositorio **[V]**:

- `HEAD` = `origin/main` = `e61be89d88539bafd3e7976917a570542d8cd629`, 0/0 ahead/behind.
- `git status --short` vacío: **working tree limpio** (el timeout reportado no se reproduce).
- **Hooks:** `.git/hooks/` contiene únicamente archivos `*.sample` y
  `core.hooksPath` no está definido ⇒ **no existe ningún hook activo** en
  este checkout. La inquietud "hooks bypassed by `commit-tree`" queda
  resuelta: no había hooks que omitir. (No es posible probar
  retroactivamente qué hooks existían el 2026-10-09.)

**Invocation:** `python scripts/layer_1_orchestrator.py --file <feed.json>`
con dry-run por defecto **[V]** — el default es `dry_run=True`
(`layer_1_orchestrator.py:1729-1734`); `--apply` es explícito y advierte
que ignora `--dry-run`.

**Corrección menor a §14:** `--file` y `--ats workday` **no** están en un
grupo mutuamente excluyente de argparse. Si se pasan ambos, el flujo ATS
sobrescribe `args.file` con su propio feed y el `--file` del usuario se
ignora en silencio. Funcionalmente excluyentes, pero no rechazados.

## 10. Baseline feed evidence (2026-10-04)

Acquired on 2026-10-04 by browser under contract v1.0 (7 queries, guest
mode). `search_summary` funnel: 420 cards → 233 unique IDs → 24 screened
by title/company → 24 detail pages validated → 12 candidates; 21
rejected; 2 not evaluated.

**[V]** Todos los números coinciden literalmente con `search_summary`:
`queries_executed=7`, `raw_cards_rendered=420`, `unique_job_ids=233`,
`title_and_company_screened=24`, `detail_pages_validated=24`,
`candidates_count=12`, `rejected_count=21`. `generated_at` =
`2026-10-04T14:17:11Z`; `search_metadata.browser_sessions=2`; filtro
`f_TPR=r604800`; método de extracción DOM.

Unreconciled: the file holds 35 individual records (12 candidates + 21
`rejected_jobs` + 2 `not_evaluated`) against 24 validated detail pages,
and 198 unique IDs have no individual record. **[V]** — `jobs` tiene 12
(items con `status="candidate"`), `rejected_jobs` 21, `not_evaluated.items`
2; total 35, y 233 − 35 = 198. Los 35 `job_id` son únicos. Do not
describe 233 as evaluated.

The feed's `data_quality_warnings` **(reported in prior notes, not
independently re-read here)** — **[S]: ahora leídas directamente.** Los
seis códigos confirman la descripción de la rev. 4 y añaden dos que no
figuraban:

| Código | Contenido verificado |
|---|---|
| `SENIORITY_SCOPE_DRIFT` | "4 de 12 candidatos" con encaje débil (roles de piso/operaciones) |
| `INDUSTRY_OUT_OF_PROFILE` | "7 de 12 candidatos" fuera de la lista de industrias del perfil |
| `POSTING_STALE` | We Are Prada `4472370761`, entrevistas 1-oct vs sesión 4-oct |
| `LOCATION_TEXT_INCONSISTENT` | La Europea `4474103889`: CDMX en titular, "(Querétaro)" en el cuerpo |
| `BLOCKED_COMPANY_CLARIFICATION` | Benefit Cosmetics `4474550128`: canal ≠ empleador (§5) |
| `COVERAGE_LIMIT` | Sólo las primeras 60 tarjetas por keyword; `detail_validated: false` |

The baseline proves parsing, not relevance. The 60-card cap is an
acquisition limit, not evidence of total vacancies. **[V]**

## 11. Coverage limitation

Contract v2.0 requires nine queries; none have been demonstrated as
executed live. **[V]** No existe en el repositorio ningún feed con las
cuatro listas v2.0 salvo el fixture sintético, que declara
explícitamente `"live_acquisition": false` y `"queries_executed": 0`, con
la nota *"NO proviene de una adquisición real de LinkedIn. No colocar en
feeds/."*

During the 2026-10-06 runtime, the browser could not initialize
(`browser.use_real_profile` enabled, default browser not supported
Chromium, cloud backend failed), reproduced in three attempts including
`local=false`. **[V]** — documentado en
`Layer_1/reports/CS-L1-RUNTIME-02_evidence_report.md` §2.2/§4.2 con el
error literal y la nota de que las 9 queries v2.0 no pueden ejecutarse
sin acceso a browser. `PASS_WITH_COVERAGE_LIMITATION` describe processing
of the v1.0 baseline, not a v2.0 acquisition **[V]**. Other limits: about
60 cards per query as guest; `start` ineffective without authentication;
authenticated access may be needed for coverage; browser failures can
block acquisition independently of VANTAGE code.

## 12. Audit events

Acquisition events (Redirect, Filled, Cloudflare, Technical, Completed,
Expired) provide acquisition-quality context and are not job rejections.
**[V]** — los 6 eventos del baseline son exactamente esos tipos, cada uno
con `source=linkedin`, `timestamp` y `details`.

## 13. Deduplication

`job_id` is the primary source-level key where available; the common
pipeline applies its own policy at ingestion. Relevant when LinkedIn and
Career Sites hold the same vacancy. **[V]** — `job_id` es único en los 35
registros del baseline; `test_dedup.py` (16 pruebas) pasa.

## 14. Cross-source coexistence

Provenance remains separate: `source_type=linkedin` versus
`career_page`. Coexistence means both feeds can be normalized by shared
code without contaminating provenance; it does not mean a single run
executed both sources. Orchestrator invocations for LinkedIn (`--file`)
and Career Sites (`--ats workday`) are mutually exclusive — **ver §9
para la corrección: no hay exclusión mutua declarada en argparse.**

**[V]** los 12 candidatos del baseline tienen
`source_type="linkedin"`, `source="linkedin"`.

## 15. Strengths

Identity-aware exclusion; explicit states for uncertainty; independently
testable matcher; source separation; provenance retention; safe failure
semantics (failed acquisition is not an empty result); v2.0
accepted-only downstream normalization. **[V]** para todos los puntos de
código; el matcher suma ahora una **prueba de paridad automática** contra
`hard_blocks.json` (§4.2), que es una fortaleza nueva respecto de rev. 4.

## 16. Limitations

Browser dependency; guest-mode caps; authentication dependency; coverage
cannot be inferred from matcher output; platform volatility;
live v2.0 acquisition remains unproven. **Retirado en rev. 5:** "matcher
and Career Sites gate still use different blocked sets" (T3.I cerrado
para el matcher; la divergencia restante es Notion ↔ repo, no
matcher ↔ `hard_blocks.json`) y "post-commit Git state and hooks remain
unverified" (working tree limpio; sin hooks activos; suite post-commit
396 verde).

**Limitación nueva:** el binding Implementation SHA ↔ contrato CANONICAL
está desajustado (§4.1) y la verificación de provenance no puede
detectarlo por diseño.

## 17. Operational boundary

The identity layer and synthetic normalizer tests have evidence, and the
integration is **already in `main`** (vía `e3a3348`) con suite completa
verde. This is not exhaustive LinkedIn coverage, does not demonstrate
live v2.0 acquisition, and does not establish production-ready Tracker
ingestion.

## 18. Expansion plan (not implemented)

A: restore a supported Chromium browser. B: authenticated acquisition
where appropriate. C: separate acquisition adapter from matcher. D:
coverage instrumentation (queries, cards, accepted, rejected,
duplicates, depth, errors, auth state). E: unified career-search
orchestration. F: additional sources only after LinkedIn is stable.
**[V]** ninguna de estas fases tiene implementación en `HEAD`.

## 19. Governance requirements

Keep acquisition, identity resolution, eligibility, normalization and
persistence distinct. Browser changes must not change blocked-employer
semantics. Identity changes need their own tests and evidence. Canonical
rules must not change to compensate for acquisition failure. A commit
created with plumbing commands must receive explicit review of the
checks/hooks that were bypassed.

**Añadido en rev. 5:**

- Un cambio al matcher **exige** nueva fila/versión en PROMPT_CANON con
  el Implementation SHA vigente. `verify_versions` V6′ no lo detecta
  (§4.1); mientras no se refuerce, el cumplimiento depende de disciplina
  humana.
- Los reportes de evidencia citados por un contrato CANONICAL deben ser
  inmutables o versionados por nombre (§6.1).

## 20. Non-goals

No exhaustive coverage guarantee; no authentication or anti-bot bypass;
no unlimited pagination; no treating every company-name mention as an
employer match; no inferring missing jobs from incomplete results; no
classifying acquisition failure as an empty result.

## 21. Open items

  -----------------------------------------------------------------------
  \#                      Item                    Tracker / estado
  ----------------------- ----------------------- -----------------------
  1                       Live v2.0 acquisition   **T3.L — ABIERTO**
                          (9 queries) not         (sin cambios)
                          demonstrated            

  2                       Baseline funnel: 35     Reconciliation Log —
                          records vs 24 validated **ABIERTO**, cifras
                          details; 198 IDs        verificadas y
                          without records         aritméticamente
                                                  consistentes (§10)

  3                       Matcher set vs          **T3.I — CERRADO**
                          `hard_blocks.json`      (§4.2). Residual
                          (Dockers divergence)    nuevo: re-sincronizar
                                                  LINKEDIN-RULES-002 §2
                                                  (Notion) y re-promover
                                                  el Implementation SHA
                                                  en PROMPT_CANON (§4.1)

  4                       Confirm post-commit Git **CS-HERMES-L1-03 —
                          state and hooks;        RESUELTO**: working
                          diagnose Git timeouts   tree limpio, sin hooks
                                                  activos, `HEAD` ==
                                                  `origin/main`, timeout
                                                  no reproducido.
                                                  Residual: los timeouts
                                                  de `git commit` no se
                                                  reprodujeron y quedan
                                                  sin causa raíz

  5                       Historical two          B5 / V27 — **NO_SOURCE**
                          `POST /v1/pages`        según el R1 original
                          investigation remains   (§D): búsqueda
                          `NO_SOURCE`,            exhaustiva en
                          non-blocking            `notion_cache.json`,
                                                  `notion_metrics.json`,
                                                  `feeds/`, `handoffs/`;
                                                  única referencia a
                                                  `/v1/pages` es un GET
                                                  del 2026-06-14. Sólo
                                                  resoluble con logs de
                                                  administración de
                                                  Notion

  6                       Existence and role of   **RESUELTO: no
                          `linkedin_search.py`    existe.** No está en
                                                  disco ni fue trackeado
                                                  en ningún commit del
                                                  repositorio. Pero
                                                  `PROMPT_CANON §2` lo
                                                  describe como parte de
                                                  la implementación ⇒
                                                  discrepancia
                                                  documentación ↔ repo

  7                       Agent family recorded   **VERIFICADO**: el R1
                          for Hermes in prior     original registra
                          evidence report         Hermes como ejecutor
                                                  (Nous Research,
                                                  `poolside/laguna-s-2.1:free`
                                                  en CS-HERMES-L1-02-R1)

  8 (nuevo)               Implementation SHA del  PROMPT_CANON /
                          contrato CANONICAL      gobernanza — ABIERTO
                          desajustado respecto    (§4.1)
                          del matcher en `HEAD`   

  9 (nuevo)               El reporte de evidencia reportes/ — ABIERTO
                          R1 fue sobrescrito por  
                          un auto-sync (§6.1)     
  -----------------------------------------------------------------------

## 22. Corrections log

  -----------------------------------------------------------------------
  Previous statement                  Current statement
  ----------------------------------- -----------------------------------
  `PromptA-v1.0+linkedin` was         `PromptA-v2.0+linkedin` is
  canonical                           canonical; v1.0 is the baseline
                                      feed prompt version **[V]**

  7 queries/233/12/21 represented     Those figures belong to the
  validated v2.0 runtime              2026-10-04 v1.0 baseline; funnel
                                      remains unreconciled **[V]**

  Blocked set includes Dockers        Dockers removed from
                                      `hard_blocks.json` by operator
                                      decision; matcher alignment remains
                                      open

  Accepted results classified as      Feed uses `status=candidate`;
  `NOT_BLOCKED`                       `NOT_BLOCKED` is a matcher state

  Ingestion does not work             v2.0 `accepted[]` normalizer
                                      integrated according to isolated
                                      commit report; post-commit
                                      state/hooks not independently
                                      verified

  No recent full-suite evidence       311 tests passed before the
                                      integration commit

  Dry-run archive may write to Notion T3.N changes archive to opt-in;
  by default                          local-only is intended default
  -----------------------------------------------------------------------

### Correcciones y adiciones de rev. 5

  -----------------------------------------------------------------------
  rev. 4                              rev. 5
  -----------------------------------------------------------------------
  Matcher alignment remains open      **CERRADO.** Dockers eliminado del
  under T3.I                          matcher por `7c4a170`; prueba de
                                      paridad añadida por `5ee2c5b`;
                                      4/4 verde **[V]**

  The matcher was not changed in      Cierto para `1e6ec75e…`, **falso
  this integration                    para `main`**: el matcher cambió
                                      en `7c4a170`/`5ee2c5b` ⇒ binding
                                      SHA `f7fa0513…` obsoleto (§4.1)

  Commit reported `1e6ec75e…`, tests  El commit existe y coincide
  311 passed before commit            exactamente, pero es un **objeto
                                      colgante superado**; el changeset
                                      llegó a `main` por `e3a3348`

  Post-commit Git state and hooks     **RESUELTO.** Working tree limpio;
  remain unverified                   no hay hooks activos; `HEAD` ==
                                      `origin/main`; 396 tests verdes

  No post-commit suite run is claimed **Hay corrida post-commit:** 396
                                      passed en `e61be89` **[V]**

  Dry-run archive may write to Notion Opt-in verificado también a nivel
  by default                          de código (`VANTAGE_ARCHIVE_DRYRUN_NOTION`)
                                      y cubierto por 4 pruebas

  The feed's `data_quality_warnings`  Leídas directamente: los 6 códigos
  (reported in prior notes, not      confirman la descripción y añaden
  independently re-read here)         `LOCATION_TEXT_INCONSISTENT`

  `linkedin_search.py` — To verify    **No existe** en disco ni en el
                                      historial de Git; PROMPT_CANON §2 lo
                                      describe como parte de la
                                      implementación

  `CS-HERMES-L1-02-R1` como           Válido, pero el archivo en esa ruta
  referencia de validación            fue sobrescrito; el contenido de
                                      integración se recupera de `e3a3348`
                                      (§6.1)

  Orchestrator invocations `--file`   No hay exclusión mutua en argparse;
  y `--ats workday` "mutually         el flujo ATS sobrescribe `--file`
  exclusive"                          en silencio (§9)
  -----------------------------------------------------------------------

### Changes in rev. 5 (vs. rev. 4)

-   Auditoría independiente contra fuentes primarias en `HEAD` `e61be89`
    (2026-10-16), con reproducción de la suite en ambos árboles.
-   **T3.I pasa a cerrado**; se documenta el residual Notion y, sobre
    todo, el **desajuste del Implementation SHA del contrato CANONICAL**.
-   Se establece que `1e6ec75e…` es un objeto colgante y que la
    integración vive en `main` por `e3a3348`.
-   Se resuelve CS-HERMES-L1-03: working tree limpio, sin hooks activos,
    `HEAD` == `origin/main`.
-   Se añade evidencia post-commit: 396 tests verdes.
-   Se documenta la **sobrescritura del reporte de evidencia R1**.
-   Se corrigen §9 (exclusión mutua de CLI) y §14, y se precisan §7/§8
    (orden de ramas del normalizador, validación todo-o-nada).
-   Se resuelven los ítems abiertos 6 (`linkedin_search.py`) y 7 (familia
    de agente), y se reubica el ítem 5 (B5/V27) con la evidencia del R1.
-   Live LinkedIn v2.0 acquisition sigue sin demostrarse.

## 23. Verification checklist (independent verifier) — con resultados rev. 5

| Ítem a confirmar | Resultado rev. 5 |
|---|---|
| Matcher file y funciones públicas | **[V]** `MatchStatus`, `MatchBasis`, `EmployerIdentityInput`, `MatchResult`, `normalize_identity`, `resolve_employer_identity`, `match_employer`, `BLOCKED_EMPLOYERS`, `CANONICAL_RULE_MAP` (`__all__`) |
| 27 matcher tests y evidencia de suite | **[V]** 27 en `1e6ec75e…` y en `HEAD`; suite total 311 → 396 |
| Blocked terms vs `hard_blocks.json` y LINKEDIN-RULES-002 §2 | **[V]** vs JSON (v1.1, sin Dockers, paridad automática). LINKEDIN-RULES-002 §2 es Notion: **[R]**, no releído |
| Identity states | **[V]** cuatro estados y orden de decisión |
| Baseline feed fields | **[V]** todas las claves listadas existen |
| Orchestrator CLI | **[V]** `--file`, `--ats workday`; dry-run default; sin mutex argparse |
| v2.0 envelope validation | **[V]** 4 arrays + `contract`/`schema`; rama al final |
| Accepted-only ingestion | **[V]** 20 pruebas |
| Reroute retention | **[V]** queda en el feed, sin ingestión |
| Dedupe y provenance | **[V]** `job_id` único (35/35); `source_type=linkedin` |
| Browser limits | **[V]** error literal y 3 intentos en CS-L1-RUNTIME-02 |
| Benefit Cosmetics case | **[V]** también en `data_quality_warnings` del feed |
| Canonical state vs coverage | **[V]** CANONICAL ≠ cobertura; fixture declara `live_acquisition: false` |
| Commit parent y file list exacto | **[V]** `e58dce1`, 9/1026/1 |
| Post-commit worktree | **[V]** limpio |
| Hooks bypassed por `commit-tree` | **[V]** no hay hooks activos |
| B5/V27 status | **[V]** `NO_SOURCE` en el R1 original; sólo resoluble con logs de Notion |
| **Nuevo:** binding SHA ↔ contrato | **[V] FALLA.** `f7fa0513…` ≠ matcher en `HEAD` (`88df0c45…`); V6′ no lo detecta |
| **Nuevo:** integridad del reporte R1 | **[V] FALLA.** Sobrescrito por `7efbd37`; original recuperable en `e3a3348` |
| **Nuevo:** existencia de `linkedin_search.py` | **[V] AUSENTE** en disco y en todo el historial de Git |

---

### Apéndice A — Comandos de reproducción

```bash
# Estado del repositorio
git -C "<repo>" rev-parse HEAD origin/main && git status --short
ls .git/hooks | grep -v '\.sample$' ; git config --get core.hooksPath

# El commit aislado y su relación con main
git cat-file -t 1e6ec75e335511be148ff92518a1cf298e615cf6
git log -1 --format='%H%n%P' 1e6ec75e335511be148ff92518a1cf298e615cf6
git branch -a --contains 1e6ec75e335511be148ff92518a1cf298e615cf6   # vacío
git diff --numstat e58dce1 1e6ec75                                   # 9/1026/1

# El changeset que sí está en main
git log --oneline -S "ACCEPTED" -- Layer_1/scripts/feed_processor.py   # e3a3348
git diff --name-status 1e6ec75 e3a3348

# Blobs del matcher
git rev-parse f7fa051:Layer_1/scripts/linkedin_identity_matcher.py
git rev-parse HEAD:Layer_1/scripts/linkedin_identity_matcher.py
git show f7fa051:Layer_1/scripts/linkedin_identity_matcher.py | grep -n Dockers

# Suites (reproducidas en esta revisión)
git worktree add --detach /tmp/verify-1e6ec75 1e6ec75e335511be148ff92518a1cf298e615cf6
(cd /tmp/verify-1e6ec75/Layer_1 && python -m pytest tests/ -q)   # 311 passed
python -m pytest Layer_1/tests/ -q                               # 396 passed
git worktree remove /tmp/verify-1e6ec75

# El reporte R1 original
git show e3a3348:reports/CS-HERMES-L1-02-R1_verification_report.md | head -40
```
