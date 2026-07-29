### `vantage-hyperlink-loop.skill`

**Description:** Ejecuta el ciclo completo de integridad de navegación de VANTAGE: regenera el V-ID-CENSUS, audita referencias huérfanas, aplica hipervínculos cross-reference en documentación local y sincroniza el resultado hacia Notion.

**Announce Convention**
- **Inicio:** `REGENERATING NAVIGATION LOOP...`
- **Fin:** `NAVIGATION LOOP FINISHED`

---

# 1. Contexto Operativo (Invariantes)

- **Naturaleza:** Esta skill únicamente orquesta el proceso. Ningún script es ejecutado automáticamente por Claude; toda ejecución ocurre en la Terminal del operador.

- **Precedencia Obligatoria:** El Census siempre debe regenerarse antes de cualquier sincronización o actualización de versión.

- **Single Source of Truth (SSOT):**
  - Notion es el repositorio final.
  - La documentación local es el área de trabajo donde se aplican y auditan los hipervínculos.

- **Modo de Operación:**
  - Todos los cambios deben validarse mediante Dry-Run antes de modificar archivos.

---

# 2. Procedimiento

## Paso 1 — Regenerar Census (`vcensus`)

Solicitar al operador ejecutar:

```bash
vcensus
```

### Auditoría

El operador debe pegar el resumen generado.

Verificar:

- IDs sin link.
- IDs sin resolver.
- IDs duplicados.
- Referencias rotas.
- Orphans detectados.

### Guard Conditions

Si existe cualquier:

- `IDs SIN LINK`
- `UNRESOLVED`
- `BROKEN REFERENCES`

→ detener inmediatamente el loop.

No continuar hasta corregir el ancla correspondiente en Notion o en la documentación local.

### Orphans

Si aparecen IDs huérfanos:

El operador deberá decidir:

- agregar el ID a `CENSUS_SPEC` dentro de:

```
generate_census.py
```

o

- marcarlo como ruido documental.

No continuar hasta resolver el estado.

---

## Paso 2 — Liberar escritura

La documentación permanece protegida mediante permisos 444.

Solicitar:

```bash
chmod u+w Documentación/ACTIVE/*.md
```

Verificar que los permisos fueron aplicados correctamente antes de continuar.

---

## Paso 3 — Aplicar Hyperlinks (`vhyperlinks`)

### Fase Dry-Run

Solicitar:

```bash
vhyperlinks
```

Auditar:

- cantidad de documentos modificados
- cantidad de links propuestos
- referencias descartadas
- warnings

### Validación

Si:

```
Links propuestos = 0
```

y existen documentos modificados recientemente,

detener el proceso y revisar:

```
apply_hyperlinks.py
```

especialmente:

- MAPPING
- Regex
- Exclusiones

No ejecutar Apply hasta resolverlo.

---

### Fase Apply

Una vez aprobado el diff:

```bash
vhyperlinks --apply
```

---

## Paso 4 — Restaurar Integridad

Restaurar protección de archivos.

```bash
chmod 444 Documentación/ACTIVE/*.md
```

---

## Paso 5 — Sincronizar hacia Notion

Ejecutar:

```bash
vdoc local
```

### Validación

El operador debe confirmar visualmente que referencias como:

```
KERNEL:PURPOSE
PIPELINE:ACTIVE-RECON
TRACKER:STATUS
```

son ahora hipervínculos clickeables dentro de Notion.

---

## Paso 6 — Sincronizar Versiones

Ejecutar:

```bash
vversions --sync
```

La ejecución únicamente se considera exitosa cuando el resultado final contiene:

```
[VEREDICTO FINAL] PASS
```

---

# 3. Reglas de Oro

## No Auto-Link

El encabezado donde nace un V-ID nunca debe transformarse en hipervínculo.

Únicamente las referencias posteriores son elegibles para enlace.

Esta lógica pertenece exclusivamente a:

```
apply_hyperlinks.py
```

y nunca debe modificarse manualmente.

---

## Fail Fast

Si el operador no dispone de Terminal o acceso al repositorio local,

la skill entra automáticamente en:

```
MODO DEGRADADO
```

En este modo:

- no se simulan links
- no se editan documentos
- no se utilizan herramientas MCP para reemplazar el proceso

La skill únicamente documenta el estado pendiente.

---

## Limpieza Técnica

Si durante `vcensus` aparecen IDs con:

- Sección hardcodeada
- Heading inconsistente
- Alias heredados

registrar automáticamente un:

```
[TASK]
```

para normalización documental en la siguiente sesión.

---

# 4. Reporte Final

Al finalizar generar un resumen con el siguiente formato.

```
NAVIGATION LOOP REPORT

Census
-------
IDs resueltos:
164 / 164

Broken References:
0

Unresolved IDs:
0

Orphans:
0

Hyperlinks
----------
Links inyectados:
72

Documentos modificados:
12

Version Sync
------------
Versión:
v9.9.x

Estado:
PASS

Notion Sync
-----------
Sincronización:
OK

Resultado Final
---------------
NAVIGATION LOOP FINISHED
```