# HANDOFF RETOMADA — Devin nuevo, desde G2 · 2026-09-12

Instancia previa agotó tokens tras G0/G1 + esqueleto + PREGUNTAS_ABIERTAS (10 Q).
Su rama/tree puede contener trabajo pusheado o no — verificar (§Órdenes-1), no asumir.
Contrato vigente: `CONTRATO_DEVIN_REEMPLAZO_TOTAL_2026-09-12` + enmiendas abajo (rango
contractual). Autorizaciones de Mau ya registradas: (a) implementación completa, cero
recorte; (b) blockers ajenos al tracker se ignoran (los 8 IDs de tests ajenos fallidos
deben listarse en tu primer reporte — requisito heredado, sigue vigente).

## Órdenes primeras (en orden, antes de codear)

1. **Base + rescate:** `git log --oneline -1`, `git status --short`, rama de trabajo
   (fresca desde HEAD si no hay nada rescatable). Busca trabajo previo:
   `git branch -r | grep -i devin` + `git log --oneline -5 <rama>` por cada una.
   Adopta lo pusheado (esqueleto, PREGUNTAS); reporta qué hallaste / qué no.
2. **Re-verifica G0/G1 en TU checkout** (no heredes verdes): suite tracker completa,
   esperado 39 passed + lista exacta de los 8 fallidos ajenos (IDs).
3. **Recrea `PREGUNTAS_ABIERTAS.md`** desde §Resueltas (vinculantes — prohibido re-decidir).
4. **Reanuda en G2.** Gates G2→G10 del contrato, sin cambios.

## Resueltas Q-1–Q-10 (decisión final, no reabrir)

- **Q-1 Source_Type␣:** RENOMBRAR a limpio con migración (§4-v1 manda; decisión previa
  contraria queda revocada). Código nuevo usa limpio + actualiza lectores/escritores;
  rename del schema vivo vía Claude/MCP ordenado ANTES del cutover (dependencia en G8).
- **Q-2 Target→Objetivo:** ya ejecutado y verificado en prod (v9.21.56 + censo T1, 0 filas
  Target). Nada que mapear; código as-is; rationale actualizado.
- **Q-3 Holding:** curar (select alias_map o vacío); REGLA: holdings reales (Nike Inc.,
  LVMH) se migran, jamás se vacían; placeholders → vacío. Criterio por categoría vive en
  Task `3d8938be` (Mau lo cierra ahí).
- **Q-4 bloqueo Class-B/REVIEW_NEEDED:** NO implementar, ACEPTADO (Mau no vetó) — CONDICIONAL
  a derogar/reescribir `KERNEL:GATE-DECISION-010` en G9. Sin eso, gate rojo.
- **Q-5 ventana manual:** "desde último run exitoso" + OBLIGATORIO writes condicionados a
  diff real + test anti-reescritura (§2.3-v1 prerrequisito; sin esto el mecanismo falla mudo).
- **Q-6 un re-query + snapshot:** confirmado.
- **Q-7 bug día/mes:** no tocar, portar llamada. Confirmado.
- **Q-8 dedup unificado:** confirmado (survivor L1>L2>L3>N/A + `is_mutable`; consolidate a
  `Archive/`, no rm). Dependencias = grep tuyo.
- **Q-9 class_b_guard:** generalizar a TODAS las vías PYTHON en código; MCP = exención
  documentada con control procedural (APROBAR_WRITE + cláusula). No afirmes cierre-en-código
  de lo procedural.
- **Q-10 batch_operations:** retirar (one-shot versionado o `Archive/`); disposición incluye
  case `batch` en pipeline.sh + nota glosario (referencia viva confirmada).

## Enmiendas vinculantes (causa: muerte por tokens con trabajo sin pushear)

- **E1 push-por-gate:** ningún gate es VERDE hasta commiteado + pusheado a tu rama. Cada
  reporte de gate incluye su commit SHA. Push temprano, push seguido. Si mueres, el
  siguiente retoma de tu rama, no de cero.
- **E2 evidencia primero:** comandos + outputs crudos antes que prosa; lotes chicos
  (la instancia previa murió redactando). Reporte por gate, no ensayo final.
- **E3 base propia:** G0/G1 se re-corren siempre (§Órdenes-2), aunque vengan "verdes" de
  otra instancia o máquina.

Prohibiciones §3 y gates §4 del contrato, intactos. Primer reporte esperado: base +
hallazgos de rescate + G0/G1 re-corridos + path de PREGUNTAS recreado + G2 iniciado.