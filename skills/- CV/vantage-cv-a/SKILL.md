---
name: vantage-cv-a
description: Fase 1 del pipeline de CV de VANTAGE (KERNEL:CV-PIPELINE-001) — procesamiento inicial y validación de fit estratégico de una vacante contra el Career Canon de Mauricio Meyrán. Usar cuando el operador invoque el trigger "CV-A [URL/JD]", pegue una URL de vacante o un Job Description crudo pidiendo análisis, o pida identificar el Positioning Mode (N1-N4) para una oportunidad específica. También activar si el operador pide "gap analysis" de una vacante contra su trayectoria, o pida preparar el primer paso del pipeline de CV antes de construir el documento final (CV-B). No usar para construir el CV en sí (eso es vantage-cv-b) ni para auditoría de PDF final (eso es vantage-qa).
---

# VANTAGE — Skill CV-A (Análisis y Alineación)

ID Canónico: `KERNEL:CV-PIPELINE-001` · Trigger: `CV-A [URL/JD]`
Versión de alineación: v9.16.0 (validado vs Kernel, Manual, Career Canon — 2026-08-09)

## Responsabilidad

Primera fase del pipeline de CV. Procesa una vacante (URL + Job Description) y produce un HANDOFF estructurado que sirve de input exclusivo para `vantage-cv-b`. No construye el CV — solo analiza y decide.

## Invariante de Sesión — Sandbox-only

**Cero prosa en el chat.** Esta skill no conversa sobre el análisis en el cuerpo del mensaje. El único output permitido es un archivo `.md` descargable que contenga el HANDOFF completo. Cualquier explicación, aclaración o duda va dentro del propio archivo, no como texto de chat adicional.

Excepción: si falta el Career Canon o hay una ambigüedad bloqueante en el Positioning Mode (ver Regla de Desempate abajo), sí se puede preguntar al operador antes de generar el archivo — pero una vez resuelto, el resultado sigue siendo solo el archivo.

## Scope Lock — Prohibiciones de Fase (KERNEL: CV-À SCOPE LOCK)

**Prohibido** en esta fase:
- Evaluar fit estratégico ("¿me conviene esta vacante?") — eso lo decide Score (Python) + el operador, nunca CV-A.
- Cuestionar o re-evaluar la `Gate_Decision` ya tomada por Python.
- Emitir verbos de decisión sobre el gate ("bloquear", "pasa") en cualquier parte del HANDOFF.

Cualquier discrepancia detectada durante el análisis (dato faltante, JD ambiguo, posible error en la Gate_Decision previa) se documenta en el campo `observaciones` del HANDOFF — nunca como recomendación de descarte ni como verbo de decisión.

## Input requerido

- URL de la vacante
- Job Description crudo (texto completo, no resumen)

Si el operador solo da una URL sin JD pegado, usar `web_fetch` para obtener el JD real antes de proceder. No inferir contenido de JD a partir del título del puesto.

## Contrato Operativo — Pasos

### 1. Identificar Positioning Mode (N1–N4)

Referencia: `CANON:POSITIONING` (Career Canon, sección 11) + `MANUAL:POSITIONING-CRITERIA` (§19).

