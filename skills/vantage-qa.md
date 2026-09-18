---
name: vantage-qa
description: Auditoría de calidad final canónica de VANTAGE (KERNEL:TRIGGER-003) sobre un CV en PDF antes de postularlo. Usar cuando el operador invoque el trigger "QA [PDF]", adjunte un PDF de CV pidiendo revisión final, o pida verificar que un CV ya construido cumple con el Career Canon antes de enviarlo a una vacante. Emite un veredicto binario GO/NO-GO. No usar para el análisis inicial de vacante (eso es vantage-cv-a) ni para construir el CV (eso es vantage-cv-b) — esta skill solo audita un PDF ya terminado.
---

# VANTAGE — Skill QA (Verificación Canónica)

ID Canónico: `KERNEL:TRIGGER-003` · Trigger: `QA [PDF]`
Versión de alineación: v9.17.0 (patch post-mortem 2026-08-19 — BUG_TICKET, ver Bug Tracker)

## Responsabilidad

Última fase antes de postulación. Audita un CV en PDF ya construido contra el Career Canon y el Output Contract, y emite un veredicto binario GO/NO-GO con observaciones. No corrige el CV — reporta.

> Nota de sincronización: Kernel (`KERNEL:TRACKER...`) y Manual (`MANUAL:WEEKLY-FLOW-003`) referencian un "checklist de 6 ítems" — cifra desactualizada. El checklist vigente tiene **7 ítems** desde v9.16.0 (Anti-cloning agregado como ítem 7). Corregir la cifra en Kernel/Manual, no reducir este checklist.

## Regla Anti-Ambigüedad (nuevo, v9.17.0)

Cada uno de los 7 ítems se evalúa en **una sola pasada** contra la lista canónica
exacta (ej. Hard Blocks: L'Oréal, Levi's/Dockers, Palacio de Hierro — nombre
literal, no interpretación laxa).

- **Prohibido narrar reconsideración dentro del veredicto** — frases como "sin
  embargo," "corrijo a," "en rigor no hay violación" dentro de la tabla o el
  cuerpo del reporte indican que el chequeo no se hizo con la lista canónica
  desde el inicio.
- Si hay duda genuina sobre un ítem, el resultado es **FAIL** con nota "requiere
  confirmación humana" — nunca un PASS auto-justificado en el mismo mensaje.
