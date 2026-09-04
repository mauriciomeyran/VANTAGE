---
name: vantage-cv-b
description: Fase 2 del pipeline de CV de VANTAGE (KERNEL:CV-PIPELINE-002) — construye el CV final aplicando el Output Contract Framework para integración directa con Figma, a partir de un HANDOFF generado por vantage-cv-a. Usar cuando el operador invoque el trigger "CV-B [HANDOFF]", pegue o adjunte un HANDOFF de CV-A y pida construir el CV, o pida generar el Markdown con Figma Tags para una vacante ya analizada. También activar si el operador pide "serializar" un CV para Figma o menciona figma_text_id, Golden Skeleton o Figma Sync Protocol. No usar sin un HANDOFF previo de vantage-cv-a — si no existe, redirigir primero a esa skill. No usar para el análisis inicial de la vacante (eso es vantage-cv-a) ni para la auditoría final del PDF (eso es vantage-qa).
---

# VANTAGE — Skill CV-B (Construcción y Contrato de Salida)

ID Canónico: `KERNEL:CV-PIPELINE-002` · Trigger: `CV-B [HANDOFF]`
Versión de alineación: v10.1.1 — Registry Membership Guard (2026-09-03)

## Responsabilidad

Segunda fase del pipeline de CV. Toma el HANDOFF de `vantage-cv-a` y construye el CV final serializado en Markdown con Figma Tags, listo para sincronizar con el archivo Figma vía el Output Contract Framework (`CANON:OUTPUT-CONTRACT`).

## Invariante de sesión

**Cero prosa en el chat.** Esta skill no conversa sobre la construcción del CV en el cuerpo del mensaje. El único output permitido es un archivo `.md` descargable que contenga el CV completo. Cualquier explicación, aclaración o duda va dentro del propio archivo, no como texto de chat adicional.

Excepción: si el HANDOFF está incompleto, el Positioning Mode no está resuelto o la Verificación Pre-Entrega detecta un bloqueo que requiere input humano, se puede preguntar al operador. Una vez resuelto, el resultado sigue siendo solo el archivo.

## Fuera de scope

Esta skill entrega **Markdown con figma_text_id**. Cómo el plugin de Figma consume, parsea o transforma ese Markdown (JSON intermedio, `boldRanges`, regex de parser, `ui.html` o scripts downstream) está fuera del scope de CV-B y no se especula sobre ello.

- Ante una falla de render en Figma, declarar: `Fuera de scope de CV-B — necesito ver el script/plugin fuente real antes de diagnosticar.`
- El formato exacto del tag (`###### [figma_text_id](2:4)`, con corchetes y sin escapar `#`) sí está dentro de scope: se copia carácter por carácter desde el Golden Skeleton vigente, nunca se reconstruye de memoria.

## Input requerido

HANDOFF completo generado por `vantage-cv-a`, incluyendo:
- Empresa y rol
- Positioning Mode seleccionado
- Gap Analysis (`fit_gaps`, matches directos, parciales y gaps)
- `JD_keywords_top6`
- Idioma
- Validación de exclusiones en estado PASA

Si el HANDOFF está incompleto o el Positioning Mode reporta `EMPATE — requiere decisión humana` sin resolución explícita, detener y solicitar que se complete CV-A primero.

Si `cv_b_eligible: false` y el mismo HANDOFF no incluye `operator_override: true`, detener y rechazar el HANDOFF. El override debe ser un campo positivo declarado; nunca se infiere por ausencia de bloqueo explícito.

Si `observaciones` señala una desalineación de seniority no resuelta, declarar `STATUS=AWAITING_OPERATOR_ANGLE` y detener. No elegir un ángulo por default ni inferir resolución entre turnos.

## Protocolo Figma Sync

Referencia: `CANON:OUTPUT-CONTRACT-001`. Los puntos siguientes son no negociables.

### 1. Inmutabilidad de IDs

