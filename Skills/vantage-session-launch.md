---
name: vantage-session-start
description: Use this skill whenever a new VANTAGE session begins — immediately after opening a new Claude chat, after a Session Close handoff, or whenever the operator says "bootstrap", "start session", "continuemos", or "rehydrate". Runs the canonical VANTAGE startup sequence (Health Check → Version Sync → Latest Changelog → Pending Items → Memory Consistency → Census Check → Session Context → READY) before any operational work begins. Do NOT invent bootstrap steps outside this sequence; if something cannot be verified, surface it to the operator instead of silently assuming consistency.
---

# VANTAGE — Session Start Protocol

This skill reconstructs the operational state of VANTAGE before work begins. Its purpose is not to summarize documentation, but to verify that the system is internally consistent and safely rehydrated after the previous session.

## When this triggers

- Immediately after opening a new Claude chat
- Operator says "bootstrap", "start session", "continuemos", "rehydrate", "cargar contexto"
- A Session Close handoff was generated in the previous conversation
- Before any structural work, Notion write, or architectural decision

## The sequence (in order — do not reorder)

### 0. Session Ledger Check

Read `VANTAGE:SESSION-LEDGER` (most recent entry).

If `status == OPEN` (from previous session):

```
WARNING — SESIÓN PREVIA NO CERRADA

La última sesión no ejecutó Session Close correctamente.
El Pending Items de este bootstrap puede estar incompleto.
Revisar manualmente el último intercambio de la conversación
anterior antes de continuar con confianza plena.
```

Write: `session_id` = [nuevo, generado] · `status` = OPEN · `opened_at` = [timestamp actual]

This write is infrastructure housekeeping (see `KERNEL:SESSION-LEDGER`) — does not require APROBAR_WRITE, does not touch Class A/B fields.

---

### 1. Health Check

Verify that the six foundational documents are accessible.

- MANUAL
- TECHNICAL KERNEL
- CAREER CANON
- SYSTEM PROMPT
- ALIASES
- CHANGE LOG

Report:

```
Health Check

✓ MANUAL
✓ TECHNICAL KERNEL
✓ CAREER CANON
✓ SYSTEM PROMPT
✓ ALIASES
✓ CHANGE LOG
```

If any document cannot be accessed, stop the bootstrap and report it explicitly.

---

### 2. Version Consistency Check

Read the current version from every foundational document.

Apply `KERNEL:SYNC-RULE`.

Expected result:

```
Version Check

MANUAL.............vX.X.X
KERNEL............vX.X.X
CAREER............vX.X.X
PROMPT............vX.X.X
ALIASES...........vX.X.X
CHANGELOG.........vX.X.X

PASS
```

If versions differ:

```
FAIL

List every mismatching document.

Do not continue assuming consistency.
```

---

### 3. Latest Changelog

Read only the most recent Changelog entry.

Summarize:

- latest version
- purpose of the change
- high-level modifications

Do not summarize older history.

---

### 4. Pending Items

Recover pending work from `VANTAGE:SESSION-LEDGER.pending_summary` — this is the primary source, not conversational memory of the previous session.

Return exactly what remains pending.

Do not reprioritize.

Do not create new tasks.

If the Ledger shows `pending_summary` empty AND `status` was correctly CLOSED in the previous session:

```
No pending items.
```

If the Ledger shows `status == OPEN` (see step 0 WARNING) but `pending_summary` is empty or missing:

```
PENDING ITEMS UNKNOWN

La sesión anterior no cerró correctamente y no dejó resumen.
No asumir "sin pendientes" — confirmar con el operador antes de proceder.
```

---

### 4.5 Tracker Priority Snapshot

Group Bug Tracker + Tasks Tracker by `Prioridad` (CRÍTICO / ALTO / MEDIO / BAJO / Sin Prioridad) — same logic as `KERNEL:HEALTH-CHECK-002`.

Explicit detail (title) only for CRÍTICO and ALTO; MEDIO/BAJO/Sin Prioridad count only.

If ≥1 CRÍTICO ticket is open, it must appear in Session Context (step 7) before `VANTAGE READY` is emitted.

If zero tickets exist in either tracker:

```
Tracker Snapshot

No open tickets.
```

---

### 5. Memory Consistency

Check Claude Memory against the latest documented system state.

Verify:

- resolved items
- persistent decisions
- architectural conventions
- permanent operator preferences

Additionally: any Memory item whose origin predates the most recent `V-CHANGELOG` entry touching the same section/canonical ID is flagged as potentially stale.

If everything matches:

```
Memory Check

PASS
```

If inconsistencies exist:

```
WARNING

Memory differs from documented state.

List the discrepancy.
```

If a Memory item is older than the relevant Changelog entry:

```
MEMORY STALE: [item]

El Changelog más reciente en esta sección es posterior a este recuerdo.
Confirmar vigencia con el operador.
```

Never silently overwrite either source.

---

### 6. Census Validation

Determine whether the latest Changelog contains any ID state changes.

Examples:

- Stub → Ok
- New ID
- Deprecated ID
- Removed ID

If yes:

```
CENSUS CHECK

Regeneration required.
```

If not:

```
CENSUS CHECK

SKIPPED
```

Do not regenerate Census automatically unless the workflow explicitly allows it.

---

### 7. Session Context

Produce a concise operational snapshot.

Example:

```
SESSION CONTEXT

Version:
vX.X.X

Synchronization:
PASS

Pending items:
7

Latest change:
[one sentence]

Warnings:
0
```

Keep this section compact.

---

### 8. Ready

If every previous step succeeded, finish with the literal line:

```
VANTAGE READY

You may begin.
```

Nothing after this line.

If bootstrap failed, replace Ready with:

```
BOOTSTRAP INCOMPLETE

Resolve the issues above before continuing.
```

## Guardrails

- Never assume documentation is synchronized without checking versions.
- Never infer pending work from memory alone.
- Never modify Notion during bootstrap.
- Never regenerate Census unless the workflow explicitly requires it.
- Never repair inconsistencies automatically.
- If any foundational document is unavailable, stop and report the issue rather than guessing.
- Bootstrap is verification only; operational work begins after `VANTAGE READY`.