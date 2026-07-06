# Assessment: Cambio de Nombre de Carpeta "- Documentación" → "Documentación"

**Fecha:** 2026-07-05  
**Objetivo:** Evaluar implicaciones de renombrar carpeta "- Documentación" a "Documentación" (eliminar guión y espacio)  
**Alcance:** Scripts Python, configuración, documentación, y referencias en Notion

---

## 1. Referencias Directas en Código Python

### Scripts que HARDCODEAN el path absoluto

#### health_check.py
**Ubicación:** `Layer_1/scripts/health_check.py:36`
```python
ACTIVE_DIR = Path("/Users/mauriciomeyran/Documents/04-Vantage_CV/- Documentación/ACTIVE")
```
**Impacto:** CRÍTICO — Si se renombra la carpeta, este script fallará
**Fix requerido:** Cambiar a path relativo o variable de entorno

#### vsync_doc.py
**Ubicación:** `Layer_4/scripts/vsync_doc.py:44`
```python
BASE_DIR = _PROJECT / "- Documentación" / "ACTIVE"
```
**Impacto:** CRÍTICO — Si se renombra la carpeta, este script fallará
**Fix requerido:** Cambiar a path relativo

#### vsync_doc.py.bak-20260703-054923
**Ubicación:** `Layer_4/scripts/vsync_doc.py.bak-20260703-054923:44`
```python
BASE_DIR = _PROJECT / "- Documentación" / "ACTIVE"
```
**Impacto:** BAJO — Es backup, puede eliminarse o ignorarse
**Fix requerido:** Eliminar backup o actualizar si se mantiene

---

## 2. Referencias en Documentación

### Change Log.md
**Ubicación:** `- Documentación/ACTIVE/Change Log.md:188`
```markdown
- [NEW] vsync_doc.py — ... contra sus .md locales en - Documentación/v8.5/.
```
**Impacto:** BAJO — Es referencia histórica, no afecta operación
**Fix requerido:** Actualizar referencia en siguiente versión de changelog

### Validation-Report-Runtime-Graph-Builder.md
**Ubicación:** `- Documentación/ACTIVE/Validation-Report-Runtime-Graph-Builder.md:275, 285`
```markdown
**File:** `/Users/mauriciomeyran/Documents/04-Vantage_CV/- Documentación/ACTIVE/ADR-001-Runtime-Graph-Builder.md`
**File:** `/Users/mauriciomeyran/Documents/04-Vantage_CV/- Documentación/v8.4/Others/04. Runtime Documentation.md`
```
**Impacto:** BAJO — Son referencias históricas en reportes de validación
**Fix requerido:** No necesario (son reportes históricos)

### SETUP.md
**Ubicación:** `SETUP.md:39`
```markdown
└── - Documentación/           # Documentation folders
```
**Impacto:** BAJO — Es documentación de estructura
**Fix requerido:** Actualizar diagrama en SETUP.md

### PROJECT_CLOSURE_20260705.md
**Ubicación:** `docs/reports/PROJECT_CLOSURE_20260705.md:574`
```markdown
Existing documentation spread across multiple locations (- Documentación/, Layer_1/, repository root).
```
**Impacto:** BAJO — Es reporte histórico
**Fix requerido:** No necesario (es reporte histórico)

---

## 3. Referencias en Notion (NO VERIFICABLES)

### Posibles referencias en:
- Kernel.md (puede tener paths a documentación local)
- Manual.md (puede tener paths a documentación local)
- System Prompt.md (puede tener paths a documentación local)
- Change Log en Notion (puede tener paths a documentación local)

**Impacto:** BAJO — Son referencias en Notion, no afectan código
**Fix requerido:** Manual — revisar y actualizar si existen

---

## 4. Impacto de Renombrar Carpeta

### CRÍTICO (Rompe scripts si no se fixea)
1. **health_check.py** — Path absoluto hardcodeado
2. **vsync_doc.py** — Path relativo pero con nombre antiguo

### MEDIO (Actualización recomendada pero no crítico)
3. **Change Log.md** — Referencia histórica
4. **SETUP.md** — Documentación de estructura

### BAJO (No requiere acción inmediata)
5. **Validation-Report-* .md** — Reportes históricos
6. **PROJECT_CLOSURE_*.md** — Reportes históricos
7. **vsync_doc.py.bak*** — Backup que puede eliminarse
8. **Referencias en Notion** — Manuales, no críticas

---

## 5. Plan de Cambio Propuesto

### FASE 1: Renombrar carpeta (1 minuto)
```bash
cd /Users/mauriciomeyran/Documents/04-Vantage_CV
mv "- Documentación" "Documentación"
```

### FASE 2: Fix scripts críticos (10 minutos)
**health_check.py:**
```python
# ANTES
ACTIVE_DIR = Path("/Users/mauriciomeyran/Documents/04-Vantage_CV/- Documentación/ACTIVE")

# DESPUÉS
ACTIVE_DIR = Path(__file__).resolve().parent.parent / "Documentación" / "ACTIVE"
# O usar variable de entorno
```

