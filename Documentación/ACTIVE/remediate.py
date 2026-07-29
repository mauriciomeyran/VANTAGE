import re
from pathlib import Path

base_dir = Path(".")

# 1. ALIASES.md
aliases_path = base_dir / "ALIASES.md"
if aliases_path.exists():
    content = aliases_path.read_text(encoding="utf-8")
    content = content.replace("§9.2", "09.2").replace("§8.3", "08.3").replace("§", "")
    aliases_path.write_text(content, encoding="utf-8")

# 2. BRIEF.md
brief_path = base_dir / "BRIEF.md"
if brief_path.exists():
    content = brief_path.read_text(encoding="utf-8")
    content = content.replace("## TABLE OF CONTENTS", "**Table of Contents**")
    content = content.replace("## 01 BRIEF:SCOPE", "## 01 BRIEF:PURPOSE-SCOPE")
    content = content.replace("### Propósito", "### 01.1 BRIEF:PURPOSE-SCOPE-001\n### Propósito")
    content = content.replace("### Alcance", "### 01.2 BRIEF:PURPOSE-SCOPE-002\n### Alcance")
    content = content.replace("### Fuera de Alcance", "### 01.3 BRIEF:PURPOSE-SCOPE-003\n### Fuera de Alcance")
    content = content.replace("### Consulta Arquitectónica", "### 04.1 BRIEF:CONSULTATION-001\n### Consulta Arquitectónica")
    content = content.replace("### Housekeeping", "### 05.1 BRIEF:HOUSEKEEPING-001\n### Housekeeping")
    content = content.replace("### 7.1 Impact Assessment Contract", "### 07.1 BRIEF:CROSS-DEPENDENCIES-001\n### Impact Assessment Contract")
    content = content.replace("### 7.2 Mandatory Change Reporting", "### 07.2 BRIEF:CROSS-DEPENDENCIES-002\n### Mandatory Change Reporting")
    content = content.replace("### 7.3 Closure Gate", "### 07.3 BRIEF:CROSS-DEPENDENCIES-003\n### Closure Gate")
    content = content.replace("### Autoridad", "### 08.1 BRIEF:AUTHORITY-001\n### Autoridad")
    brief_path.write_text(content, encoding="utf-8")

# 3. SYSTEM_PROMPT.md
sp_path = base_dir / "SYSTEM_PROMPT.md"
if sp_path.exists():
    content = sp_path.read_text(encoding="utf-8")
    content = content.replace("| 01 | SP:BOOTSTRAP |", "| 01 | SP:BOOTSTRAP-001 |")
    content = content.replace("| 03 | SP:DIGITAL-ID-CARD |", "| 03 | SP:DIGITAL-ID-CARD-001 |")
    content = content.replace("## DECLARACIÓN DE AUDIENCIA Y ALCANCE", "## 00 SP:AUDIENCE-SCOPE\n## Declaración de Audiencia y Alcance")
    content = content.replace("### Conector único autorizado", "### 01.1 SP:BOOTSTRAP-002\n### Conector único autorizado")
    content = content.replace("### Verificación de Versión", "### 02.1 SP:VERSION-VERIFICATION-002\n### Verificación de Versión")
    content = content.replace("### Regla de versionado", "### 03.1 SP:DIGITAL-ID-CARD-002\n### Regla de versionado")
    content = content.replace("### Class A/B", "### 08.1 SP:CLASS-AB-002\n### Class A/B")
    content = content.replace("### Herramienta de verificación", "### 12.1 SP:VERIFICATION-TOOL-002\n### Herramienta de verificación")
    sp_path.write_text(content, encoding="utf-8")

# 4. CHANGELOG.md
changelog_path = base_dir / "CHANGELOG.md"
if changelog_path.exists():
    content = changelog_path.read_text(encoding="utf-8")
    content = re.sub(r'(\n---\n)# V \| CHANGELOG\n', r'\1', content)
    content = content.replace("§09.11", "09.11").replace("§08.6", "08.6").replace("§4.4", "04.4").replace("§", "")
    
    replacements = [
        ("### v9.9.9", "## 01 CHANGELOG:V9-9-9\n## v9.9.9"),
        ("### v9.9.8", "## 02 CHANGELOG:V9-9-8\n## v9.9.8"),
        ("### v9.9.7", "## 03 CHANGELOG:V9-9-7\n## v9.9.7"),
        ("### v9.9.6", "## 04 CHANGELOG:V9-9-6\n## v9.9.6"),
        ("### v9.9.5", "## 05 CHANGELOG:V9-9-5\n## v9.9.5"),
        ("### v9.9.4", "## 06 CHANGELOG:V9-9-4\n## v9.9.4"),
        ("### v9.9.3", "## 07 CHANGELOG:V9-9-3\n## v9.9.3"),
        ("### v9.9.0", "## 08 CHANGELOG:V9-9-0\n## v9.9.0"),
        ("### v9.8.0", "## 09 CHANGELOG:V9-8-0\n## v9.8.0"),
        ("### v9.7.9", "## 10 CHANGELOG:V9-7-9\n## v9.7.9"),
        ("### v9.7.8", "## 11 CHANGELOG:V9-7-8\n## v9.7.8"),
        ("### v9.7.7", "## 12 CHANGELOG:V9-7-7\n## v9.7.7"),
    ]
    for old, new in replacements:
        content = content.replace(old, new)
    changelog_path.write_text(content, encoding="utf-8")

print("Remediación completada correctamente.")
