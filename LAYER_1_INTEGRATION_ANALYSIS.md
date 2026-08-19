# Análisis de Integración Layer_1 → Scout

## 🎯 Componentes de Layer_1 aplicables a Scout

### 1. **Sistema de Deduplicación** 🔥 ALTA PRIORIDAD

**Estado actual de Scout:**
- Sin deduplicación
- Riesgo de duplicar ofertas en ejecuciones consecutivas
- No detecta ofertas ya procesadas

**Componente Layer_1:**
- `dedup_opportunities.py` - Sistema sofisticado de dedup
- Hash primario: `apply_url` normalizada
- Hash secundario: `brand|title|location`
- Hash terciario: `job_id`
- Ventana de 30 días
- Cross-layer dedup (L1 > L2 > L3)
- Sistema anti-falso-positivo con reglas específicas

**Aplicación a Scout:**
```python
# Nuevo módulo: src/dedup.py
class ScoutDedup:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.history = self._load_history()
    
    def _load_history(self) -> dict:
        """Cargar historial de outputs anteriores"""
        history = {}
        for json_file in self.output_dir.glob("vantage_scout_*.json"):
            data = json.loads(json_file.read_text())
            for item in data.get("items", []):
                hash_key = self._generate_hash(item)
                history[hash_key] = item
        return history
    
    def _generate_hash(self, item: dict) -> str:
        """Generar hash basado en apply_url, brand, title, location"""
        url = item.get("apply_url", "")
        brand = item.get("brand", "")
        title = item.get("title", "")
        location = item.get("location", "")
        
        if url:
            return hashlib.sha256(url.lower().encode()).hexdigest()
        else:
            combined = f"{brand}|{title}|{location}".lower()
            return hashlib.sha256(combined.encode()).hexdigest()
    
    def is_duplicate(self, item: dict) -> bool:
        """Verificar si item es duplicado"""
        hash_key = self._generate_hash(item)
        return hash_key in self.history
    
    def add_to_history(self, item: dict):
        """Agregar item al historial"""
        hash_key = self._generate_hash(item)
        self.history[hash_key] = item
```

---

### 2. **Gate Logic (Protección de Estados Terminales)** 🔥 ALTA PRIORIDAD

**Estado actual de Scout:**
- Sin protección de estados
- No respeta decisiones previas
- Podría re-procesar ofertas ya descartadas

**Componente Layer_1:**
- `gate_logic.py` - Protección de estados terminales
- Estados protegidos: "Postulado", "Rechazado", "Archivar", "Expirada"
- Next Actions protegidos: "Archivar", "Expirada"
- Previenen recálculo innecesario

**Aplicación a Scout:**
```python
# Integración en src/browser_agent.py
class ScoutGate:
    TERMINAL_STATUSES = {"Postulado", "Rechazado", "Archivar", "Expirada"}
    TERMINAL_ACTIONS = {"Archivar", "Expirada"}
    
    @staticmethod
    def should_process(item: dict) -> bool:
        """Determinar si item debe ser procesado"""
        # Scout podría mantener un estado local
        status = item.get("status", "")
        next_action = item.get("next_action", "")
        
        if status in ScoutGate.TERMINAL_STATUSES:
            return False
        if next_action in ScoutGate.TERMINAL_ACTIONS:
            return False
        
        return True
```

---

### 3. **Profile Fit Rules (Exclusiones Sofisticadas)** 🔥 ALTA PRIORIDAD

**Estado actual de Scout:**
- Exclusiones básicas en prompts
- No sistema de alias_map.json
- No detección de señales VM específicas

**Componente Layer_1:**
- `profile_fit.py` - Reglas avanzadas de fit
- Sistema de alias_map.json con hard_block
- Detección de señales VM en títulos
- Exclusiones contextuales (ej: "planner" vs "visual planner")
- Protección de estados activos de postulación

