---
name: vantage-session-close
description: Use this skill whenever a VANTAGE session is wrapping up — the operator says something like "cerramos aquí", "close session", asks for a handoff, the conversation is approaching token limits, or any Notion write/structural change was made during the session. Runs the canonical VANTAGE close-out sequence (Census → Changelog/version bump → version-consistency check → pending-items summary → SESIÓN COMPLETADA) before ending the chat. Do NOT invent close-out steps outside this sequence; if something doesn't fit the sequence, surface it to the operator instead of silently improvising.
---

# VANTAGE — Session Close Protocol

This skill encodes the close-out sequence VANTAGE actually follows, sourced directly from canon (`KERNEL:CEDULA-DIGITAL`, `KERNEL:SYNC-RULE`, `MANUAL:HEALTHCHECK-001 §10.4`) — not an invented checklist. If a step below doesn't apply this session, say so explicitly rather than skipping silently.

## When this triggers

- Operator signals the session is ending ("cerramos", "close", "eso es todo por hoy")
- Token budget is approaching ~90% (per memory: handoff docs generated at this point)
- Any write, structural change, or ID state-change happened this session (bug closed, ticket resolved, doc edited)
- Operator explicitly asks for a handoff or session summary

## The sequence (in order — do not reorder)

### 1. Inventory what changed this session
Before anything else, list internally:
- Any Notion writes made (which pages/DBs, Class A vs Class B fields)
- Any ticket/bug state changes (open → resolved, new ticket logged)
- Any ID state changes (a KERNEL/CANON/MANUAL section moved from Stub → Ok, or was newly created)

If nothing changed (pure read/consult session), skip to step 5 directly — no Census/Changelog work needed.

### 2. Census before Changelog — never the reverse
Per `MANUAL:HEALTHCHECK-001 §10.4`: if any ID changed state this session, the Census must be regenerated **before** any Changelog entry is written. This is a hard ordering rule, not a suggestion.

- If Terminal is available: run
  ```bash
  source ~/Documents/04-Vantage_CV/Layer_1/.venv/bin/activate
  cd ~/Documents/04-Vantage_CV/Layer_1/scripts
  python3 generate_census.py
  ```
- If Terminal is NOT available at this moment: do not fake it. Mark the affected ticket(s) as **Blocked-Census** rather than closing them. Say this explicitly to the operator — do not close a ticket in Notion that changed an ID's state without a Census re-run.

### 3. Changelog entry + version bump (only if a Changelog entry is warranted)
Per `KERNEL:CEDULA-DIGITAL`: any new entry in V-CHANGELOG must, in the same operation, update the `Versión` property of that page. This is the single source of truth for system version — never a fixed value elsewhere.

- Draft the Changelog entry (DRY RUN — show before/after, wait for APROBAR_WRITE per the standard gate).
- Confirm the version bump target with the operator if it's not obvious (patch vs. minor).

### 4. Version-consistency check (Regla de Versión Única)
Per `KERNEL:SYNC-RULE`: after any version bump, the six foundational docs (MANUAL, TECHNICAL KERNEL, CAREER CANON, SYSTEM PROMPT, ID CENSUS, CHANGE LOG) must all carry the exact same version as the Changelog. If this session's changes leave any of them behind, flag it now — don't let it carry into the next session's sync as a silent discrepancy (that would trip `KERNEL:SYNC-RULE` at next bootstrap).

### 5. Pending-items summary (hecho vs. pendiente)
Per `MANUAL:HEALTHCHECK-001 §10.4`: if there were doc or DB changes this session, present an unprompted summary — done vs. pending — the operator shouldn't have to ask for this. Format:

```
COMPLETADO ESTA SESIÓN:
- [item]

PENDIENTE:
- [item] — [por qué quedó pendiente / qué se necesita para resolverlo]
```

If the session was read-only, a shorter confirmation is enough — no need to force this template.

### 5.5 Staleness check — is this skill itself still accurate?
This skill was derived from specific canon sources: `KERNEL:CEDULA-DIGITAL`, `KERNEL:SYNC-RULE`, `MANUAL:HEALTHCHECK-001 §10.4`. If this session touched any of those — edited the Kernel's Census/Changelog ordering rule, changed the version-bump contract, or modified the Regla de Versión Única — flag it in the pending-items summary:

```
⚠️ SKILL DESACTUALIZADA: esta sesión modificó [KERNEL:X], que es fuente de la skill
vantage-session-close. Pide actualización de la skill antes de confiar en su próxima corrida.
```

Do not silently rewrite the skill mid-session. Surfacing the drift is enough — the operator decides when to request the update.

### 6. Session Ledger Update
Write to VANTAGE:SESSION-LEDGER: status = CLOSED,
pending_summary = [texto completo del bloque
COMPLETADO ESTA SESIÓN / PENDIENTE producido en el paso 5].

This is the persistent anchor of the close summary — it does not
depend on conversational memory or Claude Memory for the next
session's bootstrap to read it correctly.
This write is infrastructure housekeeping (see KERNEL:SESSION-LEDGER)
— does not require APROBAR_WRITE, does not touch Class A/B fields.

### 7. Close
End with the literal, unadorned line the operator recognizes as the close signal:

```
SESIÓN COMPLETADA → nuevo chat.
```

Nothing after this line. Per session-discipline (atomic sessions): don't tack on a new task, don't ask "anything else?", don't soften it with extra commentary.

## Guardrails

- Never skip step 2 (Census-before-Changelog) to save time — this is a canon-enforced ordering rule, not a nice-to-have.
- Never write a Changelog entry without a version bump in the same operation.
- Never close a ticket that changed an ID's state if Census couldn't be regenerated — mark it Blocked-Census instead.
- If you're unsure whether something counts as an "ID state change" worth this whole sequence, ask rather than guess — false negatives here create the exact version-drift problem `KERNEL:SYNC-RULE` exists to catch.