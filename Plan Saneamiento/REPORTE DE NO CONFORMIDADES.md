# FASE 1

## CV-A / CV-B vs. Career Canon y Output Contract

**Dictamen:** el lote no es confiable como output de producción. Hay incumplimientos de contrato, invenciones semánticas, contradicciones entre CV-A y CV-B, falsas declaraciones de verificación y avance indebido de registros bloqueados o pendientes de decisión humana. La causa raíz no es un error aislado: es que CV-A y CV-B permiten que el lenguaje persuasivo sustituya la trazabilidad factual. file:50 file:87

## Severidad y reglas

| Severidad | Definición | Acción obligatoria |
| --- | --- | --- |
| **S0 — Bloqueante** | El output no puede pasar a Figma, aplicación ni revisión editorial | Retener y reconstruir |
| **S1 — Crítica** | Afirma hechos, autoridad, herramientas o entregables no respaldados por el Canon | Eliminar o sustituir por hecho canónico |
| **S2 — Mayor** | CV-A permitió proceder pese a un gate no resuelto, contradicción o evidencia insuficiente | Corregir el Skill CV-A y reclasificar el output |
| **S3 — Menor** | Inconsistencia de idioma, metadata, terminología o estilo sin alterar sustancia | Normalizar en el rebuild |

La regla vigente permite el Match Transferible, pero prohíbe convertir un hecho disponible en una responsabilidad que el Canon no acredita o que contradice el JD; el Anti-overselling tiene prioridad. file:50

---

# Hallazgos S0 — Bloqueantes

## S0.1 — Sintaxis de tags no determinista

Se identifican tres serializaciones incompatibles dentro del lote:

```
###### figma_text_id
```

```
###### 2:4
```

```
###### 2:28|
```

El Skill indica que el formato debe copiarse literalmente del Golden Skeleton y que toda desviación es regresión. Además, el registry define el ID como `2:28`; el carácter `|` forma parte del nombre interno del nodo y no del ID Figma. file:50 file:88

**Impacto:** no existe garantía de que el parser Figma resuelva los nodos correctos ni de que se pueda inyectar contenido de forma idempotente.

**Archivos afectados confirmados:**

- H&M Junior Retail Designer: tag `2:28|`. file:55
- H&M Retail Designer: tag `2:28|`. file:56
- Eurokor: tag `2:28|`. file:83
- Servicios Andrei Moygo: tag `2:28|`. file:86
- Varios CV-B alternan entre placeholder literal `[figma_text_id]` e IDs reales. file:51 file:53

**Corrección de Skill CV-B:**

```
PRE-DELIVERY GATE — TAG_SCHEMA:
1. Extraer cada tag con regex.
2. Rechazar si no coincide exactamente con el patrón autorizado.
3. Extraer el ID y verificar membresía exacta en registry_seed.json.
4. Rechazar si existe un caracter adicional dentro del ID.
5. Rechazar si existe más de una convención de tag dentro del mismo archivo o batch.
6. Si falla: STATUS=BLOCKED_TAG_SCHEMA; no emitir archivo.
```

---

## S0.2 — Falsos “PASS” de verificación

Los footers afirman, por ejemplo, “68/68 tags matchean”, “sin discrepancias”, “PASS”, “todos los slots llenados” y “Anti-cloning Guard PASS”, mientras el propio contenido contiene tags inválidos, claims no canónicos y gates de CV-A no resueltos. file:54 file:55 file:59

**Impacto:** el footer deja de ser evidencia y se vuelve texto decorativo. Un sistema determinístico no puede aceptar autoafirmaciones sin evidencia de ejecución.

**Corrección de Skill CV-B:**

- Prohibir frases como `PASS`, `verificado`, `sin discrepancias` o `68/68` si no existe un bloque de evidencia generado por un validador.
- El footer debe registrar resultados estructurados:
    - `tag_schema_result`
    - `registry_membership_result`
    - `slot_count_result`
    - `canon_traceability_result`
    - `anti_overselling_result`
    - `batch_similarity_result`
- Si algún campo es `FAIL`, el output no puede usar el estado `PASS_FOR_FIGMA`.

---

## S0.3 — Avance a CV-B con gates de CV-A bloqueados

El CV-A de Walmart declara simultáneamente:

- Positioning Mode en empate.
- Mismatch de framework con Space Planning/Category Analytics.
- Estado terminal `Expirada / Archivar`.
- Instrucción explícita: “No avanza a CV-B sin resolución de ambos puntos”. file:67

Sin embargo, existe un CV-B de Walmart orientado a “Store Design & Space Planning Execution”. Esto es una violación directa del contrato de entrada de CV-B. file:65

**Impacto:** el sistema produce outputs para una vacante que su propio pipeline clasificó como no apta y archivada.

**Corrección de Skill CV-A:**

```
GATE PROPAGATION RULE:
Si Positioning_Mode = EMPATE
OR Status in {Expirada, Archivada, Rechazada}
OR Next_Action = Archivar
OR Gate_Decision != CREATE
THEN:
  handoff.cv_b_eligible = false
  handoff.block_reason = lista exhaustiva de gates
  CV-B debe rechazar el HANDOFF automáticamente.
```

**Corrección de Skill CV-B:**