Los `###### figma_text_id` son llaves primarias. Está prohibido alterarlos, omitirlos o inventar nuevos. El SSOT de IDs de nodo es `registry_seed.json` en `04-Vantage_CV/Figma Sync/`; ante discrepancia, el registry gana.

### 2. Integridad de slots

No se permiten fusiones ni divisiones de bloques. Si el Golden Skeleton tiene cuatro bullets para una experiencia, el output debe conservar cuatro bloques, incluso cuando uno quede vacío. Slot Integrity gobierna el conteo de bloques, no limita a un solo hecho del Canon por slot.

### 3. Regla de llenado nulo

Si el Career Canon no ofrece información suficiente para un slot, conservar el ID original y usar `[PENDING DATA]` o dejar el contenido vacío; nunca eliminar el slot. `[PENDING DATA]` solo es válido después de intentar Match Transferible Obligatorio y fallar.

### 4. Escaping

El formato exacto del tag es: `###### [figma_text_id](N:N)` donde:
- `######` : exactamente 6 caracteres hash, sin espacios
- `[figma_text_id]` : literal "figma_text_id" entre corchetes
- `(N:N)` : el ID numérico del registry entre paréntesis
- **PROHIBIDO**: cualquier variación como `[N:N](N:N)`, `[N:N|](N:N)`, espacios adicionales, o caracteres especiales en el label

Replicar el escaping de `(` y `)` únicamente si el Golden Skeleton vigente lo usa. Nunca normalizar ni modificar por preferencia.

### 5. Distinctiveness Rule

Cada bullet de Experience responde al Gap Analysis del HANDOFF activo (`fit_gaps`, `JD_keywords_top6`), no a una plantilla fija por Positioning Mode.

### 6. Match Transferible Obligatorio

Antes de marcar un slot como `[PENDING DATA]`, intentar reencuadrar un hecho disponible del Career Canon bajo terminología relevante al JD activo, incluso si no existe coincidencia literal con `JD_keywords_top6`. `[PENDING DATA]` solo aplica cuando ningún hecho del Canon, directo o reencuadrado, es transferible al eje temático de la vacante.

Anti-overselling gobierna por separado y tiene prioridad: no reencuadrar ni sintetizar un hecho si afirma una responsabilidad que el JD contradice activamente. Match Transferible no autoriza inventar ni elevar ownership.

- Válido: `coordiné ejecución visual 17 tiendas + 12 corners` → `coordinación de ejecución visual multi-punto de venta` para un JD regional.
- Inválido: `lideré 3 coordinadoras directas` reencuadrado para un JD individual contributor explícito.

Un reencuadre nunca puede subir el nivel de ownership del hecho original. Verbos permitidos cuando corresponden al Canon: coordinar, supervisar, alinear, colaborar con, dar seguimiento a. Verbos de ownership pleno — dirigir, gestionar end-to-end, desarrollar desde concepto, poseer, liderar el desarrollo de — solo se usan si existen literalmente en el Canon.

## Estructura Golden Skeleton

Referencia: `CANON:OUTPUT-CONTRACT-002`. Antes de generar cualquier output, leer `registry_seed.json` vigente. Nunca usar una tabla de IDs memorizada o hardcodeada en esta skill.

El registry mapea `slot_name` a `figma_text_id`; sus llaves ordenadas C01→C05 constituyen la referencia física de secuencia, además de la regla explícita en `CANON:OUTPUT-CONTRACT-005`.

**Formato estricto de tags:**
- Cada tag debe seguir exactamente el formato: `###### [figma_text_id](N:N)`
- El label entre corchetes debe ser literalmente `figma_text_id`, nunca el ID numérico
- No permitir variaciones como `[N:N](N:N)`, `[N:N|](N:N)`, o caracteres especiales
- Esta regla es no negociable y gana sobre cualquier template o memoria previa

Si el registry no está disponible o no se puede leer, detener la generación y solicitarlo al operador. No inventar ni asumir IDs.

## Auditoría de identidad

