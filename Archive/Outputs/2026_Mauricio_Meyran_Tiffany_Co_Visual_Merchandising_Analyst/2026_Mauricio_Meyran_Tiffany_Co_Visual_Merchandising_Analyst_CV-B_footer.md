# FOOTER CV-B — Tiffany & Co. / Visual Merchandising Analyst

> Archivo separado a propósito: `CANON:OUTPUT-CONTRACT-004` v1.1.0 prohíbe el footer dentro del `.md` de Figma.

## Metadata
- Skill: `vantage-cv-b` v10.2.0
- Output Contract: `CANON:OUTPUT-CONTRACT-001` a `-005`, Tag Registry v1.1.0 (BASELINE 2026-09-19)
- HANDOFF de origen: CV-A Tiffany & Co., 2026-09-18
- Positioning Mode: **N1 · Luxury Brand Execution** (`CANON:POSITIONING-001`), resuelto sin empate (5 vs 2)
- Idioma: EN (CV íntegramente en inglés, incluidos tagline, títulos de sección, roles y skills)
- Referencia al Canon: `CANON:EXPERIENCE-001` a `-005` (bloques EN), `CANON:PROFILE-002`, `CANON:SKILLS` (columna EN), `CANON:CAREER-TIMELINE` (títulos de rol EN), `CANON:MAJOR-PROJECT-001/002`, `CANON:FACT-005/006/007/008`, `CANON:EDUCATION`, `CANON:CERTIFICATIONS`, `CANON:UF-001/002/004`

## Reporte de gates (script sobre el archivo final; Gate 3 con lista de palabras-función en español, por ser EN el idioma objetivo)
```text
Gate 1 (Tags/Membership): PASS — 68 tags, 0 fuera de registry, 0 malformados
Gate 2 (Integridad estructural): PASS — 68/68 vs Golden Skeleton, secuencia idéntica
Gate 3 (Idioma): PASS — excepciones declaradas: "Escuela Nacional de Artes Plásticas", "Facultad de Artes y Diseño" y "EL PALACIO DE HIERRO (ALDO)" (nombres de institución/empresa)
Gate 4 (Tiempo verbal): PASS — 0 verbos en presente; los 19 bullets en pasado simple (C01 termina 03/2026 por UF01). Enmascarados como falsos positivos: "Store Design" y "design integrity" (sustantivos) y "to ensure" (infinitivo)
Gate 5 (Elegibilidad etiquetas): PASS — 1/19 bullets con etiqueta (5%), 3:2
Gate 6 (Bold de métricas): PASS — 0 cifras sin bold
Gate 7 (Formato estructural): PASS
Gate 8 (Pendientes justificados): N/A — 0 ocurrencias de [PENDING DATA]
Gate 9 (Cross-check/Anti-cloning): N/A — sin CV-B previo de N1 en la sesión. Los CV-B previos de la sesión (LG y Tendam) están en español, así que no hay coincidencia literal posible
Gate 10 (Code fences): PASS — este footer tiene 1 bloque emparejado; el .md del CV tiene 0
```

## Decisiones y desviaciones
1. **Nombre del rol (`observaciones` del HANDOFF):** el HANDOFF usa "CVM Specialist" como rol, mientras la URL y el nombre del archivo CV-A dicen "Visual Merchandising Analyst (Maternity Leave)". El título no aparece en el contenido del CV, solo en el nombre del archivo. Usé `Visual_Merchandising_Analyst` (título de la URL y del archivo CV-A). Si prefieres `CVM_Specialist`, solo hay que renombrar.
2. **Anclaje N1 (`CANON:POSITIONING-005`):** el perfil (2:9, 3:13, 2:10) se apoya en C01: 3 marcas de lujo, presupuesto CAPEX/OPEX nacional, despliegue NPI 2025 y proveedores. C02 (apertura del Adidas Brand Center Madero, 17 observaciones) entra como respaldo explícito, alineado a la keyword de new store openings. No usé como evidencia principal los KPI de C04 (+43% / +18%); solo aparecen en su propio registro (2:50).
3. **C01 (4 slots para 5 hechos):** presupuesto y proveedores se fusionaron en 2:26. NPI y colaboración con Marketing/Trade Marketing quedaron en bullets separados (2:27, 2:28), para que la keyword de coordinación con stakeholders tenga su propio slot.
4. **Títulos de rol en EN:** tomados de `CANON:CAREER-TIMELINE`. Para el rol de C05 (2014–2017) y el de C05 (2012–2014) se usaron "VM & Marketing Coordinator" y "VM Advisor". Títulos de grado y diplomado traducidos: `Bachelor's Degree in Visual Arts` y `Diploma in Museums and Exhibitions` (el Canon solo los tiene en español; nombres de institución sin traducir).
5. **C05 en el skeleton:** Coordinador 2014–2017 en el primer rol (3 bullets) y Asesor 2012–2014 en el segundo (1 bullet), en orden inverso-cronológico.
6. **Gaps sin soporte en el Canon (no afirmados):**
   - Excel, Word y PowerPoint (el Stack Técnico lista Keynote).
   - Procurement e invoice management como proceso propio.
   - Sourcing de props, mobiliario decorativo o florales.
   - Coordinación con "Global CVM" como estructura: solo se documenta la colaboración con Marketing/Trade Marketing.
   - P03 (AeroFest, `CANON:MAJOR-PROJECT-003`) queda fuera: no hay renderings ni presupuesto documentados en ese registro.
7. **Anti-overselling:** ningún verbo sube el ownership del Canon. `Led` y `Managed` aparecen solo donde el Canon los usa; los presentes de C01 pasaron a pasado simple.
8. **Contacto y etiquetas:** 8:63 lleva ` | Portfolio` (equivalente EN de `Portafolio`); el hipervínculo se aplica en Figma. Skills con "and", no "&" (`Operations and Finance`, `Leadership and Training`).
9. **Registry:** copia embebida en `CANON:OUTPUT-CONTRACT-003` (BASELINE 2026-09-19). `verify_md.py` no está disponible en este entorno; conviene correrlo localmente antes de importar a Figma.
