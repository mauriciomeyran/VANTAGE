#!/usr/bin/env zsh

cd "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts"

python3 << 'PYEOF'
from pathlib import Path
import re

script_path = Path("generate_census.py")
content = script_path.read_text(encoding="utf-8")

# Lista de tuplas actualizadas (id, old_seccion, new_seccion)
fixes = [
    ("MANUAL:SCRIPT-GLOSSARY-CV-PREP", "22.2", "22.2"),      # Confirmar estado
    ("SP:BOOTLOADER-001", "01.1", "01.1"),                   # Confirmar estado
    ("KERNEL:DASHBOARD-CHECKLIST-ARCH", "04.5", "06"),
    ("KERNEL:PURPOSE", "06", "01"),
    ("KERNEL:PURPOSE-001", "06.1", "01.1"),
    ("KERNEL:FAIL-PHILOSOPHY", "09", "02"),
    ("KERNEL:FAIL-PHILOSOPHY-001", "09.1", "02.1"),
    ("KERNEL:FAIL-PHILOSOPHY-002", "09.2", "02.2"),
    ("KERNEL:GATE-DECISION", "10", "09"),
    ("KERNEL:GATE-DECISION-001", "10.1", "09.1"),
    ("KERNEL:GATE-DECISION-002", "10.2", "09.2"),
    ("KERNEL:GATE-DECISION-003", "10.3", "09.3"),
    ("KERNEL:GATE-DECISION-004", "10.4", "09.4"),
    ("KERNEL:GATE-DECISION-005", "10.5", "09.5"),
    ("KERNEL:GATE-DECISION-006", "10.6", "09.6"),
    ("KERNEL:GATE-DECISION-007", "10.7", "09.7"),
    ("KERNEL:GATE-DECISION-008", "10.8", "09.8"),
    ("KERNEL:GATE-DECISION-009", "10.9", "09.9"),
    ("KERNEL:GATE-DECISION-010", "10.10", "09.10"),
    ("KERNEL:GATE-DECISION-011", "10.11", "09.11"),
    ("KERNEL:CV-GOLDEN-RULES", "11", "10"),
    ("KERNEL:CV-GOLDEN-RULES-001", "11", "10.1"),
    ("KERNEL:CV-GOLDEN-RULES-002", "11", "10.2"),
    ("KERNEL:CV-GOLDEN-RULES-003", "11", "10.3"),
    ("KERNEL:CV-GOLDEN-RULES-004", "11", "10.4"),
    ("KERNEL:CV-GOLDEN-RULES-005", "11", "10.5"),
    ("KERNEL:CV-GOLDEN-RULES-006", "11.6", "10.6"),
    ("KERNEL:TRIGGERS", "12", "11"),
    ("KERNEL:TRIGGER-001", "12.1", "11.1"),
    ("KERNEL:TRIGGER-002", "12.2", "11.2"),
    ("KERNEL:TRIGGER-003", "12.3", "11.3"),
    ("KERNEL:TRIGGER-004", "12.4", "11.4"),
    ("KERNEL:TRIGGER-005", "12.5", "11.5"),
    ("KERNEL:TRIGGER-006", "12.6", "11.6"),
    ("KERNEL:TRIGGER-007", "12.7", "11.7"),
    ("KERNEL:TRIGGER-008", "12.8", "11.8"),
    ("KERNEL:TRIGGER-009", "12.9", "11.9"),
    ("KERNEL:CV-PIPELINE", "13", "12"),
    ("KERNEL:CV-PIPELINE-001", "13.1", "12.1"),
    ("KERNEL:CV-PIPELINE-002", "13.2", "12.2"),
    ("KERNEL:CANON-UPDATE", "14", "13"),
    ("KERNEL:NAMING-CONVENTION", "15", "14"),
    ("KERNEL:CONTEXT-INFRASTRUCTURE", "16", "15"),
    ("KERNEL:CONTEXT-INFRASTRUCTURE-001", "16.1", "15.1"),
    ("KERNEL:CONTEXT-INFRASTRUCTURE-002", "16.2", "15.2"),
    ("KERNEL:DATA-FLOW", "17", "16"),
    ("KERNEL:EVOLUTION", "18", "17"),
    ("MANUAL:WEEKLY-FLOW-001", "08.1", "8.1"),
    ("MANUAL:WEEKLY-FLOW-002", "08.2", "8.2"),
    ("MANUAL:WEEKLY-FLOW-003", "08.3", "8.3"),
    ("MANUAL:RUNTIME-001", "09.1", "9.1"),
    ("MANUAL:RUNTIME-002", "09.2", "9.2"),
    ("MANUAL:RUNTIME-003", "09.3", "9.3"),
    ("MANUAL:RUNTIME-004", "09.4", "9.4"),
    ("MANUAL:RUNTIME-005", "09.5", "9.5"),
    ("MANUAL:SCRIPT-GLOSSARY-DASHBOARD", "22.1", "22.4"),
    ("MANUAL:SCRIPT-GLOSSARY-DASHBOARD-MODULES", "22.2", "22.4a"),
    ("MANUAL:SCRIPT-GLOSSARY-L1", "22.1", "22.1"),           # Confirmar estado
    ("MANUAL:SCRIPT-GLOSSARY-L1-MODULES", "22.1a", "22.1a"), # Confirmar estado
    ("MANUAL:SCRIPT-GLOSSARY-L1-TOOLS", "22.1b", "22.1b"),   # Confirmar estado
    ("MANUAL:SCRIPT-GLOSSARY-L4", "22.6", "22.3"),
    ("MANUAL:SCRIPT-GLOSSARY-RAYCAST", "22.7", "22.5"),
    ("MANUAL:SCRIPT-GLOSSARY-XREF", "22.8", "22.6"),
    ("SP:CONSISTENCY", "11", "10"),
    ("SP:VERSION-CHECK-TOOL", "12", "11"),
]

applied = 0
missing = []
for id_, old_sec, new_sec in fixes:
    # Corrección de SyntaxWarning usand raw string estricto r'...' sin escapar en exceso
    pattern = re.compile(r'(\{"id":\s*"' + re.escape(id_) + r'",\s*"seccion":\s*")' + re.escape(old_sec) + r'(")')
    new_content, n = pattern.subn(lambda m: m.group(1) + new_sec + m.group(2), content, count=1)
    if n == 1:
        content = new_content
        applied += 1
    else:
        missing.append(id_)

script_path.write_text(content, encoding="utf-8")
print(f"Aplicados: {applied}/{len(fixes)}")
if missing:
    print("NO encontrados (revisar manualmente):")
    for m in missing:
        print(f"  - {m}")
PYEOF

python3 -c "import ast; ast.parse(open('generate_census.py').read())" && echo "✓ Sintaxis válida"
