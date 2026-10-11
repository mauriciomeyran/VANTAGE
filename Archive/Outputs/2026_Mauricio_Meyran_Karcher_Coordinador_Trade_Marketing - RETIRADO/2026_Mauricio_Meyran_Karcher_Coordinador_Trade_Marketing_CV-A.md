# HANDOFF CV-A — Kärcher / Coordinador de Trade Marketing – Retail & Canal Tradicional

## Metadata
- URL vacante (Notion Tracker): https://app.notion.com/p/VISUAL-MERCHANDISER-ANALYST-3dc938befc42817aad74fc8392fd3dbe
- URL origen (userDefined, LinkedIn): https://www.linkedin.com/jobs/view/4461352413/
- Fecha de análisis: 2026-09-18
- Idioma detectado (ES/EN): ES
- Positioning Mode seleccionado: N4 · Commercial VM & Field Leadership
- Nota de identidad: el registro de Notion trae `Rol: "VISUAL MERCHANDISER ANALYST"` y `Holding/Marca: "LG Electronics" / "LG"`, ninguno de los cuales coincide con el contenido del JD (Coordinador de Trade Marketing, marca Kärcher). El operador confirmó en esta sesión que **el JD es el dato correcto** — este HANDOFF se genera bajo esa identidad (Kärcher), no bajo los campos de metadata del Tracker.

## Positioning Mode — Justificación

Algoritmo de 4 pasos aplicado, con filtro de señal de alarma previo al conteo final.