- Esto no impide reportar contexto (ej. "menciona L'Oréal como historial, no
  como target — ver ítem 4 nota") pero el veredicto del ítem mismo no se
  negocia en vivo.

## Separación QA ↔ CV-B (nuevo, v9.17.0)

Un FAIL en QA **nunca se resuelve regenerando CV-B en el mismo turno** por
instrucción implícita o por inercia conversacional. El output correcto de un
NO-GO es la lista priorizada de correcciones (ya requerida en el formato de
salida) — y ahí termina la responsabilidad de esta skill.

La regeneración de CV-B con esas correcciones como input requiere una
invocación explícita separada del operador (mismo principio de Single-Item
Processing que ya rige `vantage-cv-b`, aplicado aquí al handoff QA→CV-B).
Razón: colapsar QA y CV-B en el mismo turno fue la causa del loop de
auto-rechazo detectado 2026-08-19 (Claude generando CV-B, rechazándolo en QA,
y "corrigiendo" sin cambio real verificable).

## Input requerido

Archivo PDF del CV terminado. Si no está adjunto o el path no existe en `/mnt/user-data/uploads/`, solicitarlo antes de proceder — no asumir contenido.

Lee el PDF con las herramientas de computer use disponibles (ver skill `pdf-reading` si el contenido no está ya en contexto).

Si existe un HANDOFF de `vantage-cv-a` para esta vacante, úsalo como referencia para los ítems 3 y 5 — incluyendo el campo `observaciones` si tiene contenido (discrepancias que el operador ya conocía al momento del análisis).

## Checklist Canónico de 7 Ítems

Recorre los 7 ítems en orden. Para cada uno, documenta el resultado (PASS / FAIL / N/A con razón), aplicando la Regla Anti-Ambigüedad arriba.

### 1. Invarianza estructural
¿Los subtítulos y headers del PDF coinciden con el Golden Skeleton (`CANON:OUTPUT-CONTRACT-002`, numeración real `2:X`/`3:X`)? Verifica que no se hayan fusionado, dividido, renombrado o reordenado secciones respecto a la estructura canónica. Incluye verificar que el tercer párrafo de perfil (`2:10`) no sea una duplicación verbatim del segundo (`3:13`) — si el CV-B correspondiente no tenía material para un tercer párrafo distinto, el slot debe mostrar `[PENDING DATA]` o estar vacío, nunca repetir el párrafo anterior.

### 2. Orden cronológico
¿La trayectoria (Experience) sigue orden cronológico absoluto, sin reordenamiento estratégico? Referencia: `CANON:CAREER-TIMELINE` — C01 (2025–2026) → C02 (2022–2023) → C03 (2018–2021) → C04 (2017–2018) → C05 (2012–2017), en orden inverso-cronológico estándar de CV (más reciente primero). Verifica que ningún rol se haya movido de posición para "verse mejor" ante el JD.

### 3. Cobertura JD
Si hay un HANDOFF de CV-A disponible para esta vacante, mapea las keywords estratégicas identificadas ahí (`JD_keywords_top6`) contra el texto del PDF. ¿Están presentes las que el HANDOFF marcó como matches directos? Revisa también si `observaciones` del HANDOFF señala algo que el CV-B debía reflejar y no lo hizo. Si no hay HANDOFF disponible, marca este ítem como N/A y anótalo en observaciones — no infieras cobertura sin el HANDOFF de referencia.

### 4. Hard Blocks — exclusiones de marcas protegidas
Confirma que el CV no está siendo preparado para ni menciona como target actual a: **L'Oréal (todas las divisiones), Levi's/Dockers, El Palacio de Hierro** (Hard Blocks confirmados en `MANUAL:DATA-MANAGEMENT`), ni a roles store-level sin alcance estratégico o multi-tienda.

> Nota: Aéropostale NO es un Hard Block — confirmado con el operador 2026-08-07. Cualquier referencia previa que lo incluyera (memoria operativa u otros briefs) era un error; el historial en Aéropostale sigue siendo válido como contenido del CV (Experience Records C04) y las vacantes de esa empresa no se excluyen por este criterio.

Nota: el historial laboral en estas empresas SÍ es válido como contenido del CV (Experience Records C01, C03, C04, C05) — el bloqueo aplica solo a que el CV se esté preparando *para* una vacante nueva ahí, no a mencionar el pasado. Este es el único contexto permitido dentro del veredicto del ítem (ver Regla Anti-Ambigüedad) — se declara una vez, no se "negocia" línea por línea.

### 5. No inferencia / Canon
¿Todo dato en el PDF (métricas, fechas, nombres, certificaciones) tiene respaldo directo en el Career Canon? Revisa especialmente:
- Certificaciones: solo son válidas `CERT01` (ALDO Group, Montréal, 2014) y `CERT02` (AutoCAD & SketchUp Essentials, LinkedIn Learning, 2024) — `CANON:UF-003`. Cualquier otra certificación en el PDF es FAIL inmediato.
- Métricas (KPI01–KPI08): deben coincidir exactamente con los valores canónicos, sin redondeos ni inflación.
- Email canónico: `mauricio.meyran@icloud.com` (`CANON:UF-002`).

### 6. Formato y completitud
Verificación visual y técnica: ¿el PDF se ve completo (sin cortes de texto, overflow, o secciones a medio renderizar)? ¿No quedan placeholders como `[PENDING DATA]` visibles en el documento final salvo que sea un slot genuinamente sin datos (ver ítem 1, nota sobre `2:10`)?

### 7. Diferenciación de Contenido (Anti-cloning, v9.16.0)
Compara el texto del PDF contra los demás entregables del mismo batch (otros CV-B generados en la misma sesión o corrida). Un match verbatim >80% en la sección Experience frente a cualquier otro entregable del batch resulta en FAIL automático de este ítem — independientemente del Positioning Mode. Si no hay otros entregables del batch disponibles para comparar, marca N/A y anótalo en observaciones.

## Output — Veredicto

Estructura del reporte (en el chat, no requiere archivo descargable salvo que el operador lo pida):

```
## QA Report — [nombre del archivo]

| # | Ítem | Resultado | Observaciones |
|---|---|---|---|
| 1 | Invarianza estructural | PASS/FAIL | |
| 2 | Orden cronológico | PASS/FAIL | |
| 3 | Cobertura JD | PASS/FAIL/N/A | |
| 4 | Hard Blocks | PASS/FAIL | |
| 5 | No inferencia / Canon | PASS/FAIL | |
| 6 | Formato y completitud | PASS/FAIL | |
| 7 | Diferenciación de Contenido | PASS/FAIL/N/A | |

## Veredicto: GO / NO-GO

[Si NO-GO: lista priorizada de qué corregir antes de re-someter a QA.
Corrección se ejecuta vía invocación explícita separada de CV-B — ver
Separación QA↔CV-B arriba. Esta skill no regenera el CV.]
```

Regla de veredicto: **un solo FAIL en cualquier ítem = NO-GO.** No hay veredictos parciales o "GO con reservas" — eso viola el invariante de estado binario del brief original.