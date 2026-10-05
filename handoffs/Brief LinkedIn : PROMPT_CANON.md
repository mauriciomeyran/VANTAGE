# Brief de Documentación Técnica
## LinkedIn · Layer 1 · PROMPT_CANON

**Fecha:** 05 octubre 2026  
**Estado:** Cerrado / Publicado  
**Commit de referencia:** `a67d5fa3c745e83ec25aee9d2bdea241107ca15d`

### 1. Propósito

Documentar la arquitectura técnica y el estado de canonicalización de la fuente LinkedIn dentro de Layer 1 de VANTAGE, incluyendo su implementación de búsqueda, integración operativa, contrato de prompt y mecanismos de autoridad, provenance y verificación.

La documentación distingue entre cuatro capas de autoridad:

- **PROMPT LIBRARY:** autoridad sobre el texto del prompt.
- **PROMPT_CANON:** autoridad sobre estado, identidad y provenance del contrato.
- **Git:** autoridad sobre la implementación versionada.
- **verify_versions.py:** autoridad de verificación de consistencia, no de promoción.

Hermes ejecuta y verifica. No posee autoridad autónoma para promover un contrato de `CANDIDATE` a `CANONICAL`.

### 2. `linkedin_search.py`

`linkedin_search.py` forma parte de la implementación de LinkedIn utilizada por Layer 1 para ejecutar la búsqueda y producir resultados estructurados.

Su responsabilidad se mantiene en la capa de adquisición y procesamiento inicial de resultados. No contiene la autoridad estratégica de selección ni sustituye el Gate de VANTAGE.

El tratamiento de identidad de empleador quedó separado en un matcher versionado y reproducible, evitando que la lógica de bloqueo dependa de substring matching arbitrario.

La implementación versionada incorpora:

- identidad exacta y variantes autorizadas;
- diferenciación entre empleador y retail channel / store / client / distribution partner;
- estado `AMBIGUOUS` cuando la identidad no puede resolverse de forma segura;
- bloqueo únicamente cuando la identidad del empleador coincide con una entidad bloqueada;
- ausencia de inferencia de `BLOCKED` a partir de coincidencias ambiguas;
- comportamiento determinista;
- pruebas versionadas y reproducibles.

El caso `Dockers Heroes` quedó explícitamente separado de `Dockers`: no produce `BLOCKED` por sí mismo y no establece `employer_match=True`.

### 3. Integración Layer 1

El flujo canónico de Layer 1 para Active Recon es:

`Human signal → LinkedIn / Aggregators / Career Sites / Gemini → JSON estructurado → FEED → feed_processor.py → Notion (Class A) → vantage-pipeline`

LinkedIn constituye una de las fuentes de adquisición. Layer 1 es responsable de maximizar cobertura y trazabilidad, no de realizar la priorización estratégica final.

La integración respeta los campos Class A y utiliza el wrapper de fuente para emitir la estructura esperada. `feed_processor.py` normaliza el formato y no redefine los criterios de elegibilidad.

Layer 1 no delega en LinkedIn la lógica del Gate. La decisión posterior continúa siendo responsabilidad de VANTAGE.

### 4. Contrato y prompt canónico

El prompt de LinkedIn fue tratado originalmente dentro del conjunto de artefactos `PromptA-v2.0+linkedin` y sus contratos asociados.

Los artefactos canónicos relacionados fueron:

- `PromptA-v2.0+linkedin.md`
- `LINKEDIN-RULES-002.md`
- `LINKEDIN-QUERYSET-002.md`
- `LINKEDIN-OUTPUT-SCHEMA-002.md`
- `PHASE3-TEST-002.md`
- `PHASE3C-MATCHER-CLOSURE-SPEC.md`

La canonicalización posterior no convirtió `PROMPT_CANON` en un repositorio del cuerpo del prompt. Su función es registrar el estado y provenance del contrato.

La autoridad sobre el texto del prompt continúa en PROMPT LIBRARY.

### 5. PROMPT_CANON

Se incorporó `PROMPT_CANON` como autoridad de estado y provenance de contratos de prompt.

**Notion page:** `3f0938be-fc42-813a-9215-c6a1a716c3b7`  
**Data source:** `Prompt Contract Registry`  
**Data source ID:** `9d63b44d-c744-4a17-9bba-94222782b95b`

El registro utiliza estados cerrados:

`CANONICAL | CANDIDATE | BLOCKED | SUPERSEDED`

La validación independiente implementada en `verify_versions.py` comprueba:

- existencia de la autoridad;
- lectura del data source;
- integridad de las filas `CANONICAL`;
- correspondencia con los artefactos;
- enum cerrado de estado;
- SHA válido;
- resolución del SHA en Git;
- binding real SHA → Implementation Path;
- existencia del path;
- ausencia de duplicados activos por Prompt ID.

No existe fallback de autoridad si `PROMPT_CANON` está ausente. Su ausencia constituye un fallo de infraestructura.

### 6. Registry y documentación canónica

`document_registry` fue ampliado de 12 a 13 claves para registrar `PROMPT_CANON`.

La clave apunta a:

`3f0938be-fc42-813a-9215-c6a1a716c3b7`

También se incorporó `PROMPT_CANON` a `DOC_KEYS` de `verify_versions.py`.

En `KERNEL:NAM-ID-CONTRACT §12.1` se actualizó la enumeración de prefijos autorizados para incluir `PROMPT_CANON`.

No se modificó la maquinaria de census.

Específicamente:

- `generate_census.py` no consume `PROMPT_CANON`;
- `DOCUMENTS` no fue modificado;
- `VALID_PREFIXES` del census no fue modificado;
- `DOC_PRIORITY` no fue modificado.

Esta separación evita convertir un registro de estado en un documento `PREFIX:KEY` indexable por census.

### 7. Validación

La implementación de PROMPT_CANON quedó validada mediante:

- `23/23` tests específicos de `test_prompt_canon.py`;
- `282/282` tests de Layer 1;
- prueba de binding real SHA → path;
- validación desde clean clone;
- verificación de ausencia de fallback;
- verificación de autoridad obligatoria;
- aislamiento del census.

La implementación anterior de matcher quedó cubierta por la validación de Phase 3C, incluyendo `27/27` pruebas específicas y la suite completa correspondiente a ese cierre.

### 8. Publicación

Commit:

`a67d5fa3c745e83ec25aee9d2bdea241107ca15d`

Mensaje:

`feat(Layer_1): PROMPT_CANON — autoridad de estado y provenance de contratos de prompt`

El commit fue publicado mediante fast-forward a `origin/main`.

Estado posterior:

`HEAD == origin/main`

SHA local y remoto:

`a67d5fa3c745e83ec25aee9d2bdea241107ca15d`

Working tree: limpio.

### 9. Estado final

LinkedIn queda con:

- implementación versionada;
- matcher reproducible;
- contrato trazable;
- provenance verificable;
- autoridad PROMPT_CANON;
- binding real entre Git y artefacto;
- integración Layer 1 documentada;
- publicación en `origin/main`.

La evidencia histórica de Phase 3B permanece como antecedente de auditoría. Phase 3C resolvió la reproducibilidad futura sin afirmar reconstrucción del runtime histórico.

`PROMPT_CANON = CANONICAL`

`LinkedIn = CANONICAL`