```
INPUT ADMISSION GATE:
No iniciar generación si cv_b_eligible != true.
No permitir override inferido.
Solo aceptar override con:
- operator_override = true
- operator_override_reason
- override_timestamp
- override_scope
```

---

# Hallazgos S1 — Invención y overselling

## S1.1 — Autoría de paquetes arquitectónicos no acreditada

El Canon acredita:

- Implementación visual y técnica del Adidas Brand Center Madero.
- Supervisión de producción y logística de materiales de Store Design.
- Coordinación de proveedores especializados.
- Protección de la integridad del diseño arquitectónico y visual. file:87

El Canon **no acredita**:

- Autoría de paquetes arquitectónicos.
- Producción de construction documents.
- Revisión formal de planos o documentos de construcción.
- Diseño arquitectónico de origen.
- Gestión de obra.
- Validación de floor plans.
- Coordinación con consultants como relación contractual formal.

A pesar de ello, los CV-B de H&M incluyen expresiones como:

- “hands-on ownership of architectural drawings”.
- “construction documents”.
- “technical package”.
- “architectural package review”.
- “reviewing construction documents”.
- “validating floor plans”.
- “construction-document validation”.
- “architectural production”.
- “project timeline ownership on construction documentation”. file:55 file:56

**Clasificación:** S1 crítica. No es reencuadre transferible; es sustitución de la función real por una función arquitectónica no probada.

**Sustituciones permitidas:**

| Prohibido | Sustitución canónica |
| --- | --- |
| Architectural package ownership | Visual and technical implementation for a flagship-store opening |
| Reviewing construction documents | Coordinating visual and technical implementation under global Store Design standards |
| Validating floor plans | Aligning zoning and category layout with corporate visual standards |
| Architectural production | Production and logistics of Store Design materials |
| Construction-document validation | Quality control of Store Design materials, finishes and installation |
| Technical package through handover | Production, logistics and on-time opening delivery |

**Cambio obligatorio en CV-B:**

```
No convertir:
- coordinación
- implementación
- producción
- logística
- acabados
- integridad de diseño

en:
- diseño de origen
- arquitectura
- planos
- permisos
- documentación de construcción
- autoría técnica
- dirección de obra
```

---

## S1.2 — Permisos, accesos y calendarización inventados

El CV-B de GDC afirma:

> “Gestioné múltiples proveedores especializados — cadena de suministro, permisos, accesos y calendarización — asegurando la integridad del diseño arquitectónico y visual desde planos hasta entrega final.” file:54
> 

El Canon no documenta permisos, accesos, calendarización integral, trabajo “desde planos” ni gestión de obra. Documenta producción, logística, proveedores, acabados, mobiliario e implementación visual/técnica. file:87

**Clasificación:** S1 crítica.

**Corrección obligatoria:**

```
Eliminar: permisos, accesos, calendarización, desde planos, obra.
Conservar: coordinación de proveedores, producción y logística de materiales,
calidad de acabados, mobiliario, iluminación, props e implementación visual.
```

---

## S1.3 — “Showroom premium” y home staging presentados como experiencia

El CV-B de GDC utiliza:

- “showrooms premium”.
- “showroom staging”.
- “espacios de exhibición premium”.
- “equivalente a staging y estilismo de espacios de exhibición premium”.
- “protocolos de calidad visual aplicables a redes de 270+ puntos de venta”. file:54

El CV-A reconoce expresamente que el sector inmobiliario, home staging y showrooms de bienes raíces **no existen en el Canon** y que Asana, HubSpot y portafolio formal tampoco están respaldados. file:79

**Clasificación:** S1 crítica para “showroom premium” si se presenta como experiencia; S2 si se usa solo como orientación de vacancy-fit.

**Regla nueva:**

```
TRANSFERABILITY BOUNDARY:
Una equivalencia funcional puede explicar la relevancia de un hecho,
pero nunca puede renombrar la industria, el producto o el entorno real
de experiencia como si fuera literal.

Permitido:
“transferable to premium physical-space execution.”

Prohibido:
“experience in premium showrooms / home staging”
si el Canon no lo contiene de forma literal.
```

---

## S1.4 — “Skincare de lujo” para marcas de fragancias

El CV-B de Eurokor afirma experiencia en “fragancias/skincare de lujo” para Valentino, Giorgio Armani y Ralph Lauren. file:83

El Canon establece explícitamente `Valentino / Giorgio Armani / Ralph Lauren (fragancias)`. No hay claim canónico de skincare. file:87

**Clasificación:** S1 crítica.

**Corrección:** sustituir por “fragancias de lujo” o “luxury fragrance brands”. Nunca combinar fragancias con skincare salvo evidencia canónica nueva.

---

## S1.5 — “Planogramas digitales” no acreditados

El CV-B de Eurokor afirma:

> “implementación de planogramas digitales para field teams”. file:83
> 

El Canon acredita “manuales de Zoning & Mapping y herramientas digitales para field teams”, además de planogramas de categorías en Aéropostale. No acredita que los planogramas fueran digitales. file:87

**Clasificación:** S1 crítica.

**Sustitución permitida:**

```
“manuales de Zoning & Mapping y herramientas digitales para field teams”
```

No es válido fusionar dos hechos para crear un tercero: “planogramas digitales”.

---

