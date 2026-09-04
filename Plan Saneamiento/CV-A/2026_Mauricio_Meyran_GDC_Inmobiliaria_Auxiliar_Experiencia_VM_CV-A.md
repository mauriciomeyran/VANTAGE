# HANDOFF CV-A — GDC Inmobiliaria / Auxiliar de Experiencia y Visual Merchandising

## Metadata
- URL vacante: https://mx.indeed.com/viewjob?jk=2772e8e2be137116
- Fecha de análisis: 2026-09-03
- Idioma detectado (ES/EN): ES
- Positioning Mode seleccionado: N2

## Positioning Mode — Justificación

JD_keywords_top6:
1. Estilismo de espacios muestra: mobiliario, decoración, textiles, props, staging
2. Coordinación con proveedores de home staging, mobiliario, florería, mantenimiento
3. Supervisión de calidad de materiales impresos y señalización (renders, maquetas, brochures, planos)
4. Diseño de protocolos de experiencia de visita por perfil de cliente
5. Mapeo y optimización del recorrido del cliente (customer journey)
6. Conocimiento de marcas de lujo, concept stores, hospitalidad alta gama, sector inmobiliario premium

Mapeo contra anclas de Positioning Modes (`CANON:POSITIONING`):
- N1 (lujo multi-marca, CAPEX/OPEX, NPI): 1/6 match débil (keyword 6, mención de marcas de lujo) — sin componente multi-marca ni NPI explícito.
- N2 (Store Design & Flagship Execution — fixtures, blueprints, coordinación con proveedores/obra): 3/6 matches (keywords 1, 2, 3 — diseño físico de espacio, coordinación de proveedores de montaje, supervisión de calidad de materiales/planos).
- N3 (Regional Brand Execution & Rollout — multi-país): 0 matches — el JD es de una sola ubicación (Hipódromo Condesa, CDMX).
- N4 (VM comercial y liderazgo de campo — KPIs tráfico/conversión): 1-2/6 matches parciales (keywords 4, 5 — protocolos de experiencia y customer journey), sin KPI comercial medible explícito.

N2 gana con 3/6 — no hay empate, no aplica Regla de Desempate.

## Gap Analysis

### Matches directos
- Diseño/estilismo de espacios físicos (mobiliario, decoración, staging) → `CANON:EXPERIENCE-002` (C02 Bisonte/Adidas Brand Center)
- Coordinación con proveedores para montaje/producción de espacio → `CANON:MAJOR-PROJECT-001` (P01 Adidas Brand Center Madero)
- Supervisión de calidad de materiales técnicos (renders, maquetas, planos, señalización) → `CANON:KPI-007` (Adidas Punch List Count)

### Matches parciales
- Conocimiento de marcas de lujo/concept stores → parcial vía `CANON:EXPERIENCE-001` (C01 L'Oréal Luxe), pero la vertical es distinta (beauty de lujo vs. inmobiliario premium/showrooms).
- Diseño de protocolos de experiencia de cliente y customer journey → parcial vía experiencia de liderazgo comercial en tienda (C04/C05), sin métricas de conversión aplicables a este contexto (showroom inmobiliario, no retail transaccional).

### Gaps (fit_gaps)
- Vertical inmobiliaria / home staging / showrooms de bienes raíces — sin experiencia documentada en el Canon en este sector específico.
- Requisito de manejo de Asana y Hubspot — sin mención en el Canon.
- Requisito de portafolio de diseño adjunto al CV — el Canon no documenta un portafolio de diseño formal (mismo gap detectado en handoffs previos de este batch).
- Nivel del puesto ("Auxiliar", asistente) — posible desalineación de seniority marcada frente al perfil de +10 años y roles de gerencia regional documentados en el Canon (`CANON:KPI-008`).

## Validación de exclusiones

- Empleador: GDC Inmobiliaria, S.A. de C.V. — **PASA** (no está en la lista de Hard Blocks: L'Oréal, Levi's/Dockers, El Palacio de Hierro).
- Alcance del rol: el JD describe una sola ubicación física ("Hipódromo Condesa - Cuauhtémoc, CDMX"), sin mención de red de showrooms ni alcance multi-ubicación — lectura textual apunta a **store-level sin alcance estratégico explícito** (criterio de exclusión de `MANUAL:DATA-MANAGEMENT §10`). El registro trae `VM_Scope: Alto` (Notion), lo que genera la misma discrepancia detectada en handoffs previos de este batch (ver Observaciones) — no se resuelve unilateralmente aquí.

## Observaciones

1. **Discrepancia de alcance:** `VM_Scope: Alto` en Notion vs. lectura textual del JD que describe una sola ubicación física sin red de showrooms — mismo patrón de discrepancia ya señalado en el handoff de Zara Home (2026-09-03). No se cuestiona la `Gate_Decision` (`CREATE`); se documenta para decisión del operador.
2. **Flag de integridad de registro:** el campo `Notas` de este registro en Notion indica `[ARCHIVO] Razón: URL Gate rechazada (AGREGADOR_STATUS_401)` y `Validación de URL falló: AGREGADOR_STATUS_401` — esto sugiere que el pipeline ya marcó este registro para archivado por fallo de validación de URL del agregador (Indeed). Este es un dato de estado del pipeline, no una decisión de esta skill, pero se reporta explícitamente por ser relevante para decidir si vale la pena continuar con CV-B sobre una vacante potencialmente inválida/caída.
3. **Desalineación de seniority:** el título "Auxiliar" y el rango salarial indicado ($18,000–$20,000 MXN/mes) son consistentes con un rol de nivel de entrada/asistente, notablemente por debajo del nivel de gerencia regional que refleja el Canon.

## Próximo paso

**REVISIÓN HUMANA REQUERIDA** antes de CV-B — por (a) discrepancia de alcance (`VM_Scope: Alto` vs. lectura de ubicación única) y (b) flag de integridad de registro (`AGREGADOR_STATUS_401` / posible archivado pendiente). No se genera bloqueo unilateral; se solicita confirmación del operador sobre si procede continuar con esta vacante antes de avanzar a CV-B.
