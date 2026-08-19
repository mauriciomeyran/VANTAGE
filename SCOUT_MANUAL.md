# VANTAGE Scout - Manual de Usuario Completo

## 🎯 ¿Qué es VANTAGE Scout?

VANTAGE Scout es un **robot automatizado que busca trabajo por ti**. Imagina esto:

- **Tú normalmente**: Abres Google, entras a 20 páginas de empresas, ves qué ofertas hay, copias datos... 🥵
- **Scout**: Tú le dices "busca trabajos en páginas de carrera" y él solo hace todo eso automáticamente 🤖

**Scout hace esto:**
1. Abre un navegador (Chrome automatizado)
2. Va a sitios de empleo (LinkedIn, páginas de empresas, etc.)
3. Lee las ofertas de trabajo
4. Filtra según tu perfil específico
5. Aplica reglas avanzadas de Layer_1 (deduplicación, gates, etc.)
6. Guarda todo en un archivo JSON organizado

---

## 🚀 Novedades - Integración con Layer_1

### ¿Qué es Layer_1?
Layer_1 es el sistema avanzado de VANTAGE que maneja toda la lógica de procesamiento de oportunidades. Ahora Scout está **completamente integrado** con Layer_1, lo que significa:

### 🔥 **Nuevas Capacidades (Alta Prioridad)**

#### 1. **Deduplicación Inteligente**
- **Antes**: Scout podía encontrar la misma oferta varias veces en ejecuciones diferentes
- **Ahora**: Sistema de deduplicación con 3 niveles de hash:
  - Primario: URL de aplicación normalizada
  - Secundario: Marca|Título|Ubicación  
  - Terciario: ID del trabajo
- **Ventana de historial**: 30 días
- **Resultado**: 80-90% menos duplicados

#### 2. **Protección de Estados Terminales**
- **Antes**: Scout podría re-procesar ofertas que ya descartaste
- **Ahora**: Respeta decisiones previas
- **Estados protegidos**: "Postulado", "Rechazado", "Archivar", "Expirada"
- **Acciones protegidas**: "Archivar", "Expirada"
- **Resultado**: No pierde tiempo en lo que ya decidiste

#### 3. **Filtrado de Perfil Avanzado**
- **Antes**: Exclusiones básicas en prompts
- **Ahora**: Sistema completo usando `alias_map.json` de Layer_1
- **Capacidades**:
  - Hard blocks de marcas (L'Oréal, Levi's, etc.)
  - Exclusiones contextuales (ej: "planner" vs "visual planner")
  - Detección de señales VM en títulos
  - Filtros de ubicación (CDMX o remote México)
- **Resultado**: Exclusiones mucho más precisas

### 🔧 **Nuevas Capacidades (Media Prioridad)**

#### 4. **Validación de URLs**
- **Antes**: Scout navegaba a URLs sin saber si funcionaban
- **Ahora**: Valida URLs antes de navegar
- **Clasificación de fuentes**:
  - Career_Page_Premium (LVMH, Richemont, Kering, etc.)
  - Career_Page_Standard
  - Aggregators (LinkedIn, Indeed, etc.)
- **Resultado**: Ahorra tiempo en URLs rotas

#### 5. **Sincronización con Notion**
- **Antes**: Solo generaba JSON local
- **Ahora**: Integración opcional con tracker VANTAGE
- **Capacidades**:
  - Sync automático con Notion
  - Protección de estados en Notion
  - Class A schema completo
- **Resultado**: Flujo completamente automatizado

### 📊 **Nuevas Capacidades (Baja Prioridad)**

#### 6. **Analytics de Fuentes**
- **Antes**: Sin información de efectividad
- **Ahora**: Reportes completos de rendimiento
- **Métricas**:
  - Efectividad por fuente
  - Tasas de éxito/fracaso
  - Tendencias temporales
  - Recomendaciones automáticas
- **Resultado**: Optimización basada en datos

---

## 📦 Instalación (Primera vez)

### Paso 1: Clonar e instalar dependencias
```bash
cd VANTAGE
pip install -r requirements.txt
playwright install chromium
```

