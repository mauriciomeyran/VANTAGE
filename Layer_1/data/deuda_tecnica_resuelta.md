# Deuda Técnica Resuelta — Post-Auditoría
**Fecha:** 2026-08-10  
**Contexto:** Dictamen de consistencia documental (Reference Librarian) identificó deuda técnica residual tras H1-H4

---

## Estado de Resolución

### ✅ Resuelto (Prioridad Alta)

**1. Divergencia de Runners**
- **Problema:** `layer_1_run_dash.py` v7.5 con lógica vieja vs `layer_1_run.py` v8.0 con fixes H1/H2
- **Solución:** Actualizado `layer_1_run_dash.py` a v7.6:
  - gate() con umbral de Score (H1 FIX: ≥60 CREATE, 40-59 REVIEW_NEEDED, <40 BLOCKED)
  - Protección de terminales extendida (H2 FIX: gate_logic() + evaluate_rejection_status())
  - "PROTECCIÓN TOTAL" reemplazada por contrato KERNEL:GATE-DECISION-010
- **Archivo:** Dashboard/scripts/layer_1_run_dash.py

**2. Divergencia de Vocabulario**
- **Problema:** Kernel/docs decían "Para Revisar" vs código usa "REVIEW_NEEDED"
- **Solución:** Normalizado a "REVIEW_NEEDED" en:
  - Kernel.md (L415)
  - Change Log.md (L20)
  - Manual.md (L161)
- **Consistencia:** Vocabulario unificado entre Kernel/código/documentación

---

### ⏳ Pendiente (Prioridad Media/Baja)

**3. Observabilidad (H9)**
- **Problema:** Falta de timestamps por transición y logs estructurados
- **Estado:** No implementado
- **Impacto:** Trazabilidad limitada de transiciones
- **Recomendación:** Agregar campo `Last_Gate_Run`/`Gate_History` (Class B)

**4. Transición APPLIED Automática**
- **Problema:** Status=Postulado → Gate_Decision=APPLIED sigue siendo proceso manual
- **Estado:** No implementado
- **Impacto:** Inconsistencia entre transición documentada (GATE-DECISION-011 fila 11) y comportamiento real
- **Recomendación:** Implementar edge-triggered cuando Status cambia a Postulado

---

## Veredicto Actual

**Estado:** **SINC_ALTA** (de SINC_PARCIAL → SINC_ALTA)

**Cambios aplicados:**
- ✅ Doble semántica de gate eliminada (runners sincronizados)
- ✅ Vocabulario unificado (Para Revisar → REVIEW_NEEDED)
- ✅ Contrato KERNEL:GATE-DECISION-010 respetado en ambos runners

**Restante:**
- ⏳ Observabilidad mejorada (requiere diseño de schema)
- ⏳ Transición APPLIED automática (requiere decisión de diseño)

---

## Documentación

**Change Log:** Entrada v9.20.0 documentando sincronización de runners y vocabulario  
**Kernel.md:** Vocabulario normalizado a REVIEW_NEEDED  
**Manual.md:** Vocabulario normalizado a REVIEW_NEEDED  
**layer_1_run_dash.py:** v7.6 sincronizado con layer_1_run.py v8.0

---

**Generado con Devin AI — 2026-08-10**