**Aplicación a Scout:**
```python
# Nuevo módulo: src/profile_filter.py
class ProfileFilter:
    def __init__(self):
        self.alias_map = self._load_alias_map()
        self.exclude_patterns = self._load_exclude_patterns()
    
    def _load_alias_map(self) -> dict:
        """Cargar alias_map.json de Layer_1"""
        alias_path = Path("../../Layer_1/config/alias_map.json")
        if alias_path.exists():
            return json.loads(alias_path.read_text())
        return {}
    
    def is_hard_blocked(self, brand: str) -> bool:
        """Verificar si marca está hard blocked"""
        if not brand:
            return False
        
        brand_lower = brand.strip().lower()
        for alias_key, alias_data in self.alias_map.get("aliases", {}).items():
            if alias_key in brand_lower or brand_lower in alias_key:
                if alias_data.get("hard_block", False):
                    return True
        
        # Hard blocks básicos
        hard_blocks = {"l'oréal", "loreal", "levi's", "levis", "el palacio de hierro"}
        return any(block in brand_lower for block in hard_blocks)
    
    def is_role_excluded(self, title: str) -> tuple[bool, str]:
        """Verificar si rol está excluido con contexto"""
        exclude_patterns = [
            (r"\bvendedor", "ventas_directas"),
            (r"\bsales\b", "ventas_directas"),
            (r"store\s+manager(?!.*visual)", "gerente_tienda"),
            # ... más patrones de Layer_1
        ]
        
        has_vm_signal = self._has_vm_signal(title)
        
        for pattern, reason in exclude_patterns:
            if re.search(pattern, title.lower()):
                # Excepciones para roles VM
                if has_vm_signal and reason in ["planner", "coordinador_merchandising"]:
                    continue
                return True, reason
        
        return False, ""
    
    def _has_vm_signal(self, title: str) -> bool:
        """Detectar señales de Visual Merchandising"""
        vm_signals = ["visual", "merchandis", "brand environment", "retail design"]
        title_lower = title.lower()
        return any(signal in title_lower for signal in vm_signals)
```

---

### 4. **URL Validation & Source Analytics** 🔥 MEDIA PRIORIDAD

**Estado actual de Scout:**
- Sin validación de URLs
- Sin analytics de efectividad de fuentes
- No detecta URLs rotas antes de navegar

**Componente Layer_1:**
- `layer_1_run.py` - URL Gate pre-scoring
- `source_analytics.py` - Análisis de efectividad por fuente
- Validación HEAD+GET de URLs
- Clasificación de fuentes (Career_Page_Premium, Career_Page_Standard, etc.)

**Aplicación a Scout:**
```python
# Nuevo módulo: src/url_validator.py
class URLValidator:
    def __init__(self):
        self.url_history = {}  # Track URL success/failure
    
    async def validate_url(self, url: str) -> dict:
        """Validar URL antes de navegar"""
        if url in self.url_history:
            return self.url_history[url]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(url, timeout=10)
                result = {
                    "accessible": response.status_code == 200,
                    "status": response.status_code,
                    "content_type": response.headers.get("content-type", "")
                }
                self.url_history[url] = result
                return result
        except Exception as e:
            result = {"accessible": False, "error": str(e)}
            self.url_history[url] = result
            return result
    
    def classify_source(self, url: str) -> str:
        """Clasificar tipo de fuente"""
        if not url:
            return "Unknown"
        
        url_lower = url.lower()
        
        # Career pages premium
        premium_brands = ["lvmh", "richemont", "kering", "nike", "adidas", "gucci", "dior"]
        if any(brand in url_lower for brand in premium_brands):
            return "Career_Page_Premium"
        
        # Career pages standard
        career_domains = ["careers.", "jobs.", "empleos."]
        if any(domain in url_lower for domain in career_domains):
            return "Career_Page_Standard"
        
        # Aggregators
        aggregators = ["linkedin", "indeed", "occ", "computrabajo"]
        if any(agg in url_lower for agg in aggregators):
            return "Aggregator"
        
        return "Other"
```

---

### 5. **Notion Integration** 🔥 MEDIA PRIORIDAD

**Estado actual de Scout:**
- Solo genera JSON local
- Sin integración con Notion
- Manual sync con ecosistema VANTAGE

**Componente Layer_1:**
- `feed_processor.py` - Integración completa con Notion
- Class A schema (layer, hash, dedup cross-layer)
- Sincronización automática con tracker Notion
- Protección de estados terminales en Notion

