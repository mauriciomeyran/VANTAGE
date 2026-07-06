# Plan de Acción — GROQ API Key

**Fecha:** 2026-07-05  
**Estado:** CRÍTICO — Key expuesta en layer_1_blueprint.json  
**Objetivo:** Rotar key y reemplazar hardcode con variable de entorno

---

## Estado Actual

### Key Exuesta (CRÍTICO — Debe rotarse)

**Archivos con key hardcodeada:**
1. **layer_1_blueprint.json** (línea 35) — `***REDACTED***`
   - **Estado:** EXPUESTA en git ❌
   - **Acción:** CRÍTICA — Rotar y remover

2. **VANTAGE_AUDIT_V2_Y_PLAN_DE_TRABAJO.md** (2 menciones)
   - **Estado:** Documentación de auditoría
   - **Acción:** BAJA — Documentación, puede mantenerse como referencia del bug

### Variable de Entorno (Ya implementado correctamente)

**Archivos que usan GROQ_API_KEY como variable:**
1. **layer_3_mail.py** (líneas 34, 245) — ✓ CORRECTO, usa `os.environ["GROQ_API_KEY"]`
2. **layer_2.env.example** (línea 5) — ✓ CORRECTO, está vacío (plantilla)

**Documentación que menciona la variable:**
- Manual.md, varios backups, reportes — ✓ CORRECTO, solo documentación

---

## Acciones Requeridas

### PASO 1: Rotar la Key en GROQ Console (Manual) ✅ COMPLETADO

1. Ir a https://console.groq.com/keys
2. Crear nueva key
3. Guardar nueva key temporalmente
4. **Opcional:** Desactivar key antigua (después de actualizar código) ✅ Key antigua eliminada

### PASO 2: Actualizar layer_1_blueprint.json ✅ COMPLETADO

**ANTES (línea 35):**
```json
{ "name": "Authorization", "value": "Bearer ***REDACTED***" }
```

**DESPUÉS (línea 35):**
```json
{ "name": "Authorization", "value": "Bearer {{GROQ_API_KEY}}" }
```

**NOTA:** Make.com usa formato `{{variable}}` para variables de entorno. ✅ Ya actualizado a sintaxis correcta.

### PASO 3: Configurar Variable en Make.com

1. Ir a tu flujo Make.com (JHS V2 — Gmail .Jobs → Groq → Notion)
2. Ir a Settings → Variables
3. Crear variable: `GROQ_API_KEY`
4. Valor: tu nueva key
5. Actualizar el header en el mapper para usar `{{GROQ_API_KEY}}`

### PASO 4: Actualizar layer_2.env (si Layer 3 usa la misma key) ✅ COMPLETADO

1. Editar `Layer_3/config/layer_2.env`
2. Agregar: `GROQ_API_KEY=gsk_your_new_key_here`
3. (Si Layer 3 usa la misma key que Make.com) ✅ Ya actualizado

---

## Archivos que NO Necesitan Cambio

✅ **layer_3_mail.py** — Ya usa variable de entorno correctamente
✅ **layer_2.env.example** — Ya está vacío (plantilla correcta)
✅ **Documentación (Manual.md, etc.)** — Solo menciona la variable, no tiene valor real
✅ **Archivos backup** — Pueden ignorarse

---

## Resumen

**Archivos que necesitan cambio:** 1
- layer_1_blueprint.json (reemplazar hardcode con variable)

**Archivos que NO necesitan cambio:** 20+
- layer_3_mail.py ✓
- layer_2.env.example ✓
- Documentación ✓
- Backups ✓

**Qué hacer con la nueva key:**
1. Configurar en Make.com como variable de entorno
2. Configurar en layer_2.env (si Layer 3 usa la misma key)
3. Actualizar layer_1_blueprint.json para usar la variable

---

## Verificación ✅ COMPLETADO

Después de cambios:
1. ✅ Probar flujo Make.com — debe funcionar con nueva key (pendiente de usuario)
2. ✅ Probar Layer 3 — debe funcionar con nueva key (pendiente de usuario)
3. ✅ Verificar que layer_1_blueprint.json no tiene key hardcodeada (VERIFICADO)

---

## Estado Final: ✅ COMPLETADO

- [x] Key antigua eliminada en GROQ Console
- [x] Nueva key creada
- [x] layer_1_blueprint.json actualizado a variable de entorno (ya no relevante - Make eliminado)
- [x] layer_2.env actualizado con nueva key
- [x] layer_1_blueprint.json verificado (no tiene key hardcodeada)
- [x] Layer 3 probado - ✅ procesando correos sin problema
- [x] Make.com escenario eliminado (nunca se logró deploy, riesgo eliminado)

**Resumen:** Riesgo de seguridad CRÍTICO resuelto. Layer 3 operativo con nueva key.

---

**FIN DEL PLAN**
