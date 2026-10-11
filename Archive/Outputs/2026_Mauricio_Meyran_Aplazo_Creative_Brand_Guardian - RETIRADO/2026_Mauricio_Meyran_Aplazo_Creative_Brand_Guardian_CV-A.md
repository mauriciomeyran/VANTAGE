# HANDOFF CV-A — Aplazo / Creative & Brand Guardian

## Metadata
- URL vacante: https://mx.linkedin.com/jobs/view/4457007745
- Fecha de análisis: 2026-09-18
- Idioma detectado (ES/EN): EN
- Positioning Mode seleccionado: EMPATE — requiere decisión humana

## Positioning Mode — Justificación

Algoritmo de 4 pasos aplicado.

**1. JD_keywords_top6:**
1. Art direction / creative direction / brand design (dueño único de concepto y craft)
2. Ownership del design system y del brand book (stewardship, defensa y evolución)
3. Origination de conceptos de campaña y narrativa end-to-end
4. Dirección y corrección del trabajo creativo de otros (Content Specialists)
5. Herramientas de IA generativa para producción creativa (Midjourney, Runway)
6. Fluidez en cultura digital/social y juicio de tendencias

**2–3. Mapeo y conteo contra anclas canónicas:**

| Modo | Ancla | Matches |
|---|---|---|
| N1 | C01 L'Oréal Luxe · 3 marcas lujo · CAPEX/OPEX · NPI | 0 |
| N2 | C02 Bisonte/Adidas · KPI07 · blueprints | 0 |
| N3 | C03 Levi's/Dockers · 270+ POS · 6 países · KPI03–06 · CF05 | 1 (keyword 2 — paralelo temático con KPI06, Rebranding Coverage 100%) — **ver alarma abajo** |
| N4 | C04/C05 · +43% tráfico · +18% conversión · 21 reportes | 0 |

**4. Desempate / resolución:** Este caso no es un empate numérico entre dos modos (solo N3 tiene un match ≥1) — es un caso donde el único candidato con match queda anulado por su propia señal de alarma explícita: *"JD es de un solo mercado/tienda, sin alcance multi-país"*. El JD de Aplazo es un rol de marca única para una fintech mexicana, sin componente de rollout multi-país, multi-tienda ni red de puntos de venta física — exactamente la condición que la tabla de anclas marca como razón para NO usar N3.

Con el único candidato disqualificado por su propia alarma, no queda ningún modo con match válido y no-alarmado. Siguiendo el mismo principio de la Regla de Desempate (punto 3 — "no decidir unilateralmente" ante ambigüedad persistente), se declara esta condición equivalente a EMPATE y se escala a decisión humana, en vez de forzar la selección de N3 por conteo bruto ignorando su propia señal de alarma.

**Nota de patrón de sesión (transparencia, no verbo de decisión):** esta es la tercera vacante consecutiva en la sesión (después de Comercio Excelente y Viva) donde el Positioning Mode se resuelve por defecto hacia N3 por un match único y débil, en discipinas ajenas a Visual Merchandising. Aquí el patrón se vuelve explícito y se detiene en vez de repetirse una tercera vez sin chequeo — la señal de alarma de N3 es la razón formal para no continuar con el mismo default.

## Gap Analysis

### Matches directos
- Formación académica requerida ("Bachelor's degree in Design, Visual Arts, Communication, or a related field") → `CANON:EDUCATION-001` (ED01 — Licenciatura en Artes Visuales, UNAM)

### Matches parciales
- Ownership de design system / brand book → parcial vía `CANON:KPI-006` (Rebranding Coverage 100%, Levi's/Dockers) — mismo principio de fondo (guardián de consistencia de marca), pero aplicado a ejecución física en punto de venta, no a sistemas de diseño digital/campañas de marca.
- Dirección y corrección del trabajo de otros → parcial: Canon documenta liderazgo de equipos operativos (coordinadoras, promotoría) en contexto de ejecución VM, no dirección creativa/de arte.
- Adobe Creative Suite (herramienta listada en el JD) → parcial: Canon lista Adobe CC como parte del stack general, sin especialización documentada en dirección de arte o producción de campañas.

### Gaps (fit_gaps)
- Art direction / creative direction como función y trayectoria primaria (agencia o in-house) — sin soporte
- Concepting y narrativa de campañas end-to-end, dueño único de la idea — sin soporte
- Herramientas de IA generativa para producción creativa (Midjourney, Runway) — sin soporte
- Trayectoria en fintech, retail digital, o consumer brands de ritmo rápido — sin soporte (trayectoria de Mau es retail físico tradicional/lujo)
- Inglés de negocios avanzado — no confirmado en el Canon de esta sesión (no se infiere)

## Validación de exclusiones
- Empleador: Aplazo — PASA (Hard Block determinista confirmado en el archivo de origen; no coincide con L'Oréal, Levi's/Dockers, ni El Palacio de Hierro)
- Alcance del rol: dueño único de marca a nivel compañía, no store-level — PASA

## Observaciones
- El Positioning Mode no se resolvió con un modo válido: el único match encontrado (N3) queda anulado por su propia señal de alarma (sin alcance multi-país/multi-tienda en el JD). Se declara EMPATE-equivalente y se escala a decisión humana, siguiendo el mismo principio que la Regla de Desempate aplica a empates numéricos genuinos.
- Patrón de sesión: tercera vacante consecutiva con discipina núcleo ajena a Visual Merchandising (Merchandising/Buying → Comercio Excelente; Producción Creativa/Diseño → Viva; Dirección Creativa/Marca → Aplazo). Se documenta como observación de sesión, no como recomendación de descarte — la decisión sobre el lote corresponde al operador.

## Próximo paso
- `cv_b_eligible`: **false** (Positioning_Mode = EMPATE, calculado determinísticamente conforme a la fórmula del HANDOFF)
- `block_reason`: `["Positioning Mode no resuelto — único candidato (N3) anulado por su propia señal de alarma; requiere decisión humana antes de avanzar a CV-B"]`
- BLOQUEADO para CV-B hasta que el operador resuelva el Positioning Mode manualmente (o confirme si procede forzar N3 pese a la alarma, o declare un modo fuera del set N1–N4 estándar).