## S1.6 — “Colorimetría” presentada como competencia factual

Varios CV-B incorporan colorimetría como si fuera una habilidad acreditada: Andrei Moygo, H&M Junior, Multicont y otros. file:55 file:86

El Career Canon no contiene una habilidad, certificación, proyecto o evidencia de colorimetría formal. Sí contiene visual storytelling, lineamientos visuales, zoning, planogramas, exhibición y campañas. file:87

**Clasificación:** S1 crítica si aparece como hard skill, competencia probada o keyword de experiencia.

**Regla nueva:**

```
SKILL ADMISSION RULE:
Una skill sólo puede aparecer como competencia declarada si:
1. existe literalmente en CANON:SKILLS; o
2. está respaldada por experiencia/certificación explícita con trazabilidad.

No se permite inferir una skill técnica desde afinidad estética o sectorial.
```

---

## S1.7 — “Supply chain end-to-end” y procurement ampliado

En los CV-B de H&M se declara:

- “Managed the Store Design supply chain end-to-end”.
- “fixtures, lighting and props procurement”.
- “vendor timelines”.
- “project handover”. file:55 file:56

El Canon acredita supervisión de producción y logística de materiales, coordinación de proveedores y calidad de acabados/mobiliario. No declara procurement de extremo a extremo, administración integral de supply chain ni ownership de handover. file:87

**Clasificación:** S1 crítica.

**Límite obligatorio:**

```
“production and logistics coordination”
no puede escalarse a:
“end-to-end supply-chain ownership”
sin evidencia de sourcing, compras, inventario, transporte, recepción,
control de proveedores y entrega final bajo responsabilidad propia.
```

---

## S1.8 — Resultados no atribuibles convertidos en capacidad causal

El Canon dice que se contribuyó directamente a +43% de tráfico y +18% de conversión bajo supervisión estratégica. file:87

Algunos CV-B intensifican el claim hacia formulaciones de causalidad plena, como “estrategia comercial de piso que llevó a” esos resultados o una atribución directa y exclusiva al zoning y a acciones específicas. file:58

**Clasificación:** S1 crítica cuando se elimina el matiz de contribución.

**Regla nueva:**

```
KPI ATTRIBUTION RULE:
Si el Canon usa “contribuí directamente”, el CV-B debe preservar
contribución, no convertirla en causalidad exclusiva.

Permitido:
“Contributed directly to...”
“Supported a +43% increase...”

Prohibido:
“Delivered +43%...”
“Drove +43%...”
“Led to +43%...”
salvo que el Canon lo afirme.
```

---

# Hallazgos S2 — Fallas de CV-A

## S2.1 — CV-A etiqueta como match directo lo que luego reconoce como gap

El CV-A de H&M Junior declara como “Matches directos”:

- “Architectural drawings / construction documents for stores”.
- “Commercial space planning”. file:78

Pero, en sus propios matches parciales y gaps, reconoce que el Canon no acredita producción de planos arquitectónicos técnicos, Revit ni autoría formal de paquetes y documentos de construcción. file:78

**Clasificación:** S2 mayor. El CV-A convierte un match transferible parcial en match directo, habilitando el overselling de CV-B.

**Corrección CV-A:**

```
MATCH CLASSIFICATION RULE:
Un match es DIRECTO sólo si el Canon afirma la misma capacidad funcional
y el mismo nivel de responsabilidad.

Si:
- el sector cambia,
- el entregable cambia,
- la herramienta cambia,
- el nivel de ownership cambia,
- o el Canon sólo respalda coordinación,

entonces el match debe ser PARCIAL o TRANSFERIBLE, nunca DIRECTO.
```

---

## S2.2 — CV-A permite avanzar con “revisión humana requerida”

Zara Home y GDC cierran con “REVISIÓN HUMANA REQUERIDA antes de CV-B”. file:68 file:79

Pese a ello, ambos tienen CV-B generados. file:54 file:66

**Clasificación:** S2 mayor.

**Falla de diseño:** “REVISIÓN HUMANA REQUERIDA” es texto narrativo; no es una variable de control que CV-B consuma.

**Corrección CV-A:**

```
{
  "cv_b_eligible": false,
  "admission_status": "HUMAN_REVIEW_REQUIRED",
  "blocking_conditions": [
    "scope_conflict",
    "listing_integrity_failure"
  ]
}
```

**Corrección CV-B:**

```
Aceptar sólo:
admission_status = READY_FOR_CV_B
o
admission_status = OPERATOR_OVERRIDE_APPROVED.
```

---

## S2.3 — Inconsistencia del Positioning Mode Eurokor

El CV-A de Eurokor declara N2 como modo seleccionado, pero su propio conteo concluye que N3 gana 3 contra 2 y recomienda N3, sujeto a confirmación. file:82

El CV-B se emite como N3 con supuesto “confirmado por operador”. file:83

**Clasificación:** S2 mayor.

**Falla:** no existe evidencia adjunta del override del operador. El CV-B no puede transformar una recomendación pendiente en una decisión confirmada.

**Corrección:**

```
POSITIONING RESOLUTION CONTRACT:
Si modo precargado != modo recomendado:
  status = POSITIONING_CONFLICT
  cv_b_eligible = false

Sólo se puede continuar si existe:
  operator_selected_mode
  operator_resolution_reference
  timestamp
```

