# CHANGELOG UPDATE
## LinkedIn · Canonicalización, Auditabilidad y PROMPT_CANON

**Fecha:** 05 octubre 2026  
**Tipo:** Architecture / Canonicalization / Layer 1  
**Estado:** COMPLETED  
**Commit final:** `a67d5fa3c745e83ec25aee9d2bdea241107ca15d`

### Summary

Se completa el ciclo técnico de canonicalización de LinkedIn en VANTAGE, desde la validación de adquisición y matcher hasta el cierre de auditabilidad de Phase 3C y la incorporación de `PROMPT_CANON` como autoridad obligatoria de estado y provenance.

### LinkedIn Phase 3B

Se ejecutó la validación de LinkedIn sobre el conjunto canónico de queries.

Resultados documentados:

- 9 queries canónicas ejecutadas.
- 533 cards recolectadas.
- 297 job IDs únicos.
- `coverage_state=PARTIAL` bajo las restricciones guest/session.
- 6/6 páginas golden de detalle validadas.
- Sin IDs, URLs o detalles fabricados.
- Determinismo observado.

Se identificó y documentó la distinción entre empleador y retail channel/client/distribution partner.

### R08

Se construyó y validó el harness aislado de clasificación de errores y estados de detalle.

Resultado final:

`17/17 PASS`

La evidencia R08 permanece correctamente delimitada como validación de lógica aislada. No se eleva a prueba de comportamiento runtime real de LinkedIn.

### Phase 3B Auditability Gap

Se determinó que los cambios históricos del matcher ejecutados en Hermes no disponían de evidencia reproducible del estado BEFORE.

Conclusión:

`BLOCKED BY AUDITABILITY / EVIDENCE GAP, NOT BY PROVEN RULE VIOLATION.`

No se reconstruyó artificialmente el estado histórico.

### Phase 3C

Se implementó un matcher versionado y reproducible para eliminar la dependencia de modificaciones efímeras del runtime.

Se incorporaron:

- reglas explícitas de identidad;
- exclusión de retail channel/client/distribution partner;
- estados de identidad;
- matriz M01–M10;
- regresiones;
- determinismo;
- control de cambios;
- evidencia reproducible desde clean clone;
- límites explícitos de R08.

Resultado:

`27/27` pruebas específicas PASS.

Suite completa asociada al cierre:

`259/259` PASS.

Se mantuvieron intactos los cuatro artefactos canónicos originales mediante verificación MD5.

### Correcciones de validación

Se corrigió el tratamiento de variantes geográficas de `L'Oréal Mexico S.A. de C.V.` para producir `BLOCKED` de acuerdo con la identidad canónica.

Se corrigió además una expectativa de test sobre `ORÉAL`, preservando la regla canónica que distingue `L'Oréal` de una entidad diferente.

Se corrigió el criterio de promoción de `Dockers Heroes`: no se exige `NOT_BLOCKED`; la propiedad relevante es que no produzca `BLOCKED` por inferencia de identidad. El resultado válido es `AMBIGUOUS` con `employer_match=False`.

### PROMPT_CANON

Se incorporó `PROMPT_CANON` como autoridad formal de estado y provenance de contratos de prompt.

Cambios:

- nuevo registro de autoridad en Notion;
- incorporación de la clave `PROMPT_CANON` a `document_registry`;
- incorporación a `DOC_KEYS`;
- incorporación a la enumeración de prefijos autorizados de `KERNEL:NAM-ID-CONTRACT §12.1`;
- implementación de `verify_prompt_canon()`;
- validaciones V1–V7′;
- binding real SHA → Implementation Path;
- ausencia de fallback;
- separación del census.

Se registraron los artefactos LinkedIn en la autoridad correspondiente.

### Validación PROMPT_CANON

Resultado:

`23/23` tests específicos PASS.

Resultado de Layer 1:

`282/282` tests PASS.

La prueba I12 confirmó que el binding depende de un commit real y no de un mock.

### Authority Model

Queda formalizada la separación:

- **PROMPT LIBRARY:** prompt text SSOT.
- **PROMPT_CANON:** contract state/provenance SSOT.
- **Git:** implementation/version SSOT.
- **verify_versions.py:** consistency verifier.
- **Hermes:** executor/verifier.
- **Operator:** autoridad de promoción `CANDIDATE → CANONICAL`.

### Publication

Commit final:

`a67d5fa3c745e83ec25aee9d2bdea241107ca15d`

Publicado mediante fast-forward a:

`origin/main`

Post-push:

`HEAD == origin/main`

Working tree:

`clean`

### Scope

Este update cubre exclusivamente el ciclo de desarrollo y canonicalización de LinkedIn.

Career Sites queda fuera de este cambio y permanece como candidato independiente de canonicalización futura, sin modificación como parte de esta entrega.

### Version Bump

**Propuesta de incremento:** `PATCH`

Motivo: el cambio formaliza infraestructura de provenance, verificación y documentación canónica sin introducir un cambio incompatible en la API funcional de Layer 1.

**Versión anterior:** `[VERSIÓN ACTUAL DEL CHANGELOG]`  
**Nueva versión:** `[PATCH +1]`

> La sustitución de estos dos valores debe hacerse contra la versión efectiva del archivo Changelog, no mediante una versión inferida.