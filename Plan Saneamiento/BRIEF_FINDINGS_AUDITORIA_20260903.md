# BRIEF DE FINDINGS — Auditoría Plan Saneamiento (2026-09-03)

**Propósito de este documento:** insumo estructurado para que otra instancia (o skill de documentación transversal, ej. `vantage-cv-a`, `vantage-cv-b`, `vantage-qa`, o actualización directa de Kernel/Manual) genere las correcciones formales sin tener que re-derivar el análisis. Cada finding trae: ubicación exacta, evidencia verbatim, clasificación de severidad, y el documento/skill que debería recibir la corrección.

---

## FINDING 1 — Falso positivo sistemático en gate de tag Figma

**Severidad:** Alta (afecta al Skill, no a un archivo — impacto en todo output futuro)
**Documento a corregir:** `vantage-cv-b/SKILL.md`, sección "Verificación Pre-Entrega — Obligatoria", punto 1
**Skill relacionado:** `vantage-cv-b`

**Evidencia:** El tag `###### [2:28|](2:28)` fue señalado por el reporte de Perplexity como sintaxis rota. Verificación directa contra `registry_seed.json` (línea 151: `"id": "2:28"`) confirma que el ID es válido. El carácter `|` está dentro del *label* del link Markdown (`[2:28|]`), no dentro del ID entre paréntesis `(2:28)` — que es el único campo que el parser de Figma consume.

**Causa raíz:** el gate de verificación actual (o el proceso de auditoría que lo evaluó) lee el tag completo como cadena, sin distinguir label de ID.

**Corrección propuesta para el Skill:**
```
PRE-DELIVERY GATE — TAG_SCHEMA (revisado):
1. Extraer cada tag con regex que capture EXCLUSIVAMENTE el grupo entre paréntesis: \(([^)]+)\)
2. Ignorar cualquier carácter dentro de los corchetes del label — no es parte del ID.
3. Verificar membresía exacta del contenido capturado en registry_seed.json.
4. Rechazar solo si el ID entre paréntesis (no el label) contiene caracteres ajenos al registry.
```

---

## FINDING 2 — Bug de plantilla: tag placeholder literal sin ID

**Severidad:** Alta (bloqueante técnico real, distinto del Finding 1)
**Documento a corregir:** proceso de generación de CV-B (posible bug en el prompt/plantilla usado para IKEA, Inditex, Zara Home — mismas instancias o mismo prompt base)
**Skill relacionado:** `vantage-cv-b`
**Archivos afectados:** IKEA, Inditex, Zara Home — 68/68 tags cada uno

**Evidencia:** los tres archivos usan `###### figma_text_id` como línea literal — sin corchetes, sin ID real — en el 100% de sus tags. Ejemplo verbatim confirmado por el operador en esta sesión (documento adjunto al chat):
```
###### figma_text_id
**MAURICIO MEYRÁN**
```//debería ser `###### [2:4](2:4)`

**Impacto:** el parser de Figma no puede resolver ningún nodo en estos 3 archivos hasta corregir. No confirmado aún si el fallo es total (nada se inyecta) o parcial (se inyecta en el nodo equivocado) — pendiente de prueba real contra el plugin.

**Acción recomendada:** antes de reescribir contenido, correr una prueba de inyección real en Figma con uno de estos 3 archivos para diagnosticar el comportamiento del parser ante el placeholder. Documentar el resultado en `MANUAL:FIGMA-SYNC-DIAGNOSTIC` (Manual, sección 12.1 — Matriz de Errores).

---

## FINDING 3 — Overselling de función: coordinación reencuadrada como autoría técnica

**Severidad:** Crítica (afecta integridad factual del CV, no solo formato)
**Documento a corregir:** `vantage-cv-b/SKILL.md`, sección "Match Transferible Obligatorio" — reforzar el límite de Anti-overselling
**Skill relacionado:** `vantage-cv-b`
**Archivos afectados:** H&M Junior Retail Designer, H&M Retail Designer, SARELLY

**Evidencia verbatim (H&M Retail Designer, línea 92):**
> "Managed the Store Design supply chain end-to-end — fixtures, lighting and props procurement, quality control and vendor timelines"

**Evidencia verbatim (SARELLY, línea 87):**
> "Led fixture development from concept through production for the Adidas Brand Center Madero flagship opening"

**Canon real (C02, Bisonte/Adidas):** coordinación de proveedores especializados, supervisión de producción y logística de materiales, protección de integridad de diseño. **No acredita:** autoría de desarrollo/diseño desde concepto, ownership de supply chain end-to-end, autoría de paquetes arquitectónicos.

**Patrón identificado:** ambos casos convierten "coordinar/supervisar la ejecución de un tercero" en "poseer/desarrollar/dirigir la función completa desde origen" — el mismo tipo de escalada de ownership, en dos redacciones distintas (H&M en inglés vía "managed... end-to-end"; SARELLY vía "led... development from concept"). El footer de SARELLY intenta justificarlo como "Match Transferible (regla 6)", exponiendo que la regla 6 actual no distingue con suficiente claridad entre reencuadrar un hecho (permitido) y escalar el nivel de responsabilidad del hecho (prohibido).

**Corrección propuesta para el Skill (reforzar regla 6 existente):**
```
Añadir a "Match Transferible Obligatorio":
Un reencuadre NUNCA puede cambiar el verbo de nivel de ownership del hecho
original. "Coordinar" no se reencuadra como "gestionar end-to-end",
"dirigir" o "desarrollar desde concepto" — son verbos de ownership
superior, no sinónimos de framing.

Verbos de coordinación (permitidos para reencuadre): coordinar, supervisar,
alinear, colaborar con, dar seguimiento a.
Verbos de ownership pleno (prohibidos salvo literal en Canon): dirigir,
gestionar end-to-end, desarrollar desde concepto, poseer, liderar el
desarrollo de.
```

