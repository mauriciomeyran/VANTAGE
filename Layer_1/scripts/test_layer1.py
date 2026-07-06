#!/usr/bin/env python3
"""
Tarea #16 + #17: Tests de regresión — scoring v6.4 y gate logic
VANTAGE v8.0
"""

import sys
import os

# Patch imports que necesitan env/archivos externos
sys.modules['profile_fit'] = type(sys)('profile_fit')
sys.modules['profile_fit'].has_vm_title_signal = lambda rol: True
sys.modules['profile_fit'].is_role_excluded = lambda rol: False
sys.modules['profile_fit'].resolve_alias_flags = lambda marca: (False, None)
sys.modules['profile_fit'].profile_misfit_reasons = lambda **kw: []
sys.modules['profile_fit'].should_auto_cleanup = lambda s, r: False

os.environ.setdefault('NOTION_TOKEN', 'test-token')

from layer_1_run import calculate_score_v6, gate, get_vm_scope, get_role_class, evaluate_application_status, get_application_next_action

# ─── Helpers ────────────────────────────────────────────────────────────────

passed = 0
failed = 0

def check(label, actual, expected):
    global passed, failed
    if actual == expected:
        print(f"  ✅ {label}")
        passed += 1
    else:
        print(f"  ❌ {label}")
        print(f"     esperado: {expected!r}")
        print(f"     obtenido: {actual!r}")
        failed += 1

# ─── #16: Scoring v6.4 ──────────────────────────────────────────────────────

print("\n=== #16: calculate_score_v6 ===")

# Base score: entrada vacía → 40 (solo base)
check("entrada vacía → 40",
    calculate_score_v6({"title": "", "company": "", "jd": "", "contact": ""}), 40)

# Visual signal: +20
check("JD con 'visual' → 60",
    calculate_score_v6({"title": "", "company": "", "jd": "visual merchandising excellence", "contact": ""}), 60)

# High impact company: +15
check("Nike sin JD visual → 55",
    calculate_score_v6({"title": "", "company": "nike", "jd": "", "contact": ""}), 55)

# Luxury heritage: +5 + visual +20 + high_impact +15 + base +40 = 80
check("Dior + JD visual → 80 (high_impact + luxury_pure)",
    calculate_score_v6({"title": "", "company": "dior", "jd": "visual brand standards", "contact": ""}), 80)

# Role quality: +10
check("manager title → 50",
    calculate_score_v6({"title": "store manager", "company": "", "jd": "", "contact": ""}), 50)

# Max cap = 100
check("todo al máximo no supera 100",
    calculate_score_v6({
        "title": "visual merchandising manager",
        "company": "lvmh dior louis vuitton",
        "jd": "visual brand experience retail store design shopper",
        "contact": "recruiter present"
    }), 100)

# Ready-to-apply threshold
score_rta = calculate_score_v6({"title": "visual coordinator", "company": "adidas", "jd": "visual guidelines", "contact": ""})
check("ready-to-apply (>=60) con adidas+visual+coord",
    score_rta >= 60, True)

# Pivot bonus
check("trade marketing title → pivot bonus (+5) → 45",
    calculate_score_v6({"title": "trade marketing", "company": "", "jd": "", "contact": ""}), 45)

# ─── #16: get_vm_scope / get_role_class ─────────────────────────────────────

print("\n=== #16: get_vm_scope ===")
check("'Visual Merchandising Manager' → Alto", get_vm_scope("Visual Merchandising Manager"), "Alto")
check("'Sales Associate' → Bajo", get_vm_scope("Sales Associate"), "Bajo")
check("vacío → Bajo", get_vm_scope(""), "Bajo")
check("'VM Coordinator' → Alto", get_vm_scope("VM Coordinator"), "Alto")

print("\n=== #16: get_role_class ===")
check("'Visual Merchandising' → VM", get_role_class("Visual Merchandising"), "VM")
check("'Retail Design Lead' → Pivote", get_role_class("Retail Design Lead"), "Pivote")
check("'Sales Manager' → Otro", get_role_class("Sales Manager"), "Otro")
check("'Trade Marketing' → Pivote", get_role_class("Trade Marketing Specialist"), "Pivote")
check("vacío → Otro", get_role_class(""), "Otro")

