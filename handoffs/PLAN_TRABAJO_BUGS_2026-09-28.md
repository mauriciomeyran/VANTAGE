#!/usr/bin/env python3
"""
VANTAGE — Plan de Trabajo: Bug Tracker (3 fases).
Generado: 2026-09-28.
Fuente: BUG TRACKER Notion (44 tickets), Kernel.md, Manual.md,
         System Prompt.md, Changelog Archivo.md.
Estado del repo: origin/main @ 1b3d714.
Versión del sistema: v9.21.49.
"""

PLAN = {
    "version": "2026-09-28",
    "repo_state": "origin/main @ 1b3d714",
    "system_version": "v9.21.49",
    "bug_tracker_query": "Archivar=false → 44 tickets abiertos",
    "notas_contexto": (
        "Kernel/Manual/SP/Census locales desactualizados vs v9.21.31–v9.21.49. "
        "Hay 18 entradas de Changelog sin propagar vversions --sync. "
        "Esto no es bug del sistema, pero es el contexto de cualquier lectura de código."
    ),
    fases: [
        {
            "nombre": "Fase 1 — Limpieza y alineación documental",
            "duración": "1-2 días",
            "sin_código_python": True,
            "bugs": [
                {
                    "id": "HO-000021",
                    "titulo": "Devin self-report sigue Abierto — no revisado por límite de sesión",
                    "prioridad": "2 MEDIO",
                    "componente": "Python",
                    "acciones": [
                        "Leer handoff HO-000021 y verificar el reporte contra repo.",
                        "Si es false positive / ya resuelto: marcar Resuelto con nota de evidencia.",
                        "Si es válido: clasificar en la fase correcta.",
                    ],
                    "dependencia": "Ninguna.",
                },
                {
                    "id": "HO-000011",
                    "titulo": "Drift v10.2.0 vs v10.0.0 — sin confirmación en esta sesión",
                    "prioridad": "2 MEDIO",
                    "componente": "Notion",
                    "acciones": [
                        "Leer HO-000011 y confirmar que la evidencia de v9.21.47 basta para cerrar.",
                        "Si hay duda: correr verify_versions.py --skills --drift contra v10.2.0.",
                        "Marcar Resuelto con nota o dejar abierto con evidencia nueva.",
                    ],
                    "dependencia": "Versión vigente del skill (SP:SKILL-VERSION-PIN: vantage-cv-b v10.2.0).",
                },
                {
                    "id": "HO-000022",
                    "titulo": "Layer3 heartbeat sin correr — 74h (umbral 48h)",
                    "prioridad": "2 MEDIO",
                    "componente": "Layer 3",
                    "acciones": [
                        "Verificar crontab + último heartbeat en ~/.vantage/l3_heartbeat.json.",
                        "Si está corriendo: marcar Resuelto (cron job activo desde v9.21.40).",
                        "Si no está corriendo: mover a Fase 2 como bug de infra.",
                    ],
                    "dependencia": "Acceso a crontab + verificación de heartbeat.",
                },
                {
                    "id": "3e1938be",
                    "titulo": "Skill vantage-cv-b contradice CANON:OUTPUT-CONTRACT-004",
                    "prioridad": "3 ALTO",
                    "componente": "Notion",
                    "acciones": [
                        "Decidir SSOT: CANON:OUTPUT-CONTRACT-004 v1.1.0 (prohíbe footer) vs skill v10.2.0 (exige footer).",
                        "Si CANON es SSOT: actualizar skill para quitar footer del .md.",
                        "Si skill es SSOT: actualizar CANON para permitir footer.",
                        "Escribir Changelog con la decisión.",
                    ],
                    "dependencia": "Ninguna (decisión autónoma).",
                },
                {
                    "id": "3b4938be",
                    "titulo": "Discrepancia doc transversal vs MANUAL:PATCH-QUA",
                    "prioridad": "3 ALTO",
                    "componente": "Notion",
                    "acciones": [
                        "Leer MANUAL §08.2 y el skill de documentación transversal.",
                        "Identificar filtros discrepantes.",
                        "Alinear Manual ↔ skill y escribir Changelog.",
                    ],
                    "dependencia": "Ninguna.",
                },
            ],
        },
        {
            "nombre": "Fase 2 — Cierre de bugs de código con fix directo",
            "duración": "3-5 días",
            "python": True,
            "bugs": [
                {
                    "id": "3b0938be",
                    "titulo": "backfill_class_a.py con bugs (3 defects)",
                    "prioridad": "3 ALTO",
                    "componente": "Python",
                    "acciones": [
                        "Leer Layer_1/scripts/backfill_class_a.py completo.",
                        "Corregir bug 1: priority_default = '4' → calcular Urgencia×Importancia.",
                        "Corregir bug 2: .get('number') sin fallback → agregar valor por defecto.",
                        "Corregir bug 3: posted_date inexistente → usar campo correcto del schema.",
                        "py_compile + dry-run + Changelog.",
                    ],
                    "dependencia": "Ninguna (script autónomo de VL1).",
                },
                {
                    "id": "3b8938be",
                    "titulo": "Dedup no cubre archivados",
                    "prioridad": "3 ALTO",
                    "componente": "Python",
                    "acciones": [
                        "Verificar si NOTION_ARCHIVE_DATA_SOURCE_ID ya está usada en dedup_opportunities.py.",
                        "Si no: agregar consulta al ARCHIVO TRACKER en el flujo de dedup.",
                        "Extender ANTI_FALSE_POSITIVE_RULES si es necesario.",
                        "Dry-run con --dry-run --window-days 60 contra ambos data sources.",
                        "Changelog.",
                    ],
                    "dependencia": "No bloquea 3b2938be, pero es conveniente paralelizar.",
                },
                {
                    "id": "3b2938be",
                    "titulo": "Dedup falla en variantes de título",
                    "prioridad": "3 ALTO",
                    "componente": "Python",
                    "acciones": [
                        "Leer feed_processor.py y dedup_cross_layer() para confirmar comparación exacta.",
                        "Agregar fuzzy matching con difflib.SequenceMatcher (ratio > 0.85).",
                        "Agregar reglas de variantes (coordinator/coordinador, asistente/assistant, acronyms).",
                        "Dry-run + Changelog.",
                    ],
                    "dependencia": "Puede paralelizarse con 3b8938be.",
                },
                {
                    "id": "3cd938be",
                    "titulo": "Drift GLOBAL_VANTAGE_COUNTER (27 vs 28)",
                    "prioridad": "1 CRÍTICO",
                    "componente": "Python",
                    "acciones": [
                        "Leer state/vantage_handoff_counter.sqlite3 y verificar valor actual.",
                        "Si DB está en 27: investigar por qué v9.21.40 no lo actualizó.",
                        "Si DB está en 28: el bug reporta 27 por lectura incorrecta — corregir la lectura.",
                        "Verificar con ho_counter --verify que el serial HO-###### generado coincida.",
                        "Changelog.",
                    ],
                    "dependencia": "Ninguna. ALTO-CRÍTICO: afecta trazabilidad de handoffs.",
                },
                {
                    "id": "3af938be",
                    "titulo": "Skill tidy no cruza exhaustivo Changelog",
                    "prioridad": "3 ALTO",
                    "componente": "Notion",
                    "acciones": [
                        "Leer vantage-tidy-bug-task-tracker/SKILL.md completo.",
                        "Verificar si el Escenario 2 realmente no cruza tickets individuales vs Changelog.",
                        "Si es válido: extender el skill para cruce exhaustivo ticket-by-ticket.",
                        "Si no es válido: cerrar como falso positive con evidencia.",
                        "Changelog.",
                    ],
                    "dependencia": "Ninguna.",
                },
            ],
        },
        {
            "nombre": "Fase 3 — Mitigación de comportamiento del agente y alineación normativa",
            "duración": "2-3 días",
            "sin_código_nuevo": True,
            "bugs": [
                {
                    "id": "3e5938be",
                    "titulo": "Devin narra pushes/commits que no ocurren",
                    "prioridad": "1 CRÍTICO",
                    "componente": "Notion",
                    "acciones": [
                        "Documentar explícitamente en handoff: afirmaciones de Devin sobre GitHub deben verificarse contra repo real.",
                        "Agregar línea de verificación al protocolo de handoff.",
                        "Si hay patrón recurrente: considerar aclaración en SP:BOOTLOADER-002.",
                    ],
                    "dependencia": "Ninguna.",
                },
                {
                    "id": "392938be",
                    "titulo": "System Prompt inferencias espontáneas",
                    "prioridad": "3 ALTO",
                    "componente": "Notion",
                    "acciones": [
                        "Releer SP:BOOTLOADER-001 y verificar que las restricciones de inferencia están claras.",
                        "Documentar patrón específico de inferencias recurrentes en handoff.",
                        "Considerar si KERNEL:CONTEXT-INFRASTRUCTURE-001 necesita aclaración.",
                    ],
                    "dependencia": "Puede ir en paralelo con 3e5938be (mismo tipo).",
                },
                {
                    "id": "3e1938be (ejecución)",
                    "titulo": "Ejecutar decisión documental tomada en Fase 1",
                    "prioridad": "3 ALTO",
                    "componente": "Notion",
                    "acciones": [
                        "Si CANON es SSOT: actualizar skill vantage-cv-b v10.2.0, quitar footer del .md.",
                        "Si skill es SSOT: actualizar CANON:OUTPUT-CONTRACT-004 v1.1.0, permitir footer.",
                        "Changelog.",
                    ],
                    "dependencia": "Fase 1, sección 1.2 (decisión primero).",
                },
                {
                    "id": "3b4938be (alineación)",
                    "titulo": "Ejecutar alineación doc transversal vs MANUAL:PATCH-QUA",
                    "prioridad": "3 ALTO",
                    "componente": "Notion",
                    "acciones": [
                        "Alinear Manual ↔ skill según decisión tomada en Fase 1.",
                        "Changelog.",
                    ],
                    "dependencia": "Fase 1.",
                },
            ],
        },
    ],
    "bugs_baja_prioridad_restantes": [
        "vload alias — Documentar (Kernel §04 ya documenta lazy_loader.py, no vload)",
        "Match faltante en CV-B — Monitorear (no es bug de sistema, es campo no poblado)",
        "vsum notions params — Documentar (código existente, no es bug)",
        "Source_Type space key — Documentar (no afecta funcionalidad)",
        "Skills desactualizados en Registry — Documentar (SP:SYNC-RULE, proyecto futuro)",
        "Guard descarta MCP a CV-A/B/PDF/Figma — Documentar (no es bug del sistema)",
        "¶¶ corruption en Manual.md — Corregir manualmente (encoding de 'á')",
        "verify_versions.py comentario — Documentar (confusión de lectura, no bug)",
        "health_check.py docstring — Documentar (minor docstring inconsistency)",
        "vsync_doc.py banner v9.13.0 — Documentar (residual nomenclatura, no bug)",
    ],
    "notas_finales": (
        "El plan asume que los 10 bugs de baja prioridad del inicio del query "
        "son 'documentar/monitorear' y no requieren fix de código. "
        "Los 3 bugs de sesión pendientes (HO-000021/11/22) son el cuello de botella "
        "de la Fase 1 porque sin cerrarlos, no sabes si los demás bugs son reales o ya resueltos. "
        "El bug 3cd938be (GLOBAL_VANTAGE_COUNTER) es el único CRÍTICO restante y debe "
        "descifrase antes de generar cualquier handoff nuevo."
    ),
}

if __name__ == "__main__":
    import json
    print(json.dumps(PLAN, indent=2, ensure_ascii=False))
