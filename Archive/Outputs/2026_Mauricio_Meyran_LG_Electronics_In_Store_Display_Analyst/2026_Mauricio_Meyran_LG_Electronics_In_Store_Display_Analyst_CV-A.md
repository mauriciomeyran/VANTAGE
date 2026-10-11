# HANDOFF CV-A — LG Electronics / In-Store Display Analyst

## Metadata
- URL vacante: https://mx.linkedin.com/jobs/view/4463634113
- Fecha de análisis: 2026-09-18
- Idioma detectado (ES/EN): ES
- Positioning Mode seleccionado: N2 · Store Design & Flagship Execution
- Nota de corrección: el scaffold de origen titulaba esta vacante "Liverpool" (y el Hard Block Check corrió contra ese nombre); el JD confirma que el empleador real es **LG Electronics** — confirmado con el operador en esta sesión.

## Positioning Mode — Justificación

Algoritmo de 4 pasos aplicado, con filtro de señal de alarma previo al conteo final.

**1. JD_keywords_top6:**
1. Ejecución de exhibiciones en punto de venta / Visual Merchandising a nivel nacional
2. Gestión end-to-end de proyectos de exhibición (planeación, logística, instalación, mantenimiento, retiro)
3. Coordinación de proveedores, cotizaciones y presupuestos (producción, transporte, instalación)
4. Supervisión de mantenimientos preventivos/correctivos y validación de ejecución en punto de venta
5. Administración de inventarios y distribución de materiales POP/POSM
6. Desarrollo/actualización de planogramas, playbooks y lineamientos de exhibición consistente a nivel nacional

**2–3. Mapeo, conteo y filtro de alarma por ancla:**

| Modo | Ancla | Matches (bruto) | Señal de alarma | Elegible |
|---|---|---|---|---|
| N1 | C01 L'Oréal Luxe · 3 marcas lujo · CAPEX/OPEX · NPI | 0 | Triggered — JD es retail masivo de electrónica de consumo, sin componente multi-marca de lujo | No |
| N2 | C02 Bisonte/Adidas · KPI07 · blueprints | 2 (keywords 2, 4 — gestión de proyecto de instalación end-to-end + mantenimientos/validación de ejecución) | No triggered — JD sí tiene obra física, instalación y mantenimiento, no es solo "diseño" conceptual | **Sí** |
| N3 | C03 Levi's/Dockers · 270+ POS · 6 países · KPI03–06 · CF05 | 4 (keywords 1, 3, 5, 6) | **Triggered** — JD es "a nivel nacional" (México), sin alcance multi-país explícito | No |
| N4 | C04/C05 · +43% tráfico · +18% conversión · 21 reportes | 0 | Triggered — JD no reporta KPIs de tráfico/conversión ni tamaño de equipo de campo | No |

**4. Resolución:** N3 tiene el conteo bruto más alto (4), pero queda descalificado por su propia señal de alarma (sin alcance multi-país). Entre las anclas que sí superan su propia alarma, solo N2 tiene matches (2) — único candidato elegible, sin empate. Se selecciona N2.

## Gap Analysis

### Matches directos
- Gestión de proyecto de instalación end-to-end (planeación, logística, instalación, mantenimiento) → `CANON:MAJOR-PROJECT-001` (P01 — Adidas Brand Center Madero), `CANON:EXPERIENCE-002` (C02 Bisonte Experiential)
- Mantenimientos preventivos/correctivos y validación de ejecución en punto de venta → `CANON:KPI-007` (KPI07 — Adidas Punch List Count, 17), `CANON:FACT-003` / `CANON:FACT-004` (Adidas Punch List Count / Severity)

### Matches parciales
- Coordinación de proveedores, cotizaciones y presupuestos, optimización de recursos → parcial vía `CANON:KPI-003` (KPI03 — Campaign Cost Reduction -74%, Levi's/Dockers) — disciplina de optimización de costos afín, pero en contexto de rollout regional de campaña, no de gestión directa de proveedores de instalación de exhibiciones.
- Administración de inventarios y distribución de materiales POP/POSM → parcial vía `CANON:KPI-005` (KPI05 — POP Coverage 100%, LATAM COVID-19) — cobertura de material documentada, pero no logística/distribución de inventario como proceso explícito.
- Desarrollo/actualización de planogramas y playbooks de exhibición nacional → parcial vía `CANON:KPI-006` (KPI06 — Rebranding Coverage 100%) — consistencia de ejecución de marca documentada, sin confirmar experiencia específica en construcción de planogramas como documento técnico.

### Gaps (fit_gaps)
- Excel y PowerPoint avanzados — no confirmado en el Canon (stack documentado: Notion, Figma, Adobe CC, Apple; sin nivel de Excel/PowerPoint documentado)
- Inglés intermedio comprobable — no confirmado en el Canon en esta sesión

## Validación de exclusiones
- Empleador: LG Electronics — PASA (Hard Block determinista sobre el nombre corregido; no coincide con L'Oréal, Levi's/Dockers, ni El Palacio de Hierro)
- Alcance del rol: ejecución de exhibiciones "a nivel nacional" en distintos canales de retail — no es store-level de una sola tienda — PASA

## Observaciones
- El JD pide 1–2 años de experiencia; el Canon documenta 10+ años (`CANON:KPI-008`). Esto es un desajuste de seniority hacia arriba (sobrecalificación), no un gap de experiencia — se documenta para que el operador lo pondere, sin recomendar descarte.
- Metodología aplicada por primera vez explícitamente en esta sesión: filtrar candidatos por su propia señal de alarma antes de rankear por conteo — evita repetir el patrón de las tres vacantes anteriores (Comercio Excelente, Viva, Aplazo) donde un modo ganaba por conteo bruto pese a estar en su propia zona de alarma.

## Próximo paso
- `cv_b_eligible`: **true** (Positioning Mode resuelto sin empate; sin señal de Status/Next_Action que indique Expirada, Archivada, Rechazada o Archivar)
- `block_reason`: `[]`
- Listo para CV-B.