---

## S2.4 — CV-A diluye hard blocks mediante lenguaje narrativo

El CV-A de Walmart es claro en la condición terminal, pero el sistema produjo CV-B de todos modos. file:67 file:65

El problema no es solo CV-B: CV-A no entrega un control de admisión inequívoco y computable. Usa frases como “BLOQUEADO”, “próximo paso” y “requiere decisión humana”, pero no una señal operacional única.

**Corrección:** CV-A debe producir un bloque final obligatorio, no editable y legible por máquina:

```
{
  "handoff_schema_version": "1.0",
  "cv_b_admission": "BLOCKED",
  "positioning_mode": null,
  "operator_override_required": true,
  "blocked_reasons": [
    "POSITIONING_TIE",
    "ROLE_DISCIPLINE_MISMATCH",
    "TERMINAL_RECORD_STATUS"
  ]
}
```

---

## S2.5 — “Scope Lock” usado como excusa para avanzar

Varios CV-A señalan conflictos entre el texto de la vacante y `VM_Scope=Alto` de Notion, pero dicen que no reevaluarán la decisión anterior por Scope Lock. file:68 file:75 file:76 file:79

**Problema:** Scope Lock impide modificar fields de tracker; no debe impedir bloquear la generación de un CV-B si existe una contradicción material no resuelta.

**Regla nueva:**

```
SCOPE LOCK LIMIT:
Scope Lock prohíbe modificar el Tracker.
No prohíbe:
- declarar incertidumbre,
- detener CV-B,
- requerir override,
- registrar contradicción como blocking condition.
```

---

# Hallazgos S3 — Consistencia y calidad

## S3.1 — Mezcla no controlada de idiomas

En outputs con JD en español aparecen:

- profile en inglés;
- skills en español;
- experiencia en inglés;
- títulos de sección en español;
- footer bilingüe.

El Skill permite adaptar contenido, pero no define una política determinística de idioma por JD ni de slots bilingües. file:50 file:51 file:56

**Corrección:**

```
LANGUAGE POLICY:
- JD ES -> CV-B ES completo, salvo nombres propios/herramientas.
- JD EN -> CV-B EN completo, salvo nombres oficiales de grado/institución.
- Bilingüe -> requiere flag explícito en HANDOFF y razón.
- Ningún slot puede cambiar de idioma por conveniencia estilística.
```

---

## S3.2 — Versiones contradictorias

Los archivos declaran diferentes versiones de Output Contract y Career Canon; algunos footers nombran `v10.1.0`, otros `v1.0`, `v9.21.41` u otras combinaciones. file:51 file:59 file:65

**Corrección:**

```
VERSION PINNING:
CV-A debe emitir:
- canon_version
- output_contract_version
- registry_sha
- skill_version

CV-B debe copiar estas cuatro variables sin reinterpretarlas.
Si el runtime detecta divergencia: BLOCKED_VERSION_DRIFT.
```

---

## S3.3 — Referencias a rutas inexistentes

Se usó en documentos la ruta:

```
04-Vantage_CV/Figma Sync/registry_seed.json
```

El repositorio actual contiene el archivo en:

```
Figma Sync/registry_seed.json
```

La ruta incorrecta aparece en la documentación del Skill adjunto y deriva en metadata inconsistente. file:50 file:88

**Corrección:**

- Eliminar rutas hardcodeadas de CV-A y CV-B.
- Resolver siempre la ubicación desde configuración o desde el SHA del registry.
- Exigir que el footer incluya `registry_sha`, no solo una ruta narrativa.

---

# Matriz de no conformidades por archivo

| CV-B | Hallazgos principales | Estado |
| --- | --- | --- |
| Beyond | Idioma EN pese a JD ES, tags placeholder, claims de redacción no trazables de manera granular | `REBUILD_REQUIRED` |
| Confidencial Nacional | Posible falta de separación entre Canon y expansión narrativa; revisar output tag schema | `REBUILD_REQUIRED` |
| Confidencial Gerente | Redacción de “proyectos visuales de principio a fin” y “dirección” más amplia que el Canon en algunos slots | `REVIEW_AND_REBUILD` |
| GDC | Permisos, accesos, calendarización, desde planos, home staging/showroom presentados como experiencia | `BLOCKED_S1` |
| H&M Junior | Autoría de paquetes arquitectónicos, documentos, planos, contractors, handover; tag `2:28|` | `BLOCKED_S0_S1` |
| H&M Retail Designer | Construction documents, floor plans, architectural production, supply chain end-to-end; tag `2:28|` | `BLOCKED_S0_S1` |
| IKEA | Gate de scope store-level pendiente; revisar claims de auditoría/formación | `BLOCKED_GATE` |
| Juguetron | Gate de sobrecalificación sin override; cuidado con liderazgo para rol operativo | `OPERATOR_OVERRIDE_REQUIRED` |
| Intimissimi | La propia metadata admite elección de ángulo sin instrucción explícita; gate de seniority no formalizado | `REVIEW_REQUIRED` |
| Inditex | Scope conflict no resuelto; no debía pasar a CV-B sin override | `BLOCKED_GATE` |
| Multicont VM | Riesgo de liderazgo jerárquico y claims de negociación/inventario sin soporte literal | `REVIEW_AND_REBUILD` |
| SARELLY | Riesgo de “audit framework” y “fixture development from concept” como roles formales | `REBUILD_REQUIRED` |
| Tendam | Gate de nivel táctico/seniority sin decisión explícita | `OPERATOR_OVERRIDE_REQUIRED` |
| Multicont Supervisor | Principalmente QA estructural y trazabilidad de términos; es candidato prioritario a rebuild | `REBUILD_REQUIRED` |
| Walmart | Empate + estado terminal + mismatch disciplinar; CV-B no admisible | `ARCHIVE_DO_NOT_REBUILD` |
| Zara Home | Conflicto scope store-level no resuelto | `BLOCKED_GATE` |
| Eurokor | Conflicto N2/N3 sin override probado, skincare inventado, planogramas digitales, tag `2:28|` | `BLOCKED_S0_S1_S2` |
| Servicios Andrei Moygo | Tag `2:28|`, “coordinación de obra” y colorimetría no acreditada | `BLOCKED_S0_S1` |

