# VANTAGE Scout Layer 1 - Guía Rápida

## 🚀 Formas de Ejecutar el Sistema

### Opción 1: Línea de Comandos (CLI) - Recomendado para Producción

#### Instalación
```bash
cd vantage_scout
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# Editar .env con tus API keys
```

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

#### Ver Manual Completo
```bash
cat MANUAL.md
```

---

### Opción 2: Interfaz Web (UI) - Recomendado para Uso Interactivo

#### Instalación UI
```bash
cd vantage_scout
pip install flask
```

#### Ejecutar UI
```bash
python web_ui.py
```

#### Acceder a la UI
- Abre tu navegador en: http://127.0.0.1:5000
- Selecciona el wrapper deseado
- Click en "Ejecutar" o "Dry Run"
- Los resultados se muestran en tiempo real

#### Características de la UI
- ✅ Selección visual de wrappers
- ✅ Monitoreo de estado en tiempo real
- ✅ Visualización de resultados históricos
- ✅ Estado de configuración
- ✅ Auto-refresh cada 30 segundos

---

## 📋 Comparación: CLI vs UI

| Característica | CLI | UI |
|----------------|-----|-----|
| **Producción** | ✅ Ideal | ⚠️ Requiere servidor |
| **Testing** | ✅ Rápido | ✅ Visual |
| **Monitoreo** | ⚠️ Manual | ✅ Automático |
| **Programación** | ✅ Cron/Scripts | ❌ Manual |
| **Facilidad de uso** | ⚠️ Técnico | ✅ Intuitivo |
| **Recursos** | ✅ Ligero | ⚠️ Flask server |

---

## 🎯 Flujo de Trabajo Recomendado

### Para Desarrollo/Testing
1. Usa la **UI Web** para pruebas interactivas
2. Ejecuta **dry runs** para validar configuración
3. Revisa resultados en la interfaz visual

### Para Producción
1. Usa **CLI** para ejecución programada
2. Configura **cron jobs** para ejecución automática
3. Monitorea archivos JSON en `output/` directory

---

## 📁 Archivos de Salida

Los resultados se guardan en `vantage_scout/output/`:
```
vantage_scout_Prompt_Career_Sites_20260818.json
vantage_scout_LinkedIn_20260818.json
vantage_scout_Aggregators_20260818.json
```

---

## 🔄 Integración Automatizada

### Script de Ejecución Completa
```bash
#!/bin/bash
# run_all_scouts.sh

cd /ruta/a/VANTAGE/vantage_scout

echo "🔍 Running Career Sites Scout..."
python main.py --wrapper Prompt_Career_Sites

echo "🔍 Running LinkedIn Scout..."
python main.py --wrapper linkedin

echo "🔍 Running Aggregators Scout..."
python main.py --wrapper aggregators

echo "✅ All scouts completed!"
```

### Configuración Cron (Ejecución Diaria)
```bash
# Editar crontab: crontab -e
# Ejecutar todos los scouts diariamente a las 9 AM
0 9 * * * cd /ruta/a/VANTAGE/vantage_scout && python main.py --wrapper Prompt_Career_Sites
0 10 * * * cd /ruta/a/VANTAGE/vantage_scout && python main.py --wrapper linkedin
0 11 * * * cd /ruta/a/VANTAGE/vantage_scout && python main.py --wrapper aggregators
```

---

## 🆘 Ayuda Rápida

### Problemas Comunes
- **Error de dependencias**: `pip install -r requirements.txt`
- **Error de Playwright**: `playwright install chromium`
- **Error de API key**: Configurar `.env` correctamente
- **Timeout**: Aumentar `BROWSER_MAX_STEPS` en `.env`

### Ver Logs
```bash
# Ver último resultado
cat output/vantage_scout_*.json | jq .

# Contar jobs encontrados
cat output/vantage_scout_*.json | jq '.items | length'
```

### Ejecutar Tests
```bash
pytest tests/ -v
```

---

## 📚 Documentación Adicional

- **Manual Completo**: `MANUAL.md`
- **Configuración**: `.env.example`
- **Tests**: `tests/` directory
- **Prompts**: `prompts/` directory

---

## 🎓 Recomendaciones de Uso

### LinkedIn
- Configura `CHROME_USER_DATA_DIR` con tu perfil
- Mantén sesión activa en LinkedIn
- Usa `BROWSER_HEADLESS=false` inicialmente

### Career Sites
- No requiere perfil persistente
- Headless mode funciona bien
- Menos detección anti-bot

### Agregadores
- Requiere más tiempo
- Aumenta `BROWSER_MAX_STEPS` si timeout
- Rate limiting es importante

---

**¡El sistema está listo para usar! Elige CLI para producción o UI para desarrollo interactivo.** 🚀