**vsync_doc.py:**
```python
# ANTES
BASE_DIR = _PROJECT / "- Documentación" / "ACTIVE"

# DESPUÉS
BASE_DIR = _PROJECT / "Documentación" / "ACTIVE"
```

### FASE 3: Actualizar documentación (15 minutos)
- **SETUP.md:** Actualizar diagrama de estructura
- **Change Log.md:** Actualizar referencia en próxima versión
- **Notion:** Revisar Kernel, Manual, System Prompt, Change Log por referencias

### FASE 4: Limpieza (5 minutos)
- Eliminar vsync_doc.py.bak-20260703-054923
- Actualizar .gitignore si no está ignorando backups

---

## 6. Alternativa: Usar Variable de Entorno

### Pros
- No requiere cambios en código
- Fácil de configurar para diferentes entornos
- Más flexible para desarrollo vs producción

### Cons
- Requiere configuración adicional
- Puede olvidarse configurar en nuevos entornos
- Agrega complejidad

### Implementación
```python
# health_check.py
import os
ACTIVE_DIR = Path(os.environ.get("VANTAGE_DOCS_DIR", 
    "/Users/mauriciomeyran/Documents/04-Vantage_CV/Documentación/ACTIVE"))

# vsync_doc.py
BASE_DIR = _PROJECT / os.environ.get("VANTAGE_DOCS_DIR", "Documentación") / "ACTIVE"
```

**Recomendación:** NO usar variable de entorno — el path es predecible y consistente en este proyecto.

---

## 7. Riesgos y Mitigaciones

### Riesgo #1: health_check.py falla después de renombrar
**Probabilidad:** ALTA (100% si no se fixea)
**Impacto:** CRÍTICO — Health check no funcionará
**Mitigación:** Fixear ANTES de renombrar carpeta

### Riesgo #2: vsync_doc.py falla después de renombrar
**Probabilidad:** ALTA (100% si no se fixea)
**Impacto:** CRÍTICO — Sync de documentación no funcionará
**Mitigación:** Fixear ANTES de renombrar carpeta

### Riesgo #3: Referencias en Notion quedan obsoletas
**Probabilidad:** MEDIA (depende de si existen)
**Impacto:** BAJO — Documentación desactualizada
**Mitigación:** Revisar manualmente después del cambio

### Riesgo #4: Git history muestra paths antiguos
**Probabilidad:** ALTA (siempre pasa)
**Impacto:** BAJO — No afecta operación, solo contexto histórico
**Mitigación:** No es problema, git history debe mantenerse intacto

---

## 8. Recomendación Final

### Opción A: Renombrar y fixear (RECOMENDADO)
**Ventajas:**
- Nombres más limpios y estándar
- Mejor experiencia de desarrollo
- Paths predecibles y consistentes

**Costo:** 30 minutos de trabajo
**Riesgo:** Bajo (si se sigue el plan propuesto)

### Opción B: No renombrar
**Ventajas:**
- Cero riesgo de romper algo
- No requiere cambios

**Costo:** 0 minutos
**Riesgo:** Nulo

**Conclusión:** Renombrar es un cambio cosmético de bajo riesgo, pero el beneficio es marginal. Si te molesta el guión y espacio, hazlo. Si no, no vale la pena.

---

## 9. Orden de Ejecución (si decides hacerlo)

1. **Fixear scripts PRIMERO** (health_check.py, vsync_doc.py)
2. **Renombrar carpeta** (mv "- Documentación" "Documentación")
3. **Actualizar documentación** (SETUP.md, Change Log.md)
4. **Revisar Notion** (opcional, baja prioridad)
5. **Limpiar backups** (vsync_doc.py.bak*)

---

## 10. Definición de Terminado

- [x] health_check.py actualizado
- [x] vsync_doc.py actualizado
- [x] Carpeta renombrada
- [x] SETUP.md actualizado
- [x] Change Log.md actualizado (en próxima versión)
- [x] Referencias en Notion revisadas ✅ NO HAY REFERENCIAS OPERATIVAS
- [ ] Backups eliminados (opcional)
- [x] health_check.py probado exitosamente
- [x] vsync_doc.py probado exitosamente

## Resultado de Revisión en Notion (Mistral)

**Páginas revisadas:** 6 (System Prompt, Manual, Kernel, Career Canon, Change Log, Aliases)
**Referencias encontradas:** 1 (Change Log v8.9.8 - referencia histórica)
**Referencias operativas:** 0
**Acción requerida:** NINGUNA ✅

**Conclusión:** No hay referencias operativas al nombre antiguo en Notion. Solo el Change Log contiene una referencia histórica que no debe modificarse.

---

**FIN DEL ASSESSMENT**