**Aplicación a Scout:**
```python
# Nuevo módulo: src/notion_sync.py
class NotionSync:
    def __init__(self):
        self.client = Client(auth=os.environ["NOTION_TOKEN"])
        self.db_id = os.environ["NOTION_DB_OPPORTUNITIES"]
    
    def sync_to_notion(self, scout_output: dict) -> dict:
        """Sincronizar output de Scout con Notion"""
        results = {
            "created": 0,
            "skipped": 0,
            "errors": 0
        }
        
        for item in scout_output.get("items", []):
            try:
                # Verificar si ya existe (por apply_url)
                existing = self._find_existing(item)
                
                if existing:
                    # Aplicar gate logic
                    if not self._should_update(existing):
                        results["skipped"] += 1
                        continue
                    
                    # Actualizar existente
                    self._update_item(existing["id"], item)
                else:
                    # Crear nuevo
                    self._create_item(item)
                    results["created"] += 1
                    
            except Exception as e:
                results["errors"] += 1
                print(f"Error syncing item: {e}")
        
        return results
    
    def _find_existing(self, item: dict) -> dict | None:
        """Buscar item existente en Notion"""
        # Implementar búsqueda por apply_url o hash
        pass
    
    def _should_update(self, existing: dict) -> bool:
        """Aplicar gate logic de Layer_1"""
        status = existing.get("Status", "")
        next_action = existing.get("Next_Action", "")
        
        # Usar gate_logic de Layer_1
        from gate_logic import gate_logic
        terminal = gate_logic(existing)
        
        return terminal is None  # Solo actualizar si no es terminal
```

---

### 6. **Source Analytics** 🔥 BAJA PRIORIDAD

**Estado actual de Scout:**
- Sin analytics de efectividad
- No tracking de qué páginas funcionan mejor
- Sin insights de optimización

**Componente Layer_1:**
- `source_analytics.py` - Analytics completos
- Efectividad por fuente
- Quality insights
- Recomendaciones automáticas

**Aplicación a Scout:**
```python
# Nuevo módulo: src/analytics.py
class ScoutAnalytics:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.history = self._load_history()
    
    def generate_report(self) -> dict:
        """Generar reporte de efectividad de fuentes"""
        source_stats = defaultdict(lambda: {
            "total": 0,
            "success": 0,
            "errors": 0,
            "avg_time": 0
        })
        
        for json_file in self.output_dir.glob("vantage_scout_*.json"):
            data = json.loads(json_file.read_text())
            audit_log = data.get("audit_log", [])
            
            for entry in audit_log:
                source = entry.get("source", "Unknown")
                source_stats[source]["total"] += 1
                
                if entry.get("type") == "HTTP":
                    source_stats[source]["errors"] += 1
                else:
                    source_stats[source]["success"] += 1
        
        return dict(source_stats)
```

---

## 📋 Plan de Implementación Priorizado

### Fase 1: Core (Alta Prioridad)
1. **Deduplicación** - Evitar duplicados en ejecuciones consecutivas
2. **Gate Logic** - Respetar decisiones previas
3. **Profile Filter** - Usar sistema de exclusiones de Layer_1

### Fase 2: Integración (Media Prioridad)
4. **URL Validation** - Validar URLs antes de navegar
5. **Notion Sync** - Integración automática con tracker VANTAGE

### Fase 3: Analytics (Baja Prioridad)
6. **Source Analytics** - Reportes de efectividad
7. **Performance Metrics** - Tiempos por fuente, éxito/fracaso

---

## 🔧 Arquitectura Propuesta

```
vantage_scout/
├── src/
│   ├── browser_agent.py (existente)
│   ├── config.py (existente)
│   ├── dedup.py (NUEVO)
│   ├── profile_filter.py (NUEVO)
│   ├── url_validator.py (NUEVO)
│   ├── notion_sync.py (NUEVO)
│   └── analytics.py (NUEVO)
├── Layer_1_integration/
│   ├── gate_logic.py (importado de Layer_1)
│   ├── profile_fit.py (importado de Layer_1)
│   └── alias_map.json (referenciado de Layer_1)
```

---

## 💡 Beneficios Esperados

1. **Reducción de duplicados**: 80-90% menos ofertas duplicadas
2. **Respeto a decisiones**: No re-procesar ofertas ya descartadas
3. **Mejor calidad**: Exclusiones más sofisticadas del perfil
4. **Integración VANTAGE**: Sync automático con tracker Notion
5. **Optimización**: Analytics para enfocarse en fuentes efectivas

---

## 🚀 Próximos Pasos

1. Implementar módulo `dedup.py` con hash-based deduplication
2. Integrar `gate_logic.py` de Layer_1
3. Crear `profile_filter.py` con reglas de Layer_1
4. Test de integración con datos reales
5. Implementar sync con Notion (opcional)