El conteo no valida identidad estructural. Antes de entregar, verificar simultáneamente:

1. `COUNT(figma_text_id)_SKELETON == COUNT(figma_text_id)_OUTPUT`.
2. Cada `figma_text_id` del output pertenece literalmente al `registry_seed.json` vigente.
3. Cada ID del registry aparece exactamente una vez en el output, salvo slots explícitamente excluidos por el Skeleton vigente.
4. La secuencia de IDs del output corresponde exactamente a la secuencia del Golden Skeleton.
5. **Formato de label**: cada tag debe usar exactamente `[figma_text_id]` como label, no `[N:N]` ni variaciones.
6. **Caracteres prohibidos**: no permitir caracteres especiales como `|`, `{`, `}` en los labels de los tags.

Un schema heredado puede conservar la cantidad esperada y aun así fallar si contiene IDs obsoletos, slots fusionados, slots desplazados, o formato de label incorrecto. Si falla conteo, membership, unicidad, correspondencia de secuencia o formato de label, abortar y re-mapear antes de declarar `PASS_FOR_FIGMA`.

## Densidad por síntesis multi-hecho

Cuando el Canon contiene múltiples datos relacionados y transferibles para un mismo slot, sintetizarlos en un bullet denso:

```text
**[Etiqueta temática en bold]:** [Hecho 1 del Canon]; [Hecho 2 relacionado], [Hecho 3 relacionado si aplica].
```

Reglas:
1. Cada hecho debe existir literalmente en el Canon; la síntesis combina datos reales, nunca interpola relaciones no documentadas.
2. La etiqueta bold nombra la categoría funcional real del conjunto de hechos.
3. Un slot puede contener un hecho aislado sin etiqueta si es el único dato relevante.
4. `[PENDING DATA]` solo aplica tras intentar el Match Transferible Obligatorio y documentar el fallo.

## Contenido de skills

Los cinco slots de Skills deben mapear a las cinco categorías de `CANON:SKILLS`:

- Estrategia Visual
- Operaciones & Finanzas
- Liderazgo & Training
- Stack Técnico
- Idiomas

Las cinco categorías requieren contenido antes de considerar completo el CV-B. Match Transferible aplica también a estos slots.

## Positioning Mode

Referencia: `CANON:OUTPUT-CONTRACT-005`. El Positioning Mode N1–N4 declarado en el HANDOFF gobierna tagline, perfil, skills y el énfasis de los bullets de Experience. No modifica el orden ni la existencia de slots: Experience conserva siempre C01→C05.

No mezclar bullets de dos Positioning Modes en un mismo CV-B. El modo determina énfasis y ángulo; la disponibilidad de contenido la determina Match Transferible Obligatorio.

## Reglas de serialización

Referencia: `CANON:OUTPUT-CONTRACT-004`.

- Cada tag es un párrafo independiente, sin listas ni bullets manuales (`•`, `-`, `*`) al inicio.
- Bold se reserva para keywords estratégicos dentro del párrafo.
- Empresa: bold standalone en su propio tag.
- Rol: `**rol** *período*`.
- Skills: `Categoría: texto plano`.
- Tagline: `[Título · Subtítulo] · Ciudad | Tel | Email | LinkedIn | Portfolio`.
- Mantener `&` en nombres de empresa.
- Replicar exactamente el escaping que muestre el Golden Skeleton para cada slot.

## Política de idioma

- `HANDOFF.idioma = ES`: CV-B íntegramente en español, salvo nombres propios, software y títulos oficiales de certificación o institución.
- `HANDOFF.idioma = EN`: CV-B íntegramente en inglés bajo el mismo criterio.
- Si el idioma del cuerpo no coincide con `HANDOFF.idioma`, declarar `STATUS=BLOCKED_LANGUAGE_MISMATCH` y no generar el archivo.

## Verificación pre-entrega

Esta verificación corre internamente antes de crear el archivo. No se muestra como output intermedio en chat.

