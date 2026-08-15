# Dedup Audit Guide

## Propósito
`dedup_opportunities.py` detecta duplicados mediante fuzzy matching (empresa ≥0.85, rol ≥0.7) y marca el campo `Dedup_Flag = "Posible duplicado"` en los registros elegibles.

## Cadencia de Ejecución

### Opción 1: Auditoría Manual (Recomendada)
Ejecutar el script manualmente cuando se sospeche acumulación de duplicados:

```bash
cd /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1
./scripts/dedup_audit.sh
```

o directamente:
```bash
python3 scripts/dedup_opportunities.py
```

**Frecuencia sugerida:** Semanal, como parte del tidy del Tracker.

### Opción 2: Integrado al Pipeline Principal
Ejecutar automáticamente como parte de `layer_1_run.py`:

```bash
python3 scripts/layer_1_run.py --dedup-audit
```

**Consideraciones:**
- Añade ~1-2 minutos al tiempo de ejecución del pipeline
- Se ejecuta después de todas las fases principales (Fase 6)
- Siempre respeta la protección de estados terminales (Gate_Decision=APPLIED, Next_Action ∈ {Archivar, Expirada})

### Opción 3: Limpieza de Falsos Positivos
Para limpiar un `Dedup_Flag` incorrecto (falso positivo):

```bash
python3 scripts/dedup_opportunities.py --clear <page_id>
```

Ejemplo:
```bash
python3 scripts/dedup_opportunities.py --clear 38b938befc4281d3953ac5e89d118413
```

## Qué Hace el Script

1. **Obtiene todas las oportunidades** del Tracker
2. **Aplica fuzzy matching** para detectar grupos de duplicados:
   - Similitud de empresa ≥ 0.85 (normalizada: sin "group", "ag")
   - Similitud de rol ≥ 0.7 (por intersección de keywords: visual, merchandising, coordinator, manager)
   - **Anti-falso positivo:** Excluye pares donde uno tiene "electrónica" y el otro no
3. **Filtra registros elegibles:**
   - Omite registros en estado terminal (Postulado, Rechazado, Next_Action=Archivar/Expirada)
   - Omite registros con Gate_Decision=APPLIED
4. **Marca TODOS los registros elegibles** del grupo con `Dedup_Flag = "Posible duplicado"`
5. **Reporta cambios** con IDs truncados para referencia

## Protección de Estados

El script respeta las restricciones del Kernel (KERNEL:GATE-DECISION-010):
- **NUNCA** modifica `Next_Action`
- **NUNCA** marca registros con `Gate_Decision=APPLIED`
- **NUNCA** modifica registros en estado terminal (Postulado, Rechazado, Archivar, Expirada)

## Lógica de Marcado (v8.3)

Para cada grupo de duplicados:
1. Filtra registros NO en estado terminal
2. **Marca TODOS los registros elegibles** del grupo (no solo uno)
3. Reporta cuántos del grupo fueron marcados vs cuántos se omitieron por estado terminal

Esto asegura evidencia completa: si hay 2 duplicados reales, ambos reciben el flag, no solo uno.

## Integración con Skills de Tidy

Los skills de tidy (ej. `vantage-tidy-opportunities-tracker`) pueden usar `Dedup_Flag = "Posible duplicado"` como señal para sugerir archivado automático de registros.

## Expiración por NAD Vencido

Desde v8.2, `layer_1_run.py` Fase 3.5.1 detecta automáticamente registros con NAD vencido y los marca como `Status = Expirada`, `Next_Action = Archivar`. Esta lógica corre en cada ejecución del pipeline principal, sin necesidad de flag adicional.

## Prevención de Falsos Positivos

El script incluye reglas anti-falso positivo:
- **Electrónica:** Excluye pares donde uno tiene "electrónica" y el otro no (evita agrupar retail general con retail especializado)
- **Estados terminales:** Respeta protecciones del Kernel
- **Limpieza manual:** Opción `--clear` para corregir falsos positivos residuales
