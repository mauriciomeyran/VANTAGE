---
name: vantage-cv-a
description: Fase 1 del pipeline de CV de VANTAGE (KERNEL:CV-PIPELINE-001) — procesamiento inicial y validación de fit estratégico de una vacante contra el Career Canon de Mauricio Meyrán. Usar cuando el operador invoque el trigger "CV-A [URL/JD]", pegue una URL de vacante o un Job Description crudo pidiendo análisis, o pida identificar el Positioning Mode (N1-N4) para una oportunidad específica. También activar si el operador pide "gap analysis" de una vacante contra su trayectoria, o pida preparar el primer paso del pipeline de CV antes de construir el documento final (CV-B). No usar para construir el CV en sí (eso es vantage-cv-b) ni para auditoría de PDF final (eso es vantage-qa).
---

# VANTAGE — Skill CV-A (Análisis y Alineación)

ID Canónico: `KERNEL:CV-PIPELINE-001` · Trigger: `CV-A [URL/JD]`

## Responsabilidad

Primera fase del pipeline de CV. Procesa una vacante (URL + Job Description) y produce un HANDOFF estructurado que sirve de input exclusivo para `vantage-cv-b`. No construye el CV — solo analiza y decide.

## Invariante de Sesión — Sandbox-only

**Cero prosa en el chat.** Esta skill no conversa sobre el análisis en el cuerpo del mensaje. El único output permitido es un archivo `.md` descargable que contenga el HANDOFF completo. Cualquier explicación, aclaración o duda va dentro del propio archivo, no como texto de chat adicional.

Excepción: si falta el Career Canon o hay una ambigüedad bloqueante en el Positioning Mode (ver Regla de Desempate abajo), sí se puede preguntar al operador antes de generar el archivo — pero una vez resuelto, el resultado sigue siendo solo el archivo.

## Input requerido

- URL de la vacante
- Job Description crudo (texto completo, no resumen)

Si el operador solo da una URL sin JD pegado, usar `web_fetch` para obtener el JD real antes de proceder. No inferir contenido de JD a partir del título del puesto.

## Contrato Operativo — Pasos

### 1. Identificar Positioning Mode (N1–N4)

Referencia: `CANON:POSITIONING` (Career Canon, sección 11).

| Modo | Ancla canónica |
|---|---|
| N1 · Luxury Brand Execution | C01 (L'Oréal Luxe) · 3 marcas lujo · CAPEX/OPEX · NPI |
| N2 · Store Design & Flagship Execution | C02 (Bisonte/Adidas) · Adidas Brand Center · KPI07 · blueprints |
| N3 · Regional Brand Execution & Rollout | C03 (Levi's/Dockers) · 270+ POS · 6 países · KPI03–06 · CF05 |
| N4 · Commercial VM & Field Leadership | C04/C05 (Aéropostale/Palacio de Hierro) · +43% tráfico · +18% conversión · 21 reportes |

Mapea las keywords del JD contra las anclas de cada modo. El modo con más matches gana.

### 2. Regla de Desempate en JDs híbridos

Referencia: `CANON:POSITIONING-004`.

Cuando el JD activa criterios de dos o más modos simultáneamente, en orden de precedencia:

1. El modo con mayor número de keywords del JD mapeados a su ancla canónica.
2. En empate de keywords: el modo de mayor seniority estratégico (N2 > N1, N4 > N3 cuando el JD tiene presupuesto regional explícito).
3. En empate persistente: **no decidir unilateralmente.** Declarar el empate en `fit_gaps` del HANDOFF y escalar a decisión humana antes de proceder con CV-B.

El Positioning Mode seleccionado (o el empate declarado) se documenta explícitamente en el HANDOFF.

### 3. Gap Analysis vs. Career Canon

Compara los requisitos del JD contra el Career Canon (Experience Records, Skills Canon, KPIs, Canonical Facts). Para cada requisito relevante del JD:
- **Match directo:** referencia al ID canónico que lo respalda (ej. `KPI03`, `CF05`).
- **Match parcial:** nota qué tan cerca está y qué falta.
- **Gap:** requisito sin soporte en el Canon. Nunca inventar experiencia para cerrar un gap — el gap se documenta, no se rellena.

### 4. Validación de exclusiones

Antes de continuar, verificar que la vacante no provenga de un empleador con bloqueo total de recontratación: **L'Oréal, Levi's/Dockers, El Palacio de Hierro, Aéropostale**. Ninguno de los cuatro recontrata. Si la vacante es de alguno de estos, detener el análisis y reportarlo — no generar HANDOFF.

También excluir roles store-level sin alcance estratégico o multi-tienda.

> Referencia confirmada: `MANUAL:DATA-MANAGEMENT` (Manual, sección 10 — "Hard Blocks" / "Soft Blocks"), no `MANUAL:SOFT-HARD-BLOCKS` como citaba el brief original ni `MANUAL:HOW-IT-WORKS` (que solo resume el concepto y remite a esta sección como fuente completa). **Hard Blocks** (L'Oréal todas las divisiones, Levi's/Dockers, El Palacio de Hierro, roles store-level sin gestión estratégica) se filtran en el origen, antes de existir como registro en Notion, y no son recuperables bajo ninguna circunstancia. **Soft Blocks** (URL rota, JD parcial, Score insuficiente) sí son recuperables vía Dashboard — pero ese mecanismo no aplica a esta skill; CV-A solo verifica Hard Blocks.
>
> Nota: Aéropostale NO es un Hard Block — confirmado con el operador 2026-08-07. Cualquier referencia previa que lo incluyera (memoria operativa u otros briefs) era un error; el historial en Aéropostale sigue siendo válido como contenido del Canon (C04) y las vacantes de esa empresa no se excluyen por este criterio.

## Output — Estructura del HANDOFF

El archivo `.md` entregado debe incluir, como mínimo:

```markdown
# HANDOFF CV-A — [Nombre de la empresa / vacante]

## Metadata
- URL vacante:
- Fecha de análisis:
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

## Próximo paso
[Listo para CV-B, o BLOQUEADO — razón]
```

## Output — Entrega

Genera el archivo con `create_file`, guárdalo en `/mnt/user-data/outputs/`, y preséntalo con `present_files`. No agregues explicación adicional en el chat fuera del propio archivo — el mensaje de chat que acompaña la entrega debe ser mínimo (una línea, sin resumen del contenido).
