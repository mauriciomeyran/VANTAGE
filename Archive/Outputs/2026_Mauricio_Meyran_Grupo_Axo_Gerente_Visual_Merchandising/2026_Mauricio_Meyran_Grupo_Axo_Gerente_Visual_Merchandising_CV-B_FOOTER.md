# FOOTER DE METADATA — NO IMPORTAR A FIGMA (Canon 12.4: el footer va fuera del .md del plugin)

- Skill: vantage-cv-b v10.2.0 · Output Contract: CANON:OUTPUT-CONTRACT v1.1.0 (BASELINE 2026-09-19)
- Positioning Mode: N4 · Commercial VM & Field Leadership (HANDOFF CV-A Grupo Axo, 2026-09-21)
- Canon usado: CANON:EXPERIENCE-001..005, SKILLS, EDUCATION, CERTIFICATIONS, UF-002/003/004, POSITIONING-004/005
- Registry: copia embebida CANON:OUTPUT-CONTRACT-003 (68 IDs, secuencia exacta)

## Gates (ejecutados con regex/conteo sobre el texto final)
Gate 1 (Tags/Membership): PASS — 68/68 IDs en registry, formato exacto
Gate 2 (Integridad estructural): PASS — 68/68, únicos, secuencia idéntica al Skeleton, 0 nodos vacíos
Gate 3 (Idioma): PASS — 1 hit "in" en "Born in Roma" (nombre propio de campaña, excepción declarada, 2:27)
Gate 4 (Tiempo verbal): PASS — 1 hit "diseño" en 2:37 (sustantivo, falso positivo); C01–C05 todos en pretérito
Gate 5 (Elegibilidad etiquetas): PASS — 0/19 bullets con etiqueta (0%)
Gate 6 (Bold de métricas): PASS — 1 hit "3 años" en 10:198 (duración, no métrica de headcount/volumen; falso positivo)
Gate 7 (Formato estructural): PASS — sin espacio final en Rol/Grado; período con " | " inicial
Gate 8 (Pendientes justificados): N/A — 0 [PENDING DATA]
Gate 9 (Anti-cloning): PASS — 0 bullets duplicados; sin CV-B previo en esta sesión para cruce
Gate 10 (Code fences): PASS — 0 fences en el .md

NO ejecutado: verify_md.py (Canon 12.4) no está disponible en este sandbox — correrlo localmente antes de importar a Figma.

## Decisiones y discrepancias para el operador
1. Rol activo: L'Oréal cerró 03/2026 (UF01) → C01 en pretérito. El CV-A no lo marcó como activo.
2. C05: el Skeleton tiene 3 bullets para Asesor (1 hecho canónico) y 1 para Coordinador (4 hechos). Slot Integrity prohíbe mover slots: los 3 slots del Asesor se derivaron del único bullet canónico (coordinación / aperturas y rotaciones / estándares de casa matriz); los 4 hechos del Coordinador se sintetizaron en 10:198 en un bullet denso. Ambas decisiones son revisables.
3. Formación 10:161: "ENAP, UNAM" según tu preferencia de presentación (Canon 08.1 dice "Escuela Nacional de Artes Plásticas, UNAM").
4. Gaps del CV-A NO cubiertos por el CV (Anti-overselling): visa/pasaporte, herramientas de data/BI, inglés C1 (se usó "Profesional Corporativo" literal del Canon).
5. Skill vs Canon: el skill v10.2.0 pide footer dentro del .md; el Canon 12.4 lo prohíbe (rompe el plugin). Se siguió el Canon. Conviene alinear el skill.
6. 8:62 "LinkedIn" y 8:63 "Portafolio": labels literales; hipervínculos (UF05/UF06 ES) se aplican en Figma.
