# HANDOFF CV-A — Zara Home / Visual Merchandiser CDMX

## Metadata
- URL vacante: https://www.inditexpeople.com/mx/es/joinus/offers/MXAGTT5915
- Fecha de análisis: 2026-09-03
- Idioma detectado (ES/EN): ES
- Positioning Mode seleccionado: N4

## Positioning Mode — Justificación

JD_keywords_top6:
1. Ejecución de estrategia comercial ("Sigue y ejecuta todas las estrategias comerciales marcadas por la campaña")
2. Matching producto-espacio ("responsabiliza de hacer el mejor matching entre espacio de tienda y producto")
3. Estándares de atención al cliente ("Lidera los estándares de atención al cliente en su tienda")
4. Coordinación de equipo ("Comunicación y feedback continuo con su supervisor y todos los equipos de gestión en tienda")
5. Formación del equipo comercial ("debe ser una persona que asegure la formación del equipo comercial")
6. Reacción a ritmo comercial ("entiendes el ritmo comercial y reaccionas")

Mapeo contra anclas de Positioning Modes (`CANON:POSITIONING`):
- N1 (lujo multi-marca, CAPEX/OPEX, NPI): 0 matches — JD es retail de volumen (Zara Home/Inditex), sin componente multi-marca de lujo.
- N2 (diseño de tienda/flagship, blueprints): 0 matches — JD no menciona obra física ni coordinación con arquitectos.
- N3 (rollout regional multi-país, 270+ POS): 0 matches — JD es de una sola tienda ("en su tienda"), sin alcance multi-país.
- N4 (VM comercial y liderazgo de campo — C04/C05): 4/6 matches directos (ejecución comercial, atención al cliente, coordinación de equipo, formación de equipo).

N4 gana sin empate — no aplica Regla de Desempate.

## Gap Analysis

### Matches directos
- Coordinación/liderazgo de equipo en tienda → `CANON:EXPERIENCE-004` (C04 Aéropostale, liderazgo de campo) / `CANON:FACT-006` (tamaño de equipo Aéropostale)
- Ejecución de estándares de atención al cliente / impacto comercial medible → `CANON:KPI-001` (Traffic +43%), `CANON:KPI-002` (Conversion +18%, Aéropostale)
- Formación de equipo comercial → `CANON:SKILLS` (categoría Liderazgo & Training)

### Matches parciales
- "Matching entre espacio de tienda y producto" (ejecución visual de producto) → cercano a la disciplina VM general del Canon (C01–C05), pero el JD no especifica alcance multi-marca, CAPEX ni construcción física — match es de disciplina, no de escala.

### Gaps (fit_gaps)
- El JD no reporta ningún KPI comercial medible explícito (tráfico/conversión) como requisito — el match con N4 se basa en tipo de responsabilidad (liderazgo de campo, ejecución comercial), no en KPIs solicitados por la vacante.
- El JD no da señal de alcance multi-tienda o regional; está explícitamente acotado a "su tienda" (singular).

## Validación de exclusiones

- Empleador: Zara Home (Inditex) — **PASA** (no está en la lista de Hard Blocks: L'Oréal, Levi's/Dockers, El Palacio de Hierro).
- Alcance del rol: el texto del JD usa consistentemente singular de tienda ("en su tienda", sin mención de red, multi-tienda o alcance regional) — lectura textual apunta a **store-level sin alcance estratégico explícito**, criterio de exclusión de `MANUAL:DATA-MANAGEMENT §10`. Sin embargo, el registro en Notion trae `VM_Scope: Alto` (campo Class B, computado previamente). Esta discrepancia se declara en Observaciones — no se resuelve aquí unilateralmente.

## Observaciones

Discrepancia detectada: el campo `VM_Scope` de la vacante en Notion está marcado como **Alto**, mientras que la lectura textual directa del JD describe un rol acotado a una sola tienda, sin lenguaje de alcance multi-punto de venta o regional. No se cuestiona la `Gate_Decision` (`CREATE`) ni se interpreta este dato como instrucción de bloqueo — se documenta como discrepancia a resolver por el operador antes de avanzar, dado el criterio de exclusión de rol store-level definido en esta misma skill (sección 4).

## Próximo paso

**REVISIÓN HUMANA REQUERIDA** antes de CV-B — discrepancia entre `VM_Scope: Alto` (Notion) y alcance store-level explícito leído en el JD. No se genera un bloqueo unilateral; se solicita confirmación del operador sobre si el alcance real de la vacante justifica excepción al criterio de `MANUAL:DATA-MANAGEMENT §10` antes de proceder a CV-B.