La evidencia de Canon respalda VM, ejecución técnica, producción/logística de materiales, proveedores, estandarización regional, capacitación, KPIs y aperturas; no respalda arquitectura autoral, Revit, documentos de construcción, permisos, home staging, skincare o planogramas digitales. file:87

---

# Cambios obligatorios en CV-A

## Contrato de salida CV-A

Añadir al final de cada HANDOFF un único bloque JSON obligatorio:

```
{
  "handoff_schema_version": "1.0",
  "vacancy_id": "string",
  "positioning_mode": "N1 | N2 | N3 | N4 | null",
  "positioning_status": "RESOLVED | TIE | CONFLICT | OPERATOR_OVERRIDE",
  "cv_b_admission": "READY_FOR_CV_B | HUMAN_REVIEW_REQUIRED | BLOCKED | ARCHIVE",
  "canon_version": "string",
  "registry_sha": "string",
  "jd_language": "ES | EN",
  "jd_keywords_top6": ["string"],
  "direct_matches": [
    {
      "jd_requirement": "string",
      "canon_ids": ["string"],
      "evidence_type": "DIRECT"
    }
  ],
  "partial_matches": [
    {
      "jd_requirement": "string",
      "canon_ids": ["string"],
      "limitation": "string",
      "evidence_type": "PARTIAL"
    }
  ],
  "forbidden_claims": ["string"],
  "fit_gaps": ["string"],
  "blocking_conditions": ["string"],
  "operator_override_required": false
}
```

## Taxonomía obligatoria de evidencia

| Tipo | Uso permitido en CV-B |
| --- | --- |
| `DIRECT` | Puede afirmarse como experiencia propia |
| `TRANSFERABLE` | Puede usarse con redacción de equivalencia, sin cambiar industria, herramienta, ownership o entregable |
| `PARTIAL` | Puede aparecer en perfil o skills con limitación explícita; no como claim pleno |
| `GAP` | No debe reencuadrarse como competencia |
| `FORBIDDEN` | Debe ser bloqueado por el validador |

## Lista prohibida de inferencias

CV-A debe construir por vacante un arreglo `forbidden_claims` que CV-B no pueda ignorar. Ejemplo H&M:

```
[
  "Revit proficiency",
  "architectural package authorship",
  "construction-document production",
  "floor-plan validation",
  "architectural drawings ownership",
  "construction management",
  "formal architecture degree"
]
```

---

# Cambios obligatorios en CV-B

## Motor de trazabilidad factual

Cada párrafo de CV-B debe incluir metadatos internos, retirados antes de la entrega final:

```
{
  "slot_id": "2:35",
  "claim_text": "Led the visual and technical implementation...",
  "canon_ids": ["CANON:EXPERIENCE-002", "CANON:KPI-007"],
  "claim_type": "DIRECT",
  "allowed_terms": [
    "visual implementation",
    "technical implementation",
    "production",
    "logistics",
    "vendors",
    "finishes",
    "furniture",
    "on-time delivery"
  ],
  "forbidden_terms_checked": [
    "architectural package",
    "construction documents",
    "Revit",
    "permits"
  ],
  "result": "PASS"
}
```

## Gate de semántica

```
SEMANTIC CLAIM GATE:
Para cada oración:
1. Identificar sujeto, verbo, objeto, ámbito y resultado.
2. Localizar evidencia exacta en Canon.
3. Comparar el nivel de ownership:
   - support
   - coordinate
   - manage
   - lead
   - own
   - author
4. Rechazar si el CV eleva el nivel de ownership.
5. Rechazar si cambia herramienta, industria, producto o entregable.
6. Rechazar si transforma KPI de contribución en causalidad exclusiva.
```

## Diccionario de verbos controlados

| Evidencia del Canon | Verbos permitidos | Verbos restringidos |
| --- | --- | --- |
| Coordinó proveedores | Coordiné, gestioné coordinación, supervisé calidad | Dirigí obra, contraté consultores, gestioné permisos |
| Implementación visual/técnica | Implementé, lideré implementación, ejecuté | Diseñé arquitectura, autoré planos, desarrollé paquetes técnicos |
| Producción y logística | Supervisé producción y logística, coordiné materiales | Gestioné supply chain end-to-end, procurement integral |
| Integridad de diseño | Protegí, aseguré, salvaguardé | Validé planos, aprobé diseño arquitectónico |
| Contribución KPI | Contribuí, apoyé, participé directamente | Generé, entregué, provoqué, impulsé de manera exclusiva |
| AutoCAD/SketchUp Essentials | Formación/certificación, familiaridad documentada | Dominio experto, AutoCAD Architecture, Revit, CAD proficiency |