---

## FINDING 4 — Mismatch de idioma no capturado en la matriz original

**Severidad:** Media (afecta 2 de 17 archivos, detección incompleta en auditoría previa)
**Documento a corregir:** `vantage-cv-b/SKILL.md`, sección "Reglas de Serialización" — agregar política de idioma explícita
**Skill relacionado:** `vantage-cv-b`
**Archivos afectados:** Beyond, Multicont Supervisor

**Evidencia:** ambos CV-A declaran `Idioma detectado (ES/EN): ES`. Ambos CV-B tienen el cuerpo completo en inglés (`"KEY SKILLS"`, `"PROFESSIONAL PROFILE"`, etc.). El reporte original de Perplexity solo detectó este patrón en Beyond — Multicont Supervisor es un hallazgo nuevo de esta sesión.

**Corrección propuesta para el Skill:**
```
LANGUAGE POLICY (nueva sección obligatoria):
- Si HANDOFF.idioma = ES → CV-B en ES completo, salvo nombres propios,
  herramientas de software, y títulos oficiales de certificación/institución.
- Si HANDOFF.idioma = EN → CV-B en EN completo, mismo criterio de excepción.
- Verificación pre-entrega: el idioma del cuerpo del CV-B debe coincidir
  con HANDOFF.idioma antes de generar el archivo .md descargable.
  Si no coincide: STATUS=BLOCKED_LANGUAGE_MISMATCH.
```

---

## FINDING 5 — Decisión de posicionamiento estratégico tomada sin escalamiento

**Severidad:** Media (falla de proceso, no de contenido)
**Documento a corregir:** `vantage-cv-b/SKILL.md`, sección "Aplicación del Positioning Mode en el output"
**Skill relacionado:** `vantage-cv-b`, `vantage-cv-a`
**Archivo afectado:** Intimissimi

**Evidencia verbatim (footer de Intimissimi CV-B):**
> "decisión tomada por esta skill en ausencia de instrucción explícita del operador"

**Contexto:** CV-A había documentado correctamente una desalineación de seniority y la escaló al operador sin resolverla (comportamiento correcto). CV-B, en el turno siguiente, tomó la decisión de ángulo de posicionamiento por su cuenta en vez de detenerse a pedir confirmación — pese a que el propio CV-A ya había marcado el punto como pendiente de decisión humana.

**Corrección propuesta para el Skill:**
```
Añadir a "Input requerido":
Si el campo `observaciones` del HANDOFF señala una desalineación de
seniority no resuelta, CV-B debe declarar STATUS=AWAITING_OPERATOR_ANGLE
y detener la generación de contenido — no elegir un ángulo por default
y proceder. La resolución debe llegar como instrucción explícita del
operador en el mismo turno o uno posterior, nunca inferirse.
```

---

## FINDING 6 — Violación confirmada de propagación de gate (Walmart)

**Severidad:** Crítica (violación de invariante del pipeline, no de un archivo aislado)
**Documento a corregir:** `vantage-cv-a/SKILL.md`, sección "Validación de exclusiones" + `vantage-cv-b/SKILL.md`, sección "Input requerido"
**Skill relacionado:** `vantage-cv-a`, `vantage-cv-b`
**Archivo afectado:** Walmart

**Evidencia verbatim (CV-A Walmart, "Próximo paso"):**
> "BLOQUEADO — Positioning Mode en empate/mismatch de framework (requiere decisión humana) + registro en estado terminal (Expirada/Archivar)... No avanza a CV-B sin resolución de ambos puntos."

**Hallazgo:** existe un CV-B completo y bien redactado para esta vacante, pese al bloqueo explícito. Esto confirma S0.3 del reporte original de Perplexity — es el único finding de ese reporte que se sostiene sin corrección tras verificación directa.

**Corrección propuesta (ya estaba bien especificada en el reporte original, se ratifica sin cambios):**
```
GATE PROPAGATION RULE (para CV-A):
Si Positioning_Mode = EMPATE
OR Status in {Expirada, Archivada, Rechazada}
OR Next_Action = Archivar
THEN:
  handoff.cv_b_eligible = false
  handoff.block_reason = lista exhaustiva de gates

INPUT ADMISSION GATE (para CV-B):
No iniciar generación si cv_b_eligible != true.
No permitir override inferido — solo con operator_override=true explícito.
```

---

## Resumen ejecutivo para priorización de documentación

| Finding | Documento a tocar | Urgencia |
|---|---|---|
| 1 — Falso positivo tag | `vantage-cv-b/SKILL.md` | Alta — corrige ruido en auditorías futuras |
| 2 — Placeholder sin ID | Proceso de generación / `MANUAL:FIGMA-SYNC-DIAGNOSTIC` | Alta — bloqueante técnico real, sin diagnóstico aún |
| 3 — Overselling de ownership | `vantage-cv-b/SKILL.md` (regla 6) | Crítica — afecta integridad factual del CV |
| 4 — Mismatch de idioma | `vantage-cv-b/SKILL.md` (nueva Language Policy) | Media |
| 5 — Ángulo sin escalar | `vantage-cv-b/SKILL.md` (Positioning Mode) | Media |
| 6 — Gate propagation | `vantage-cv-a/SKILL.md` + `vantage-cv-b/SKILL.md` | Crítica — viola invariante ya documentado como Golden Rule |

**Nota para la instancia que documente esto:** los Findings 1, 3, 4, 5 y 6 tienen texto de corrección ya redactado arriba, listo para insertar directamente en el Skill correspondiente tras confirmación del operador — no requieren redacción adicional, solo pegado y ajuste de numeración de sección.