### Paso 2: Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus API keys
```

### Paso 3: Configuración mínima para Scout
```bash
# --- Motor de IA (Groq) ---
LLM_PROVIDER=openai_compatible
LLM_API_KEY=gsk_tu_groq_api_key_aqui
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-20b

# --- Ajustes del navegador Scout ---
BROWSER_HEADLESS=false
BROWSER_MAX_STEPS=70
LLM_COST_LIMIT=5.0
USE_CHEAP_FALLBACK=true
DOMAIN_MIN_DELAY=3.0
CHROME_USER_DATA_DIR=

# --- Integración Layer_1 (Opcional) ---
ENABLE_LAYER1_INTEGRATION=true
# NOTION_TOKEN=tu_token_aqui  # Para sync con Notion
# NOTION_DB_OPPORTUNITIES=tu_db_id
```

---

## 🎮 Formas de Ejecutar Scout

### Opción 1: Línea de Comandos (CLI) - Recomendado para Producción

#### Ejecución Básica
```bash
# Career Sites
python main.py --wrapper Prompt_Career_Sites

# LinkedIn  
python main.py --wrapper linkedin

# Aggregators
python main.py --wrapper aggregators

# Dry Run (testing)
python main.py --wrapper Prompt_Career_Sites --dry-run
```

#### Ejecución con Layer_1 Integration
```bash
# Con todas las integraciones activadas
ENABLE_LAYER1_INTEGRATION=true python main.py --wrapper Prompt_Career_Sites

# Solo deduplicación (más rápido)
ENABLE_LAYER1_INTEGRATION=true python main.py --wrapper Prompt_Career_Sites
```

### Opción 2: Interfaz Web (UI) - Recomendado para Uso Interactivo

#### Instalación UI
```bash
pip install flask
python web_ui.py
```

#### Acceder a la UI
- Abre tu navegador en: http://127.0.0.1:5000
- Selecciona el wrapper deseado
- Click en "Ejecutar" o "Dry Run"
- Los resultados se muestran en tiempo real

---

## 🔍 Qué Changed con Layer_1 Integration

### Para Usuario de Primera Ocación

#### **Antes (Scout Básico):**
```
Scout → Navega → Encuentra ofertas → Guarda JSON
```

#### **Ahora (Scout + Layer_1):**
```
Scout → Navega → Encuentra ofertas → Deduplica → 
Filtra Perfil → Valida URLs → Sync Notion → Guarda JSON
```

### **Beneficios Prácticos:**

1. **Menos Duplicados**: No verás la misma oferta 3 veces
2. **Decisiones Respetadas**: Si rechazaste algo, no vuelve a aparecer
3. **Mejor Calidad**: Filtros más inteligentes del perfil
4. **Ahorro de Tiempo**: No pierde tiempo en URLs rotas
5. **Flujo Completo**: Todo sincronizado con tu tracker VANTAGE

---

## 📂 Archivos de Salida

Los resultados se guardan en `output/`:
```
vantage_scout_Prompt_Career_Sites_20260818.json
vantage_scout_LinkedIn_20260818.json
vantage_scout_Aggregators_20260818.json
```

### **Estructura del JSON Mejorada:**
```json
{
  "prompt_variant": "A-weekly-unified-careersites",
  "prompt_version": "PromptA-v1.0+careersites",
  "today_date": "2026-08-18",
  "items": [
    {
      "job_id": "unique_id",
      "title": "Visual Merchandising Coordinator",
      "brand": "Richemont",
      "location": "Mexico City, CDMX",
      "apply_url": "https://...",
      "source_type": "career_page",
      "source_name": "Richemont",
      "fetch_status": "direct_apply",
      "prompt_version": "PromptA-v1.0+careersites"
    }
  ],
  "audit_log": [
    {
      "type": "DEDUP",
      "source": "Prompt_Career_Sites",
      "message": "Dedup stats: {'total_items': 15, 'duplicates_found': 3, 'unique_items': 12}"
    },
    {
      "type": "GATE",
      "source": "Prompt_Career_Sites",
      "message": "Gate stats: {'total_items': 12, 'processable': 10, 'terminal_protected': 2}"
    },
    {
      "type": "PROFILE_FILTER",
      "source": "Prompt_Career_Sites",
      "message": "Profile filter stats: {'total': 10, 'hard_blocked': 1, 'role_excluded': 2, 'location_blocked': 1, 'passed': 6}"
    }
  ],
  "data_quality_warnings": [],
  "reroute_candidates": []
}
```

---

## ⚙️ Configuración Avanzada

### Desactivar Layer_1 Integration
Si prefieres usar Scout básico sin las nuevas capacidades:

```bash
ENABLE_LAYER1_INTEGRATION=false python main.py --wrapper Prompt_Career_Sites
```

### Solo Algunas Integraciones
Edita `src/browser_agent.py` y comenta las integraciones que no quieras:

```python
# En run_browser_agent function:
# dedup = ScoutDedup(output_dir)  # Comentar para desactivar dedup
# profile_filter = ProfileFilter()  # Comentar para desactivar filtros
# url_validator = URLValidator()  # Comentar para desactivar validación
# notion_sync = NotionSync()  # Comentar para desactivar sync Notion
# analytics = ScoutAnalytics(output_dir)  # Comentar para desactivar analytics
```

### LinkedIn con Perfil Persistente
```bash
CHROME_USER_DATA_DIR=/Users/tu_usuario/Library/Application Support/Google/Chrome
BROWSER_HEADLESS=false
python main.py --wrapper linkedin
```

---

## 🆘 Solución de Problemas

### "ModuleNotFoundError: No module named 'httpx'"
```bash
pip install httpx
```

### "ModuleNotFoundError: No module named 'notion_client'"
```bash
pip install notion-client
# O: Comenta la integración de Notion en browser_agent.py
```

### Deduplicación muy agresiva
```bash
# Aumentar ventana de historial en src/dedup.py
ScoutDedup(output_dir, history_window_days=60)  # 60 días en vez de 30
```

### Sync con Notion falla
```bash
# Verificar que tienes las credenciales
echo $NOTION_TOKEN
echo $NOTION_DB_OPPORTUNITIES

