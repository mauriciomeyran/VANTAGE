# VANTAGE — Reporte de Saneamiento CV-B (Batch Septiembre 2026)

**Fecha de corte:** 2026-09-06 | **Handoff:** HO-000036 | **Serial anterior:** HO-000034 | **Versión del reporte:** v1.1 (cierre)

---

## ESTADO FINAL POR ARCHIVO (18/18)

| Archivo | Idioma/Verbal | Gates 6/7 (bold/italic) | Identidad Figma (68 nodos) | Estado global |
|---|---|---|---|---|
| Confidencial_Gerente_de_Visual_Merchandising | ✅ LIMPIO | ✅ LIMPIO (11 métricas bold) | ✅ OK | ✅ COMPLETO — referencia |
| Beyond_Gerente_Marketing_...BELLEZA | ✅ LIMPIO | ✅ Aplicado (15 métricas) | ✅ OK | ✅ COMPLETO |
| Confidencial_Gerente_Nacional | ✅ LIMPIO | ✅ Aplicado (20 métricas) | ✅ OK | ✅ COMPLETO |
| Eurokor_VM_Skincare | ✅ Corregido | ✅ Aplicado (13 métricas) | ✅ OK | ✅ COMPLETO |
| GDC_Inmobiliaria_Auxiliar_Experiencia_VM | ✅ Corregido (ver nota GDC) | ✅ Aplicado (17 métricas) | ✅ OK | ✅ COMPLETO |
| IKEA_Visual_Merchandiser | ✅ LIMPIO | ✅ Aplicado (15 métricas) | ✅ OK | ✅ COMPLETO |
| Inditex_Imagen_y_Visual_Merchandiser_CDMX | ✅ Corregido | ✅ Aplicado (13 métricas) | ✅ OK | ✅ COMPLETO |
| Intimissimi_Visual_Merchandising_Coordinator | ✅ Corregido | ✅ Aplicado (18 métricas) | ✅ OK | ✅ COMPLETO |
| Juguetron_Visual_Merchandiser | ✅ LIMPIO | ✅ Aplicado (16 métricas) | ✅ OK | ✅ COMPLETO |
| Multicont_Supervisor_...Cdmx | ✅ LIMPIO | ✅ Aplicado (12 métricas) | ✅ OK | ✅ COMPLETO |
| Multicont_Visual_Merchandiser | ✅ Corregido | ✅ Aplicado (11 métricas) | ✅ OK | ✅ COMPLETO |
| ServiciosAndreiMoygo_...Desarrollo_Tienda | ✅ Corregido | ✅ Aplicado (15 métricas) | ✅ OK | ✅ COMPLETO |
| Tendam_Responsable_...boutiques | ✅ Corregido (tagline 2:5 incl.) | ✅ Aplicado (12 métricas) | ✅ OK | ✅ COMPLETO |
| Walmart_Analista_Diseno_Modular_Planogramas | ✅ Corregido | ✅ Aplicado (14 métricas) | ✅ OK | ✅ COMPLETO |
| ZaraHome_VisualMerchandiser | ✅ Corregido | ✅ Aplicado (14 métricas) | ✅ OK | ✅ COMPLETO |
| HM_Junior_Retail_Designer | 🟢 EN legítimo (HANDOFF.idioma=EN) | ✅ Auditado y corregido esta sesión (nombre/empresas/roles/períodos bold+italic, 3 métricas bold) | ✅ OK | ✅ COMPLETO |
| HM_Retail_Designer | 🟢 EN legítimo | ✅ Auditado y corregido esta sesión (mismo patrón que HM Junior, 3 métricas bold) | ✅ OK | ✅ COMPLETO |
| SARELLY_Global_Retail_Experience_VM_Manager | 🟢 EN legítimo | ✅ Auditado esta sesión — formato ya era correcto, solo faltaban 5 métricas bold | ✅ OK | ✅ COMPLETO |

**18/18 archivos: COMPLETOS (idioma + tiempo verbal + Gates 6/7 + Identidad Figma).**

---