# ─── #17: gate() ────────────────────────────────────────────────────────────

print("\n=== #17: gate() ===")

# VM vacante accesible → CREATE
check("Vacante Accesible VM_Scope=Alto → CREATE",
    gate("Accesible", "Alto", "VM", "Vacante"), "CREATE")

# Vacante bloqueada → BLOCKED
check("Vacante Bloqueado → BLOCKED",
    gate("Bloqueado", "Alto", "VM", "Vacante"), "BLOCKED")

# Pivote con señal VM → CREATE
check("Vacante Accesible Pivote con señal → CREATE",
    gate("Accesible", "Bajo", "Pivote", "Vacante", rol="retail design lead"), "CREATE")

# Inbound siempre CREATE
check("Inbound → CREATE (sin importar fetch)",
    gate("Bloqueado", "Bajo", "Otro", "Inbound"), "CREATE")

# Networking → CREATE
check("Networking → CREATE",
    gate("", "Bajo", "Otro", "Networking"), "CREATE")

# Referencia → CREATE
check("Referencia → CREATE",
    gate("", "Bajo", "Otro", "Referencia"), "CREATE")

# Vacante scope bajo, no pivote → BLOCKED
check("Vacante Accesible VM_Scope=Bajo, Otro → BLOCKED",
    gate("Accesible", "Bajo", "Otro", "Vacante"), "BLOCKED")

# Parcial con VM → CREATE
check("Vacante Parcial VM_Scope=Alto → CREATE",
    gate("Parcial", "Alto", "VM", "Vacante"), "CREATE")

# ─── #17: application status & next action ──────────────────────────────────

print("\n=== #17: evaluate_application_status / get_application_next_action ===")

check("Postulado → True", evaluate_application_status("Postulado"), True)
check("En proceso → True", evaluate_application_status("En proceso"), True)
check("Expirada → False", evaluate_application_status("Expirada"), False)
check("Rechazado → False", evaluate_application_status("Rechazado"), False)
check("'' → False", evaluate_application_status(""), False)

check("Postulado → Follow-up", get_application_next_action("Postulado"), "Follow-up")
check("En proceso → Interview prep", get_application_next_action("En proceso"), "Interview prep")
check("Negociando → Follow-up", get_application_next_action("Negociando"), "Follow-up")
check("Sin respuesta → Follow-up", get_application_next_action("Sin respuesta"), "Follow-up")

# ─── Tarea #19: referencias huérfanas ───────────────────────────────────────

print("\n=== #19: referencias huérfanas en layer_1_run.py ===")

with open("layer_1_run.py") as f:
    source = f.read()

orphans = {
    "Match (prop write)": '"Match"' in source and 'update_props["Match"]' in source,
    "Prioridad (prop write)": '"Prioridad"' in source and 'score_to_prioridad' in source,
    "Fuente (prop write)": 'determine_fuente' in source,
    "check_url (huérfana)": 'def check_url' in source,
    "check_if_expired (huérfana)": 'def check_if_expired' in source,
    "get_match_level_v6 (huérfana)": 'def get_match_level_v6' in source,
    "score_to_prioridad (huérfana)": 'def score_to_prioridad' in source,
    "PASO 2 loop": 'Paso 2: URL re-check' in source,
}

for label, found in orphans.items():
    if found:
        print(f"  ❌ ENCONTRADA referencia huérfana: {label}")
        failed += 1
    else:
        print(f"  ✅ Limpio: {label}")
        passed += 1

# ─── Resultado ──────────────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"RESULTADO: {passed} passed / {failed} failed / {passed+failed} total")
if failed == 0:
    print("✅ BLOQUE 5 OK — pipeline listo para staging")
else:
    print("❌ HAY FALLOS — revisar antes de deploy")