| Modo | Ancla canónica | Señal de Alarma (no usar si...) |
|---|---|---|
| N1 · Luxury Brand Execution | C01 (L'Oréal Luxe) · 3 marcas lujo · CAPEX/OPEX · NPI | JD es retail masivo/fast fashion o venta por volumen, sin componente multi-marca de lujo |
| N2 · Store Design & Flagship Execution | C02 (Bisonte/Adidas) · Adidas Brand Center · KPI07 · blueprints | JD solo menciona "diseño" sin obra física, planos ni coordinación con arquitectos |
| N3 · Regional Brand Execution & Rollout | C03 (Levi's/Dockers) · 270+ POS · 6 países · KPI03–06 · CF05 | JD es de un solo mercado/tienda, sin alcance multi-país |
| N4 · Commercial VM & Field Leadership | C04/C05 (Aéropostale/Palacio de Hierro) · +43% tráfico · +18% conversión · 21 reportes | JD no reporta KPIs comerciales medibles (tráfico/conversión) ni involucra equipos de campo |

Mapea las keywords del JD contra las anclas de cada modo. El modo con más matches gana. Algoritmo determinista de 4 pasos:
1. **Keywords** — extraer `JD_keywords_top6` del JD.
2. **Mapeo** — alinear cada keyword contra los anclajes canónicos de `CANON:POSITIONING`.
3. **Conteo** — contar matches por ancla.
4. **Desempate** — si dos o más modos empatan, aplicar la Regla de Desempate abajo.

### 2. Regla de Desempate en JDs híbridos

Referencia: `CANON:POSITIONING-004`, `MANUAL:POSITIONING-CRITERIA` (§19).

Cuando el JD activa criterios de dos o más modos simultáneamente, en orden de precedencia:

1. El modo con mayor número de keywords del JD mapeados a su ancla canónica.
2. En empate de keywords: el modo de mayor seniority estratégico (N2 > N1, N4 > N3 cuando el JD tiene presupuesto regional explícito).
3. En empate persistente: **no decidir unilateralmente.** Declarar el empate en `fit_gaps` del HANDOFF — nombrando qué dos modos empataron, cuántos keywords mapeó cada uno, y qué falta para resolverlo sin intervención humana (ej. "N1 vs N2 empatados 3-3 — JD menciona lujo y construcción de flagship en igual peso; falta señal de presupuesto regional para desempatar por seniority") — y escalar a decisión humana antes de proceder con CV-B.

El Positioning Mode seleccionado (o el empate declarado) se documenta explícitamente en `positioning_rationale`. Sin este campo, el HANDOFF está incompleto y no avanza a CV-B.

### 3. Gap Analysis vs. Career Canon

Compara los requisitos del JD contra el Career Canon (Experience Records, Skills Canon, KPIs, Canonical Facts). Para cada requisito relevante del JD:
- **Match directo:** referencia al ID canónico que lo respalda (ej. `KPI03`, `CF05`).
- **Match parcial:** nota qué tan cerca está y qué falta.
- **Gap:** requisito sin soporte en el Canon. Nunca inventar experiencia para cerrar un gap — el gap se documenta, no se rellena.

### 4. Validación de exclusiones

Antes de continuar, verificar que la vacante no provenga de un empleador con bloqueo total de recontratación: **L'Oréal (todas las divisiones), Levi's/Dockers, El Palacio de Hierro**. Ninguno de los tres recontrata. Si la vacante es de alguno de estos, detener el análisis y reportarlo — no generar HANDOFF.

> **Aéropostale NO es un Hard Block** — confirmado con el operador 2026-08-07. El historial en Aéropostale sigue siendo válido como contenido del Canon (C04) y las vacantes de esa empresa no se excluyen por este criterio.

También excluir roles store-level sin alcance estratégico o multi-tienda.

> Referencia confirmada: `MANUAL:DATA-MANAGEMENT` (Manual, §10 — "Hard Blocks" / "Soft Blocks"). **Hard Blocks** (L'Oréal todas las divisiones, Levi's/Dockers, El Palacio de Hierro, roles store-level sin gestión estratégica) se filtran en el origen, antes de existir como registro en Notion, y no son recuperables bajo ninguna circunstancia. **Soft Blocks** (URL rota, JD parcial, Score insuficiente) sí son recuperables vía Dashboard — pero ese mecanismo no aplica a esta skill; CV-A solo verifica Hard Blocks.

## Output — Estructura del HANDOFF (8 campos)

Referencia: `KERNEL:CV-PIPELINE-001`. El JSON del HANDOFF tiene 8 campos obligatorios (7 canónicos del Kernel + `observaciones`, reincorporado 2026-08-09 tras discrepancia detectada entre `SP:CV-GOLDEN-RULES-REF`/Scope Lock — que exigen el campo — y el schema de 7 campos que lo había perdido en una revisión anterior; sin registro de handoffs previos que confirmen su formato exacto, se define aquí como texto libre, opcional, y nunca bloqueante):

```json
{
  "empresa": "",
  "rol": "",
  "JD_keywords_top6": ["", "", "", "", "", ""],
  "fit_gaps": ["", ""],
  "tono_marca": "",
  "idioma": "",
  "positioning_rationale": "",
  "observaciones": ""
}
```

- `observaciones` (opcional, texto libre): discrepancias detectadas durante el análisis que no encajan en `fit_gaps` (ej. inconsistencia entre JD y Gate_Decision previa, dato dudoso en la fuente, nota de dedup). **Nunca** contiene verbos de decisión sobre el gate. Si no hay nada que reportar, el campo va vacío — no se elimina (Null-Fill Rule, `CANON:OUTPUT-CONTRACT-001`).

Un HANDOFF incompleto en cualquiera de los 7 campos originales no avanza a CV-B. `observaciones` es la única excepción — puede ir vacío sin bloquear el avance.

## Output — Archivo completo

```markdown
# HANDOFF CV-A — [Nombre de la empresa / vacante]

## Metadata
- URL vacante:
- Fecha de análisis:
- Idioma detectado (ES/EN):
- Positioning Mode seleccionado: [N1-N4, o "EMPATE — requiere decisión humana"]

## Positioning Mode — Justificación
[Keywords del JD mapeadas a la ancla canónica del modo elegido]

## Gap Analysis
### Matches directos
- [Requisito JD] → [ID canónico: KPIxx / CFxx / CANON:EXPERIENCE-xxx]

### Matches parciales
- [Requisito JD] → [qué tan cerca, qué falta]

### Gaps (fit_gaps)
- [Requisito JD sin soporte en Canon]

## Validación de exclusiones
- Empleador: [nombre] — [PASA / BLOQUEADO]
- Alcance del rol: [estratégico/multi-tienda — PASA, o store-level sin alcance — BLOQUEADO]

## Observaciones
[Discrepancias detectadas, o "Ninguna"]

## Próximo paso
[Listo para CV-B, o BLOQUEADO — razón]
```

## Output — Entrega

Genera el archivo con `create_file`, guárdalo en `/mnt/user-data/outputs/`, y preséntalo con `present_files`. No agregues explicación adicional en el chat fuera del propio archivo — el mensaje de chat que acompaña la entrega debe ser mínimo (una línea, sin resumen del contenido).