1. **Formato y membership de tags:** extraer el ID entre paréntesis `(N:N)` de cada tag, ignorando el label entre corchetes; validar membership exacta contra `registry_seed.json`. Rechazar IDs inexistentes, convenciones mixtas de tag o el placeholder literal `figma_text_id` sin ID real.
   - Validar específicamente que el label sea exactamente `[figma_text_id]` (no `[N:N]`, `[N:N|]`, etc.)
   - Rechazar tags con caracteres especiales en el label (como `|`, `{`, `}`, etc.)
   - Verificar que no haya espacios entre `######` y `[`
2. **Integridad estructural:** validar conteo, membership, unicidad y secuencia exacta contra el Golden Skeleton conforme a la Auditoría de identidad.
3. **Sin bullets manuales:** ningún párrafo dentro de un tag puede iniciar con `•`, `-`, `*` o número seguido de punto.
4. **Pendientes justificados:** por cada `[PENDING DATA]`, el footer debe declarar el hecho del Canon evaluado, el reencuadre intentado y la causa del fallo: ausencia real, Anti-overselling o mismatch total de disciplina.
5. **Cross-check de sesión:** si el mismo `figma_text_id` tuvo contenido válido en un CV-B previo de la misma sesión y ahora está en `[PENDING DATA]`, tratarlo como alerta de probable omisión y repetir el análisis de Match Transferible.
6. **Idioma:** confirmar coincidencia entre el cuerpo del CV-B y `HANDOFF.idioma`.
7. **Integridad de code fences:** si el footer de metadata incluye bloques de código JSON, verificar que los delimitadores ``` estén correctamente emparejados (apertura y cierre). Un code fence sin cierre corrompe el parseo downstream.
8. **Anti-cloning:** ningún bullet de Experience puede coincidir verbatim con un CV-B previo del mismo Positioning Mode en la sesión o batch. Re-derivar la redacción desde el HANDOFF activo; el mismo hecho canónico puede reutilizarse si cambia el ángulo y la redacción.

## Restricción de lote

CV-B procesa exactamente un HANDOFF por invocación. Si el operador entrega un batch, procesar solo el primero, completar su ciclo y detener hasta recibir una invocación separada para el siguiente.

## Nombre del archivo

Referencia: `KERNEL:NAMING-CONVENTION`.

```text
{YYYY}_{FirstName}_{LastName}_{Empresa}_{Rol}_CV-B.md
```

- `YYYY`: año de la sesión.
- `FirstName_LastName`: `Mauricio_Meyran`.
- `Empresa` y `Rol`: extraídos del HANDOFF y normalizados, con espacios convertidos a guiones bajos, sin acentos ni caracteres especiales.
- `CV-B`: fase fija.

Ejemplo: `2026_Mauricio_Meyran_Dior_VM_Trade_Coordinator_CV-B.md`.

Si falta empresa o rol, detener y solicitarlo; no usar placeholders.

## Entrega

Generar un único archivo `.md` descargable mediante `create_file`. No renderizar el Markdown del CV en chat ni pedir confirmación adicional para crear el artefacto.

El archivo debe incluir un footer de metadata con:

- Versión del Output Contract.
- Positioning Mode activo.
- Referencia canónica al Canon usado.
- Resultado de la Verificación Pre-Entrega.
- Justificación de cada `[PENDING DATA]`, si existe.

Después de crear el archivo, releerlo y verificar la codificación de caracteres acentuados y `ñ`. Si hay corrupción, no entregar; reportar el error antes de reintentar.

**Verificación post-generación adicional:**
1. Confirmar que no existen tags con formato incorrecto (usar regex para detectar `[N:N](N:N)` o variaciones)
2. Verificar que no hay caracteres especiales prohibidos en los labels (como `|`)
3. Validar la integridad de los code fences en el footer de metadata
4. Ejecutar un diff final contra el Golden Skeleton para asegurar que solo cambió el contenido, no la estructura