---

# Controles de no recurrencia

## Tests mínimos automatizables

| Test | Falla que previene |
| --- | --- |
| `test_tag_format_exact` | Tags como `2:28|` o formatos mezclados |
| `test_registry_membership` | IDs inexistentes, alterados o inventados |
| `test_slot_count_and_order` | Omisión, fusión o reordenamiento de slots |
| `test_handoff_admission` | CV-B generado con gates pendientes o estado terminal |
| `test_positioning_resolution` | Empates y conflictos convertidos en decisiones implícitas |
| `test_forbidden_claims` | Revit, planos, arquitectura, skincare, permisos, etc. |
| `test_canon_term_traceability` | Claims sin referencia factual |
| `test_ownership_escalation` | “Coordiné” convertido en “autoré” o “dirigí” |
| `test_kpi_attribution` | “Contribuí” convertido en “entregué” |
| `test_language_consistency` | Mezcla accidental ES/EN |
| `test_footer_evidence` | PASS declarados sin resultado verificable |
| `test_batch_similarity` | Cloning verbal entre CV-B del mismo modo |

## Política de fallo

```
Cualquier S0 o S1:
- No generar .md final.
- No permitir Figma Sync.
- No permitir aplicación.
- Emitir sólo un reporte de bloqueo.

Cualquier S2:
- Exigir corrección de CV-A u override documentado.
- CV-B no puede inferir autorización.

Cualquier S3:
- Corregir durante rebuild.
- No cerrar PASS hasta normalizar.
```

---

# Prioridad de implementación

1. **Implementar gate de admisión CV-A → CV-B**: bloquea Walmart, Zara Home, IKEA, Inditex y GDC sin intervención humana documentada. file:67 file:68 file:76 file:79
2. **Implementar validación rígida de tags contra `registry_seed.json`**: elimina tags inválidos y falsos PASS. file:88
3. **Implementar diccionario de claims prohibidos y elevación de ownership**: bloquea arquitectura, documentos de construcción, permisos, skincare y planogramas digitales no acreditados. file:87
4. **Reclasificar matches CV-A como Direct / Transferable / Partial / Gap / Forbidden**: impide que los gaps técnicos se conviertan en narrativa comercial. file:78
5. **Generar footer desde resultados de validación, no desde texto libre**: elimina certificaciones falsas de “PASS”. file:54
6. **Ejecutar rebuild unitario, no batch indiscriminado**: una vacante, un HANDOFF admitido, un CV-B validado, una liberación. file:50

# FASE 2

## Plan de remediación CV-B

Objetivo: convertir el batch actual en outputs **estructuralmente válidos, trazables contra CV-A/Canon y seguros frente a overselling** antes de cualquier sync con Figma o aplicación.

La prioridad no es “mejorar redacción”; es restaurar integridad del pipeline. Ahora mismo hay tres capas de problema: **gates ignorados**, **serialización inconsistente** y **claims fuera del Canon**. El Skill exige Positioning Mode resuelto, integridad estricta de slots/IDs y Anti-overselling por encima del reencuadre transferible. file:11

## Fase 0 — Congelamiento

| ID | Acción | Owner | Prioridad | Criterio de cierre |
| --- | --- | --- | --- | --- |
| R0.1 | Marcar los 16 CV-B como `HOLD — NOT FOR FIGMA SYNC` | Operador | P0 | Ningún CV-B se inyecta, exporta o usa para aplicar hasta pasar QA |
| R0.2 | Preservar los adjuntos como baseline inmutable | Operador | P0 | Copia/versionado de los 16 outputs actuales |
| R0.3 | Separar los CV-B por estado de entrada: `READY`, `OPERATOR_OVERRIDE`, `BLOCKED`, `REVIEW_NEEDED` | AI + Operador | P0 | Cada CV-B tiene estado y justificación explícita |

Los CV-A de Walmart, Zara Home y GDC documentan bloqueos o revisión humana previa; no pueden tratarse como inputs “listos” sin una decisión posterior del operador. file:28 file:29 file:40

## Fase 1 — Resolver gates

| Grupo | CV-B afectados | Acción requerida | Estado propuesto |
| --- | --- | --- | --- |
| Gate bloqueado | Walmart | Mantener fuera del lote: CV-A declara empate de Positioning Mode, mismatch disciplinar y estado terminal `Expirada/Archivar` | `ARCHIVE / DO NOT REBUILD` |
| Revisión de scope | Zara Home, IKEA, Inditex, GDC | Confirmar si el `VM_Scope: Alto` tiene evidencia externa al JD visible que justifique la excepción store-level | `OPERATOR_DECISION_REQUIRED` |
| Integridad de vacante | GDC | Resolver el flag `AGREGADOR_STATUS_401` antes de invertir en reescritura | `VERIFY LISTING` |
| Seniority extremo | H&M Junior, Juguetron, Multicont VM, Tendam | Confirmar intención estratégica: ¿aplicar pese a sobrecalificación/compensación? | `OPERATOR_OVERRIDE_REQUIRED` |
| Posicionamiento resuelto | Beyond, SARELLY, Multicont Supervisor, Intimissimi, Confidencial Nacional, Confidencial Gerente, H&M Retail Designer | Pueden entrar a remediación técnica, con control de claims | `REBUILD_CANDIDATE` |

