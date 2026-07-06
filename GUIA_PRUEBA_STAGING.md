# Guía: Prueba de Staging para Saneamiento de Propiedades

**Fecha:** 2026-07-06  
**Objetivo:** Ejecutar layer_1_run.py en modo seguro antes de aplicar cambios a producción

---

## Opción 1: Agregar --dry-run a layer_1_run.py (RECOMENDADO)

### Paso 1: Modificar layer_1_run.py

Agregar al final del archivo (antes de `if __name__ == "__main__":`):

```python
# ── Dry-run mode ─────────────────────────────────────────────────────────────
DRY_RUN = "--dry-run" in sys.argv

if DRY_RUN:
    print("\n" + "="*60)
    print("DRY RUN MODE — No se escribirán cambios a Notion")
    print("="*60 + "\n")
```

Luego, en cada lugar donde se hace `client.pages.update()`, agregar:

```python
if not DRY_RUN:
    try:
        client.pages.update(...)
    except Exception as e:
        print(f"WARNING: Error {item['id'][:8]}: {e}")
else:
    print(f"[DRY-RUN] {item['id'][:8]}: actualizaría {list(update.keys())}")
```

### Paso 2: Ejecutar prueba

```bash
cd /Users/mauriciomeyran/Documents/04-Vantage_CV/Layer_1
python3 scripts/layer_1_run.py --dry-run
```

### Paso 3: Revisar output

El script mostrará qué cambios HARÍA hacer sin aplicarlos:
- Qué props se actualizarían
- Qué registros se afectarían
- Cuántas llamadas a API se harían

---

## Opción 2: Usar base de datos de prueba (si existe)

Si tienes una base de datos de prueba en Notion:

1. Crear variable de entorno para staging:
```bash
export NOTION_DB_ID="tu_staging_db_id"
```

2. Modificar layer_1_run.py para usar esa variable:
```python
ds_id = os.environ.get("NOTION_DB_ID", "production_db_id")
```

3. Ejecutar normal:
```bash
python3 scripts/layer_1_run.py
```

---

## Opción 3: Limitar a subset de datos (MÁS RÁPIDO)

Modificar layer_1_run.py para limitar query:

```python
# En query_all_items(), agregar límite
if "--test" in sys.argv:
    kwargs["page_size"] = 10  # Solo procesar 10 registros
```

Ejecutar:
```bash
python3 scripts/layer_1_run.py --test
```

---

## Recomendación

**Opción 1 (--dry-run)** es la más segura porque:
- No requiere base de datos de prueba
- No toca datos reales
- Muestra exactamente qué cambios se harían
- Es reversible

**Tiempo estimado:** 10-15 minutos para agregar el modo dry-run

---

## Verificación Post-Deploy

Después de aplicar cambios en producción:

1. Ejecutar `python3 scripts/test_layer1.py` (ya pasó 42/42)
2. Correr `health_check.py` para verificar integridad
3. Revisar 3-5 registros en Notion manualmente
4. Verificar que las props eliminadas (Match, Prioridad, Fuente) no están presentes

---

**FIN DE LA GUÍA**
