---
name: vantage-documentacion-transversal
description: Genera y mantiene documentación transversal en los documentos fundacionales de VANTAGE (Kernel, Manual, Career Canon, System Prompt, Aliases, Changelog, Census) cuando se integra contenido nuevo, se modifica el flujo punta-a-punta, o se detecta un cambio estructural sin reflejar en la documentación. Integra cada pieza en su nodo natural de lectura — nunca como adendum al final del documento — y en tantos documentos fundacionales como el cambio realmente toque. USAR SIEMPRE que el usuario pida "documentación transversal", "parche orgánico", "actualizar Kernel/Manual", o cuando, en el curso de cualquier otra tarea, se detecte que un cambio de código, schema o flujo operativo no tiene su contraparte documental — incluso si el operador no lo solicitó explícitamente. Esta es la función de recordatorio no-bloqueante: no impide continuar la tarea original, pero señala el gap antes de cerrar la sesión.
---

# Documentación Transversal VANTAGE

Skill para integrar contenido nuevo en la base documental (Kernel, Manual, Career Canon, System Prompt) de forma orgánica, y para recordar al operador cuando un cambio estructural queda sin documentar — sin importar en qué sesión o cuenta se haya originado el cambio.

## Cuándo se activa

**Modo explícito:** el operador pide integrar contenido nuevo, un parche, o una actualización de Kernel/Manual.

**Modo recordatorio (no-bloqueante):** en cualquier punto de la sesión — incluso dentro de otra tarea — si se detecta:
- Un script, schema, o flujo operativo cambió pero ningún documento fundacional lo refleja.
- Una decisión de arquitectura se tomó en chat pero no quedó anclada a un `KERNEL:ID` o `MANUAL:ID`.
- El propio Changelog documenta un cambio pero no hay ID canónico asociado (mismo patrón de riesgo ya visto en v9.1.1/v9.2.6: un Changelog puede documentar un write que nunca persistió, o un cambio de código que nunca se explicó en el Kernel).

En modo recordatorio, señalar el gap y preguntar si se quiere generar el parche ahora o dejarlo en el Tracker — nunca bloquear la tarea original en curso.

## Principio rector: nodo natural, no adendum

Ningún parche se apila al final de un documento por comodidad. Cada pieza de contenido nuevo se integra en el nodo donde el flujo de lectura la necesita:

- **Kernel:** el orden de las secciones es orden de prioridad de lectura — si el contenido nuevo pertenece al inicio del flujo operativo, insertarlo ahí, no después de la última sección existente. Un parche que vive al final aunque pertenezca al principio no fue "tomado en cuenta" cuando el sistema lo necesitaba.
- **Manual:** se lee como narrativa progresiva de principio a fin — el parche debe encajar en la secuencia lógica del operador, nunca como capítulo aislado que rompe el hilo.
- La pregunta que resuelve el nodo no es "¿dónde cabe?" sino "¿en qué punto del flujo un lector que avanza en orden necesita esta información?".

El contenido nuevo puede tocar más de un documento fundacional (Kernel, Manual, Career Canon, System Prompt, Aliases, Changelog, Census) — identificar todos los que aplican, no asumir que uno solo basta. Generar tantos parches como sean necesarios para integrar el subproceso completo en su flujo punta a punta.

## Principio rector: extender, no reinventar

Este skill **no redefine** criterios de calidad documental — los hereda de `MANUAL:PATCH-QUALITY-001`, que ya establece los 5 filtros vigentes:

1. Invisibilidad estructural — el parche no debe notarse como "pegado"; hereda tono y jerarquía del documento padre.
2. Continuidad de voz — técnico-estratégico, directo, cero preámbulos (ver Bloque 02 de preferencias del operador).
3. Progresión narrativa — el documento se lee como flujo lógico, no como lista de partes.
4. Diff mínimo — cambiar lo necesario, no reescribir secciones completas si un parche quirúrgico basta.
5. Coherencia transversal — el cambio no debe contradecir otra sección sin resolución explícita.

Si en algún momento surge la tentación de definir un criterio de calidad nuevo, primero verificar si ya existe en `MANUAL:PATCH-QUALITY-001` — si existe, citarlo; si no, proponer su alta ahí, no crear un contrato paralelo.