El CV-A de H&M Junior reconoce explícitamente que el puesto es junior y que el Canon no acredita Revit ni autoría formal de paquetes arquitectónicos; por eso la versión actual no puede presentarlos como hechos consolidados. file:39

### Action items

- **R1.1 — Decisión Walmart:** archivar definitivamente el CV-B y excluirlo del QA de entrega.
- **R1.2 — Decisión store-level:** aprobar excepción o excluir Zara Home, IKEA, Inditex y GDC.
- **R1.3 — Verificar GDC:** confirmar que la vacante sigue activa desde una URL primaria o archivar.
- **R1.4 — Decisión de seniority:** definir si H&M Junior, Juguetron, Multicont VM y Tendam son aplicaciones tácticas conscientes o ruido de pipeline.
- **R1.5 — Registrar overrides:** cada excepción debe quedar escrita en el HANDOFF o metadata; no solo implícita en el CV-B.

## Fase 2 — Corregir contrato Figma

El `registry_seed.json` adjunto contiene 68 nodos en Page 1 y confirma que el ID de contenido es `2:28`; el carácter `|` pertenece al nombre del nodo interno, no al identificador Figma. file:49

| ID | Acción | Impacto | Criterio de cierre |
| --- | --- | --- | --- |
| R2.1 | Normalizar todos los tags al formato `###### figma_text_id` | P0 | Cero tags con `N:N` o `[figma_text_id]`literal |
| R2.2 | Corregir `2:28|` a `2:28` en los CV-B afectados | P0 | Regex exacta pasa en los 16 archivos seleccionados |
| R2.3 | Prohibir placeholders como `[figma_text_id]` | P0 | Todo tag referencia un ID real del registry |
| R2.4 | Comparar IDs presentes contra los 68 nodos del registry | P0 | Sin IDs inventados, faltantes ni duplicados |
| R2.5 | Verificar conteo de slots por experiencia | P0 | C01×4, C02×3, C03×5, C04×3, C05 según skeleton vigente |
| R2.6 | Unificar orden narrativo | P1 | Header → Profile → Skills → C01→C05 → Educación → Certificaciones |
| R2.7 | Eliminar wrappers ```markdown de los archivos de salida | P1 | Markdown serializable limpio, sin fences externos | |  |  |
| R2.8 | Estandarizar metadata del footer | P1 | Ruta vigente `Figma Sync/registry_seed.json`, versión y referencia coherentes |

### CV-B con riesgo de tag

- **H&M Junior Retail Designer**: `###### 2:28|`; inválido contra el contrato del Skill. file:16
- **H&M Retail Designer**: mismo patrón. file:17
- **Eurokor**: mismo patrón. file:44
- **Servicios Andrei Moygo**: mismo patrón. file:47

Además, existe inconsistencia de formato: algunos outputs usan tags literales `[figma_text_id]`, otros colocan IDs como texto de enlace (`2:4`). El Skill vigente exige el primer formato exactamente, por lo que debe elegirse una sola serialización y validarse contra el parser real antes de reconstruir todo el batch. file:11

## Fase 3 — Remediar claims

La regla operativa: **reencuadrar, sí; inventar ownership, no**. El Canon acredita implementación visual/técnica, coordinación de proveedores, logística de materiales, integridad de diseño y resultados de aperturas; no acredita de forma literal autoría de planos, paquetes arquitectónicos, permisos, Revit ni dirección de obra. file:48

| Claim riesgoso actual | Estado | Sustitución segura |
| --- | --- | --- |
| “Architectural package ownership” | No respaldado | “Visual and technical implementation for flagship-store opening” |
| “Reviewing construction documents” | No respaldado | “Coordinating visual and technical execution against global Store Design standards” |
| “Validating floor plans” | No respaldado de forma literal | “Aligning zoning and category layout with corporate planograms” |
| “Architectural production” | No respaldado | “Production and logistics of Store Design materials” |
| “Permits, accesses and scheduling” | No respaldado | Eliminar salvo evidencia canónica nueva |
| “Construction documents / documentation ownership” | No respaldado | “Project coordination, production follow-up and on-time handover” |
| “Skincare de lujo” para Valentino/Armani/Ralph Lauren | Incorrecto | “Luxury fragrances” |
| “Colorimetría” como habilidad comprobada | No documentado literalmente | “Visual storytelling, zoning and product presentation” |
| “Supply chain end-to-end” | Más amplio que el Canon | “Coordinated production and logistics of Store Design materials” |
| “Showroom staging” | Transferible, no directo | Usar solo como framing de perfil, no como experiencia literal |

### Action items