## AUDITORÍA DE IDENTIDAD FIGMA (nueva esta sesión)

Ejecutada contra registry_seed.json (68 nodos) y validada adicionalmente contra un CV-B de control ya confirmado funcional en Figma (Dior/Christian Dior LVMH v2), que resultó 100% idéntico al registry en membership y orden.

Los 18 archivos del batch pasaron los 3 chequeos sobre esa misma referencia:
- Conteo: 68/68 nodos en los 18 archivos.
- Membership: mismo set exacto de figma_text_id que el registry en los 18.
- Orden de secuencia: idéntico al control validado en los 18.
- Duplicados de ID dentro de un mismo archivo: 0 en todo el batch.

Ningún patch de saneamiento (esta sesión ni sesiones previas) rompió Slot Integrity (CANON:OUTPUT-CONTRACT-001 punto 2).

## CORRECCIÓN DE RAÍZ EN triaje_v3.py (esta sesión)

Tres causas raíz identificadas y corregidas en el script (no parcheadas archivo por archivo):
1. FRASES_EXENTAS no cubría "Flagship Store" — causaba falsos positivos de IDIOMA_MIXTO_REAL en 11+ archivos.
2. limpiar_exentas() era case-sensitive — "flagship store" en minúsculas no quedaba exento (2 casos adicionales: ServiciosAndrei/Moygo, GDC). Corregido a re.sub(..., flags=re.IGNORECASE).
3. PRESENTE_PROHIBIDO marcaba "Desarrollo" como verbo incluso en frases nominales ("Desarrollo de Tienda", "Desarrollo y apertura de...", "Desarrollo de Equipos") — 6 falsos positivos en 2 archivos. Corregido con lookahead/lookbehind que excluye "Desarrollo" seguido de de/y o precedido de "de ".

Tras las 3 correcciones, re-corrida contra los 18 archivos activos (excluyendo los 3 EN por diseño del script): 14/14 archivos ES → LIMPIO (confirmado en terminal por el operador).

## VERIFICACIÓN DE DOBLE-BOLD (esta sesión)

Barrido sistemático (no muestral) de los 18 archivos: 0 ocurrencias de doble-bold y 0 líneas con conteo impar de asteriscos dobles (bold roto/asimétrico).

---

## CASO GDC — resuelto, contexto histórico

HANDOFF-A original bloqueaba con REVISIÓN HUMANA REQUERIDA (VM_Scope discrepante + flag AGREGADOR_STATUS_401). Operador confirmó 2026-09-05: vacante activa, autoriza continuar. CV-A actualizado con decisión documentada. CV-B corregido después de la autorización, no antes. Recomendación pendiente: Gate 0 en vantage-cv-b v10.2.1 (futura) que lea "Próximo paso" del HANDOFF-A antes de generar.

## SKILL VIGENTE

vantage-cv-b v10.2.0 (Auto-Verificación Mecánica, 10 gates), registrado en SP §01.3 SP:SKILL-VERSION-PIN.

## ARTEFACTOS DE ESTA SESIÓN

_saneamiento_reports/: triaje_v3.py (parcheado, 3 correcciones de raíz), triaje_v3_sin_falsos_positivos.csv (regenerado, 14/14 LIMPIO), reemplazo_global_log.csv, patch_verbal_log.csv. Backups: .bak por archivo individual (Eurokor, ServiciosAndrei/Moygo, Tendam, Multicont VM, HM Junior, HM Retail Designer, SARELLY), triaje_v3.py.bak.

---

## CHANGELOG

- 2026-09-06 04:02 CDMX — v1.1: Cierre del batch. Los 3 pendientes de Prioridad 1/2/3 y el pendiente de FRASES_EXENTAS (v1.0) quedan resueltos. 18/18 archivos COMPLETO. Sin próximos pasos obligatorios pendientes de esta iniciativa — batch cerrado.
- 2026-09-05 — v1.0: Estado inicial post-sesión de saneamiento de contenido/idioma/formato (15/18 completos, 3 EN sin auditar, Identidad Figma sin ejecutar).