## Protocolo de ejecución

Al activarse este skill (modo explícito o modo recordatorio con autorización de ejecutar), declara el inicio del protocolo respondiendo: BEGINNING DOCUMENTATION...

### Fase 1 — Mapeo y propuesta de nodo(s)

1. Identificar **todos** los documentos fundacionales que el cambio toca (no asumir uno solo).
2. **Fetch obligatorio inmediato antes de proponer nada** — `notion-fetch` en vivo de cada documento candidato, nunca desde memoria de sesión ni desde un volcado de texto previo. Esto también captura el string exacto del anchor (em-dashes, acentos, formato) para uso posterior.
3. Para cada documento, identificar el **nodo natural** de inserción según el principio rector (dónde el flujo de lectura lo necesita) — nunca el final del documento por default.
4. Presentar al operador el **bloque de propuesta** (sin contenido de parche todavía):
   - Documento(s) y nodo(s)/sección(es) exactos donde se integraría cada pieza.
   - Si se crearán IDs nuevos (`KERNEL:ID` / `MANUAL:ID` / etc.) o se reutilizan existentes.
   - Si dispara `KERNEL:CENSUS-SYNC` Regla 1 (alta/baja de ID canónico → regeneración de Census).
5. **Esperar autorización explícita de la propuesta de nodo(s)** antes de redactar un solo parche.

### Fase 2 — DRY RUN de parches + Aprobación

1. Una vez autorizada la propuesta de nodo(s), generar el DRY RUN real: contenido completo de cada parche, en su nodo ya autorizado, con los IDs nuevos (si aplica) ya definidos.
2. Validar cada parche contra los 5 filtros de `MANUAL:PATCH-QUALITY-001`.
3. **No escribir nada a Notion sin `APROBAR_WRITE` explícito** (tokens válidos: `APROBAR_WRITE`, `APROBAR`, `SÍ`, `sí`, `YEP`, `yep` — inválidos: `Ok`, `Go`, `yes`, `YES`). Esto aplica sin excepción, incluso si el operador ya vio un DRY RUN idéntico antes en la misma sesión, y es un gate distinto e independiente del de Fase 1.

### Fase 3 — Inyección

Escribir cada parche autorizado respetando:
- Jerarquía tipográfica preexistente (H1/H2/H3).
- Negritas para conceptos clave y KPIs, cursivas para roles/cargos — solo si el documento objetivo ya usa esa convención.
- Transición lógica con el párrafo anterior y posterior (progresión narrativa) — el parche vive en su nodo, no se apila.

### Fase 4 — Write-Back Verification (obligatoria, no opcional)

Después de cada escritura: **re-fetch de solo lectura** de la sección modificada (recargar el documento), comparando contra el contenido esperado. Si hay mismatch → `WRITE-BACK MISMATCH`, reportar y no continuar sin resolución (mismo mecanismo que `TCK-04`/Write-Back Verification en `vantage-session-close`). Un Changelog o confirmación en chat de que "ya se escribió" nunca es evidencia suficiente por sí sola.

### Fase 5 — Changelog y versión

1. Generar la entrada correspondiente en el Change Log (única fuente de historial de versión — nunca escribir changelog dentro de los documentos individuales).
2. Actualizar la propiedad Versión del Change Log (referencia oficial del sistema).
3. Confirmar al operador que Changelog y versión están escritos y verificados, para que corra `--sync` en Terminal sobre el resto de los documentos fundacionales.

### Fase 6 — Salida (Binary Gate)

Presentar al operador, para el resumen final de lo inyectado:
- **Opción A — Full Data Dump:** documento(s) completo(s) ya parchado(s), de una vez.
- **Opción B — Step-by-Step:** bloque por bloque, con explicación de cada cambio, esperando confirmación entre pasos.

Una vez entregado el resumen de salida, declara el cierre del protocolo respondiendo: DOCUMENTATION FINISHED

## Checklist de validación pre-cierre

Antes de considerar un parche como completo, verificar:

- [ ] **Nodo:** cada bloque nuevo vive en su nodo natural (Fase 1), ningún adendum al final por default.
- [ ] **Changelog:** entrada generada en el Change Log (`390938be-fc42-80e7-b429-d7d730339353`), versión actualizada y coincidente en los documentos tocados.
- [ ] **Census:** si se creó/eliminó un ID canónico, `KERNEL:CENSUS-SYNC` Regla 1 ejecutada.
- [ ] **Consistencia:** el parche no contradice el System Prompt ni otro documento fundacional (`SP:CONSISTENCY`); no duplica contenido ya existente.
- [ ] **Write-Back:** re-fetch de verificación (Fase 4) sin mismatch.
- [ ] **Sync:** operador confirmado para correr `--sync` en Terminal.
- [ ] **Binary Gate:** opción elegida (Full Data Dump / Step-by-Step) y confirmación recibida.

Si algún punto falla, detener y reportar el gap — no cerrar el parche a medias.

## Gestión de parches pendientes

Si el operador decide no aplicar el parche ahora, registrarlo en **Tasks Tracker** (`d2a65ca1-6a35-465d-bcff-b0d82dddd549`):
- Título: `[DOC] Parche pendiente: [descripción breve]`.
- Prioridad: Alta (flujo crítico) / Media (mejora no urgente) / Baja (cosmético).
- IDs relacionados: los `KERNEL:ID`/`MANUAL:ID` afectados o propuestos.
- Contexto: qué cambio documenta y por qué se pospuso.

Revisar el Tracker al inicio de cada sesión (`vantage-session-open`) para no perder parches pendientes.

## Reglas de oro

- **Cero paternalismo** — no explicar lo evidente, actuar como socio técnico.
- **Honestidad estructural** — si el contenido nuevo contradice algo ya documentado, DETENER y reportar la discrepancia (`SP:CONSISTENCY`) en vez de escribir sobre la contradicción.
- **Token-efficient** — densidad de información sobre extensión.
- **Fail-fast** — si Terminal no está disponible para verificación de versión y la tarea lo requiere, detener y reportarlo; no hay bypass automatizado vía MCP para ese chequeo (`KERNEL:FAIL-PHILOSOPHY`).

## Ejemplo práctico (único — auto-referencial)

La propia creación de este skill es su ejemplo canónico:

1. **Detección:** se identificó que el contrato de documentación transversal existía solo en chat, sin ID canónico ni skill formal.
2. **Nodo:** Technical Kernel, nodo natural junto a `KERNEL:CENSUS-SYNC`/`KERNEL:SESSION-LEDGER` (gobernanza documental), no como adendum al final.
3. **Propuesta (Fase 1):** alta de `KERNEL:DOCUMENTATION-TRANSVERSAL-001`, hereda los 5 filtros de `MANUAL:PATCH-QUALITY-001` en vez de redefinirlos.
4. **DRY RUN (Fase 2) → `APROBAR_WRITE` → Inyección (Fase 3) → Write-Back Verification (Fase 4).**
5. **Changelog + versión (Fase 5):** entrada en `390938be-fc42-80e7-b429-d7d730339353`, bump de versión, operador corre `--sync`.
6. **Este mismo `SKILL.md`** cita `KERNEL:DOCUMENTATION-TRANSVERSAL-001` como fuente canónica en vez de duplicar la lógica solo aquí (ver "Limitación conocida").

## Limitación conocida — alcance por cuenta/sesión

Este archivo vive en `/mnt/skills/user/` de una cuenta/instalación específica de Claude. **No viaja automáticamente a otra cuenta de claude.ai.** Si el objetivo es que el recordatorio de documentación transversal persista sin importar qué cuenta se use (el caso real que motivó este skill), la fuente de verdad tiene que vivir también en un documento que **sí** se fetchea igual en cualquier cuenta — es decir, una nota en `KERNEL` o `SYSTEM PROMPT` (vía Notion MCP), no solo este skill local. Recomendación: dar de alta un ID `KERNEL:DOCUMENTATION-TRANSVERSAL-001` que contenga el mismo contrato resumido, y que este skill lo cite como fuente canónica en vez de duplicar la lógica únicamente aquí.