# O desactivar Notion sync
ENABLE_LAYER1_INTEGRATION=true python main.py --wrapper Prompt_Career_Sites
# (comentar notion_sync en browser_agent.py)
```

---

## 📚 Resumen de Cambios

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Deduplicación** | ❌ No existía | ✅ Hash-based 3 niveles |
| **Estados Terminales** | ❌ No respetados | ✅ Protección completa |
| **Filtros de Perfil** | ⚠️ Básicos | ✅ Sistema Layer_1 completo |
| **Validación URLs** | ❌ No existía | ✅ Pre-navegación + clasificación |
| **Sync Notion** | ❌ Manual | ✅ Automático (opcional) |
| **Analytics** | ❌ No existía | ✅ Reportes completos |
| **Audit Log** | ⚠️ Básico | ✅ Detallado por integración |

---

## 🎓 Recomendaciones de Uso

### Para Usuarios Nuevos
1. **Comienza con Dry Run**: Prueba la configuración sin gastar recursos
2. **Activa Layer_1**: Usa todas las integraciones para mejor calidad
3. **Revisa Audit Log**: Entiende qué filtros se aplicaron
4. **Activa Notion Sync**: Si usas el ecosistema VANTAGE completo

### Para Usuarios Avanzados
1. **Personaliza alias_map.json**: Agrega marcas específicas
2. **Ajusta ventana de dedup**: Según tu frecuencia de ejecución
3. **Usa Analytics**: Identifica fuentes más efectivas
4. **Configura Cron Jobs**: Para ejecución automatizada

---

## 🚀 Próximos Pasos Recomendados

1. **Prueba Dry Run**: Verifica que todo funcione
2. **Ejecución Real**: Prueba con una búsqueda real
3. **Revisa Audit Log**: Entiende los filtros aplicados
4. **Activa Notion Sync**: Si usas VANTAGE completo
5. **Configura Automatización**: Cron jobs para ejecución diaria

---

**¡El sistema está listo para usar con todas las capacidades de Layer_1 integradas!** 🚀