- **R3.1 — H&M Retail Designer:** rehacer Profile, Skills y C02/C03 para remover “architectural package ownership”, “construction-document review”, “floor-plan validation” y cualquier claim de autoría arquitectónica.
- **R3.2 — H&M Junior:** aplicar la misma limpieza y, además, evitar que el perfil compita como senior end-to-end con un JD explícitamente junior.
- **R3.3 — GDC:** eliminar `permisos, accesos y calendarización`, “desde planos” y “showroom premium” como experiencia establecida; conservar coordinación de producción, proveedores, acabados e implementación visual.
- **R3.4 — Eurokor:** cambiar “fragancias/skincare de lujo” por “fragancias de lujo”; eliminar “planogramas digitales” si no está expresamente en el Canon.
- **R3.5 — Andrei Moygo:** eliminar “coordinación de obra” si no hay soporte adicional; conservar aperturas, ejecución visual/técnica, proveedores y montaje.
- **R3.6 — Batch N4:** retirar liderazgo jerárquico de bullets donde el JD sea individual contributor; usar formación, estandarización y soporte de campo sin reclamar autoridad incompatible.

## Fase 4 — Rebuild por prioridad

No rehagas todo el multiverso a la vez. El Skill CV-B especifica procesamiento de un HANDOFF por invocación; el batch debe reconstruirse como unidades independientes para conservar trazabilidad y evitar clones. file:11

### Ola A — Alto fit, sin gate pendiente

| Orden | Vacante | Modo | Trabajo principal |
| --- | --- | --- | --- |
| 1 | Confidencial — Gerente Nacional VM | N3 | Revalidar inglés como gap; mantener estrategia nacional, 6 países, 270+ POS, presupuesto y equipo |
| 2 | SARELLY — Global Retail Experience & VM Manager | N3 | Reencuadrar audits/fixtures sin convertirlos en “framework formal” o desarrollo industrial |
| 3 | Multicont — Supervisor VM CDMX | N4 | Mantener liderazgo, wholesale, rutas y KPIs; validar formato de tags |
| 4 | Beyond — Gerente Marketing/VM/PDV | N2 por override | Mantener aperturas/expansión; no ocultar gaps de assortment y resurtido |
| 5 | Intimissimi — VM Coordinator | N4 | Bajar densidad de seniority donde el JD pide coordinación, conservar trabajo nacional de campo |

Los HANDOFF de SARELLY, Multicont Supervisor, Beyond e Intimissimi tienen Positioning Mode explícito y declaran que pueden avanzar a CV-B. file:31 file:30 file:45 file:35

### Ola B — Válidos con trade-off consciente

| Orden | Vacante | Condición |
| --- | --- | --- |
| 6 | H&M Retail Designer | Sólo tras limpieza de claims arquitectónicos |
| 7 | Tendam | Sólo si aceptas seniority y banda salarial táctica |
| 8 | Multicont VM | Sólo si aceptas rol individual y compensación baja |
| 9 | Juguetron | Sólo con override explícito por sobrecalificación |
| 10 | H&M Junior | Sólo como pivote de carrera deliberado, no como CV “normal” |

### Ola C — No reconstruir sin decisión

| Vacante | Motivo |
| --- | --- |
| Walmart | Bloqueo de CV-A, mismatch disciplinar y estado terminal |
| Zara Home | Scope store-level versus `VM_Scope: Alto` sin resolver |
| IKEA | Mismo conflicto de scope |
| Inditex | Mismo conflicto de scope |
| GDC | Scope conflict + integridad URL + puesto auxiliar |

## Fase 5 — QA determinístico

| Check | Regla | Resultado esperado |
| --- | --- | --- |
| Input gate | CV-A listo, modo resuelto, exclusiones PASA u override firmado | PASS |
| Registry | IDs = registry vigente | PASS |
| Tag syntax | Una sola sintaxis aprobada por parser | PASS |
| Slot integrity | Sin fusionar/eliminar slots | PASS |
| Canon fidelity | Cada hecho es literal o reencuadre válido | PASS |
| Anti-overselling | Sin autoría técnica, herramientas o responsabilidades no documentadas | PASS |
| JD alignment | Énfasis responde a `JD_keywords_top6` y `fit_gaps` | PASS |
| Language | Idioma coherente con JD; sin mezcla accidental ES/EN | PASS |
| Anti-cloning | No hay bloques idénticos dentro del mismo Positioning Mode | PASS |
| Footer | Versión, modo, Canon, registry, excepciones y `[PENDING DATA]` verificables | PASS |

## Definition of Done

Un CV-B queda liberado sólo cuando cumple simultáneamente:

- Su CV-A está en `READY` o tiene override documentado.
- Cada tag existe en el `registry_seed.json`.
- El formato coincide con la serialización aceptada por el plugin.
- No contiene claims que excedan `Career-Canon.md`.
- Su narrativa responde al JD específico, no a una plantilla genérica N2/N3/N4.
- El footer no declara checks que el archivo no cumple.
- Recibe un estado final: `PASS_FOR_FIGMA`, `HOLD`, `ARCHIVE` o `OPERATOR_OVERRIDE`.

El Career Canon respalda con claridad la ejecución visual/técnica del Adidas Brand Center, coordinación de proveedores, estrategia regional de 6 países/270+ POS, -74% de costos, -33% de tiempo de floorset, equipo de 21 reportes y +43% de tráfico/+18% de conversión; esos son los átomos permitidos para reconstruir el batch. file:48