**1. JD_keywords_top6:**
1. Diseño/coordinación/despliegue de exhibiciones, islas, cabeceras y material POP en cadenas estratégicas (Sam's Club, Walmart, Liverpool, Coppel, Costco)
2. Liderazgo de fuerza de promotoría (25 promotores, multi-plaza: CDMX, Monterrey, Guadalajara), KPIs de asistencia y desempeño
3. Ejecución de campañas de Retail Media y publicidad física/digital para maximizar conversión y ROI
4. Cumplimiento riguroso de guías de marca en punto de venta
5. Diseño de programas de incentivos y concursos de ventas para impulsar productividad de promotoría
6. Planeación y ejecución end-to-end de presencia en exposiciones/eventos comerciales (Expo Ferretera, B2B/B2C)

**2–3. Mapeo, conteo y filtro de alarma por ancla:**

| Modo | Ancla | Matches (bruto) | Señal de alarma | Elegible |
|---|---|---|---|---|
| N1 | C01 L'Oréal Luxe · 3 marcas lujo · CAPEX/OPEX · NPI | 0 | Triggered — retail masivo de herramientas/Home & Garden, sin componente multi-marca de lujo | No |
| N2 | C02 Bisonte/Adidas · KPI07 · blueprints | 0–1 | No triggered, pero sin matches relevantes (exhibiciones POP multi-cadena ≠ construcción de flagship único) | Sí (0–1, no compite) |
| N3 | C03 Levi's/Dockers · 270+ POS · 6 países · KPI03–06 · CF05 | 2 (keywords 1, 4) | **Triggered** — JD es de un solo país (México), multi-plaza pero no multi-país | No |
| N4 | C04/C05 · +43% tráfico · +18% conversión · 21 reportes | 4 (keywords 2, 3, 5, 6) | No triggered — el JD reporta KPI comercial medible (conversión/ROI) Y involucra equipo de campo (25 promotores) explícitamente | **Sí (4)** |

**4. Resolución:** N4 gana con el conteo más alto entre las anclas elegibles (4), sin empate.

## Gap Analysis

### Matches directos
- Liderazgo de equipo de campo multi-plaza (25 promotores, CDMX/MTY/GDL) con KPIs de asistencia y desempeño → `CANON:EXPERIENCE-004` (C04 Aéropostale), `CANON:EXPERIENCE-005` (C05 Palacio de Hierro/ALDO), `CANON:FACT-006` (Aéropostale Team Size)
- Maximizar conversión en punto de venta → `CANON:KPI-002` (Conversión +18%, Aéropostale)
- Indicadores comerciales de piso de venta (tráfico) → `CANON:KPI-001` (Tráfico +43%, Aéropostale)

### Matches parciales
- Diseño/despliegue de exhibiciones, islas, cabeceras y material POP en múltiples cadenas retail → parcial vía `CANON:KPI-005` (POP Coverage 100%, LATAM COVID-19) y `CANON:EXPERIENCE-002` (C02 Bisonte/Adidas, ejecución física de proyectos) — la disciplina de ejecución física es la misma, pero el contexto de canal (marca-hacia-retailer terceros: Walmart, Sam's, Costco, Liverpool, Coppel) no está documentado en el Canon, que opera dentro de tiendas propias/de marca.
- Cumplimiento de guías de marca en punto de venta → parcial vía `CANON:KPI-006` (Rebranding Coverage 100%)
- Programas de incentivos/concursos de ventas para promotoría → parcial: Canon documenta liderazgo y desarrollo de equipos, sin evidencia específica de diseño de programas de incentivos comerciales.

### Gaps (fit_gaps)
- Trade Marketing / Shopper Marketing / Retail Media como disciplina y trayectoria formal — sin soporte (disciplina adyacente a VM, no idéntica)
- Gestión de agencias de promotoría como modelo operativo tercerizado — sin soporte (Canon documenta equipos con reporte directo, no vía agencias externas)
- Experiencia sectorial en FMCG / Bienes de Consumo Duradero / Electrodomésticos / Herramientas — sin soporte (trayectoria documentada es moda/lujo/indumentaria)
- Relación comercial B2B marca-hacia-retailer en Canal Moderno (Walmart, Sam's, Costco, Liverpool/Coppel) y Canal Tradicional (ferretero/mayorista) — sin soporte
- Logística de exposiciones comerciales B2B/B2C (ej. Expo Ferretera) — sin soporte
- Licenciatura en Marketing, Relaciones Comerciales, Administración, Ingeniería Industrial o Negocios Internacionales — el Canon documenta Lic. Artes Visuales (UNAM), disciplina distinta a la solicitada
- Inglés conversacional de negocios — no confirmado en el Canon en esta sesión

## Validación de exclusiones
- Empleador: Kärcher (identidad confirmada por el operador sobre el contenido del JD) — PASA (Hard Block determinista; no coincide con L'Oréal, Levi's/Dockers, ni El Palacio de Hierro)
- Alcance del rol: multi-plaza (CDMX, Monterrey, Guadalajara), liderazgo de equipo de 25 — estratégico/multi-tienda, no store-level — PASA

## Observaciones
- Discrepancia de origen documentada para el operador: los campos `Rol` (`VISUAL MERCHANDISER ANALYST`) y `Holding`/`Marca` (`LG Electronics` / `LG`) del registro Notion no coinciden con el JD (Kärcher, Coordinador de Trade Marketing). El operador confirmó que el JD es el dato correcto. Recomendación operativa (no ejecutada sin instrucción explícita, ver `SP:CONSISTENCY`): actualizar `Rol` y `Holding`/`Marca` en el registro Notion para que coincidan con el JD, evitando que este mismatch se propague a reportes o dashboards que consulten esos campos.
- Gap estructural relevante para decisión humana (no es recomendación de descarte): el JD es un rol de **Trade Marketing/Shopper Marketing B2B** hacia retailers terceros (Walmart, Sam's, Costco, Liverpool, Coppel) en sector FMCG/herramientas, mientras que el Canon documenta **Visual Merchandising** dentro de tiendas de marca propia en sector moda/lujo. El match N4 obtenido es real y fuerte en la dimensión de liderazgo de campo y KPIs comerciales, pero el eje de negocio (marca-hacia-retailer vs. marca-hacia-tienda-propia) y el sector (FMCG/herramientas vs. moda/lujo) son gaps estructurales que CV-B deberá manejar con la Regla 6 (Match Transferible Obligatorio) de forma extensa.

## Próximo paso
- `cv_b_eligible`: **true** (Positioning Mode resuelto sin empate; sin señal de Status/Next_Action que indique Expirada, Archivada, Rechazada o Archivar)
- `block_reason`: `[]`
- Listo para CV-B.
