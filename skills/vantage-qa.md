---

name: vantage-qa

description: Auditoría de calidad final canónica de VANTAGE (KERNEL:TRG-QA) sobre un CV en PDF antes de postularlo. Usar cuando el operador invoque el trigger "QA [PDF]", adjunte un PDF de CV pidiendo revisión final, o pida verificar que un CV ya construido cumple con el Career Canon antes de enviarlo a una vacante. Emite un veredicto binario GO/NO-GO. No usar para el análisis inicial de vacante (eso es vantage-cv-a) ni para construir el CV (eso es vantage-cv-b) — esta skill solo audita un PDF ya terminado.

---

# VANTAGE — Skill QA (Verificación Canónica)

ID Canónico: `KERNEL:TRG-QA` · Trigger: `QA [PDF]`

Versión de alineación: v9.18.0 (2026-10-15) — checklist de 8 ítems. Versión anterior: v9.17.0 (patch post-mortem 2026-08-19 — BUG_TICKET, ver Bug Tracker)

## Responsabilidad

Última fase antes de postulación. Audita un CV en PDF ya construido contra el Career Canon y el Output Contract, y emite un veredicto binario GO/NO-GO con observaciones. No corrige el CV — reporta.

**Alcance.** QA valida el **entregable**, no la vacante: formato, fidelidad al Canon, cobertura de lo que el HANDOFF ya declaró y legibilidad del documento. No evalúa fit, oportunidad, score ni conveniencia de aplicar (`KERNEL:TRG-QA`, `KERNEL:CVR-NOFIT`). Los ítems 3 y 8 miden si el documento dice lo que el HANDOFF y el propio PDF afirman, nunca si la vacante conviene.

> Nota de sincronización: Kernel (`KERNEL:TRG-QA`) y Manual (`MANUAL:WEEKLY-FLOW-003`) fueron corregidos al checklist de 8 ítems en el mismo turno de publicación de v9.18.0 (Changelog v9.22.50, 2026-10-16). Corregir la cifra en Kernel/Manual, no reducir este checklist.
> 

## Regla Anti-Ambigüedad (v9.17.0)

Cada uno de los 8 ítems se evalúa en **una sola pasada** contra la lista canónica

exacta (ej. Hard Blocks: L'Oréal, Levi's, Palacio de Hierro — nombre

literal, no interpretación laxa).

- **Prohibido narrar reconsideración dentro del veredicto** — frases como "sin

&#x20;  embargo," "corrijo a," "en rigor no hay violación" dentro de la tabla o el

&#x20;  cuerpo del reporte indican que el chequeo no se hizo con la lista canónica

&#x20;  desde el inicio.

- Si hay duda genuina sobre un ítem, el resultado es **FAIL** con nota "requiere

&#x20;  confirmación humana" — nunca un PASS auto-justificado en el mismo mensaje.

- Esto no impide reportar contexto (ej. "menciona L'Oréal como historial, no

&#x20;  como target — ver ítem 4 nota") pero el veredicto del ítem mismo no se

&#x20;  negocia en vivo.

## Separación QA ↔ CV-B (v9.17.0)

Un FAIL en QA **nunca se resuelve regenerando CV-B en el mismo turno** por

instrucción implícita o por inercia conversacional. El output correcto de un

NO-GO es la lista priorizada de correcciones (ya requerida en el formato de

salida) — y ahí termina la responsabilidad de esta skill.

La regeneración de CV-B con esas correcciones como input requiere una

invocación explícita separada del operador (mismo principio de Single-Item

Processing que ya rige `vantage-cv-b`, aplicado aquí al handoff QA→CV-B).

Razón: colapsar QA y CV-B en el mismo turno fue la causa del loop de

auto-rechazo detectado 2026-08-19 (Claude generando CV-B, rechazándolo en QA,

y "corrigiendo" sin cambio real verificable).

## Input requerido

Archivo PDF del CV terminado. Si no está adjunto o el path no existe en `/mnt/user-data/uploads/`, solicitarlo antes de proceder — no asumir contenido.

Lee el PDF con las herramientas de computer use disponibles (ver skill `pdf-reading` si el contenido no está ya en contexto).

Si existe un HANDOFF de `vantage-cv-a` para esta vacante, úsalo como referencia para los ítems 3 y 5 — incluyendo el campo `observaciones` si tiene contenido (discrepancias que el operador ya conocía al momento del análisis).

Los ítems 1, 3 y 5 requieren leer el Career Canon vivo (`CANON:OUTPUT-CONTRACT-002`, hechos y KPIs por ID, `CANON:PROFILE-001/002`). Si no está accesible, esos ítems son `FAIL — requiere confirmación humana`; no se evalúan de memoria.

## Lista de frases vacías (ítems 5 y 8)

Lista de trabajo para detectar relleno genérico. Aplica según el idioma del PDF. La coincidencia ignora mayúsculas y acentos, y cubre género y número. Es **idéntica** a la lista de `vantage-cv-b` (Gates 11a y 12): un cambio a una exige el mismo cambio en la otra, en el mismo turno, hasta que exista un archivo de configuración compartido (decisión del operador).

**ES:** apasionado por · pasión por · orientado a resultados · proactivo ·

dinámico · ayudo a · transformando · amplia experiencia · sólida experiencia ·

gran experiencia · historial probado · probada trayectoria · líder nato ·

visionario

**EN:** passionate about · passion for · results-driven · results-oriented ·

proactive · dynamic · I help · transforming · extensive experience · solid

experience · proven track record · team player · self-starter

## Checklist Canónico de 8 Ítems

Recorre los 8 ítems en orden. Para cada uno, documenta el resultado (PASS / FAIL / N/A con razón), aplicando la Regla Anti-Ambigüedad arriba.

### 1. Invarianza estructural

¿Los subtítulos y headers del PDF coinciden con el Golden Skeleton (`CANON:OUTPUT-CONTRACT-002`, numeración real `2:X`/`3:X`)? Verifica que no se hayan fusionado, dividido, renombrado o reordenado secciones respecto a la estructura canónica. Incluye verificar que el tercer párrafo de perfil (`2:10`) no sea una duplicación verbatim del segundo (`3:13`) — si el CV-B correspondiente no tenía material para un tercer párrafo distinto, el slot debe quedar sin texto visible (un solo carácter espacio en el `.md`, `CANON:OUTPUT-CONTRACT-004`; nunca `[PENDING DATA]`), nunca repetir el párrafo anterior.

**Fuente obligatoria para este ítem**: leer `CANON:OUTPUT-CONTRACT-002` (Golden Skeleton) directamente del Career Canon antes de evaluar — no evaluar de memoria ni contra una copia local desactualizada del Skeleton. Si el Golden Skeleton no está accesible al momento de correr QA, detener el ítem 1 y declararlo `FAIL — requiere confirmación humana` (Regla Anti-Ambigüedad), no asumir estructura.

### 2. Orden cronológico

¿La trayectoria (Experience) sigue orden cronológico absoluto, sin reordenamiento estratégico? Referencia: `CANON:CAREER-TIMELINE` — C01 (2025–2026) → C02 (2022–2023) → C03 (2018–2021) → C04 (2017–2018) → C05 (2012–2017), en orden inverso-cronológico estándar de CV (más reciente primero). Verifica que ningún rol se haya movido de posición para "verse mejor" ante el JD.

### 3. Cobertura JD

Si hay un HANDOFF de CV-A disponible para esta vacante, mapea las keywords estratégicas identificadas ahí (`JD_keywords_top6`) contra el texto del PDF. ¿Están presentes las que el HANDOFF marcó como matches directos? Revisa también si `observaciones` del HANDOFF señala algo que el CV-B debía reflejar y no lo hizo.

**Cobertura por ID canónico (v9.18.0).** Toma hasta tres matches directos del Gap Analysis del HANDOFF, en el orden en que aparecen, cada uno con su ID canónico (`KPIxx`, `CFxx` o `CANON:EXPERIENCE-xxx`). Para cada uno, verifica que el PDF contenga el hecho de ese ID con su valor canónico (el mismo valor que se usa en el ítem 5). Si el hecho falta y el ID está en el HANDOFF como match directo, es **FAIL por omisión**. Si lo que falta es un requisito que el HANDOFF declara en `fit_gaps` (sin soporte en el Canon), no es defecto del CV: va a la sección Observaciones del reporte, sin afectar el veredicto.

**Resultado registrado (v9.18.0).** Para cada match directo verificado: si el Career Canon registra un resultado (KPI o consecuencia explícita) para ese hecho, el PDF debe preservarlo; su omisión es **FAIL por omisión**. Si el Canon no registra resultado para ese hecho, va a la sección Observaciones — no es defecto del CV. Sin HANDOFF, N/A (mismo criterio de arriba). Cobertura limitada a los matches directos del HANDOFF (hasta tres): los bullets fuera de ese radio quedan vigilados únicamente por la ALERTA del Gate 11b de CV-B.

Si no hay HANDOFF disponible, marca este ítem como N/A y anótalo en observaciones — no infieras cobertura sin el HANDOFF de referencia.

### 4. Hard Blocks — exclusiones de marcas protegidas

Confirma que el CV no está siendo preparado para ni menciona como target actual a: **L'Oréal (todas las divisiones), Levi's, El Palacio de Hierro** (Hard Blocks confirmados en `MANUAL:DATA-MANAGEMENT`), ni a roles store-level sin alcance estratégico o multi-tienda.

> Nota: Aéropostale NO es un Hard Block — confirmado con el operador 2026-08-07. Cualquier referencia previa que lo incluyera (memoria operativa u otros briefs) era un error; el historial en Aéropostale sigue siendo válido como contenido del CV (Experience Records C04) y las vacantes de esa empresa no se excluyen por este criterio.
> 

Nota: el historial laboral en estas empresas SÍ es válido como contenido del CV (Experience Records C01, C03, C04, C05) — el bloqueo aplica solo a que el CV se esté preparando *para* una vacante nueva ahí, no a mencionar el pasado. Este es el único contexto permitido dentro del veredicto del ítem (ver Regla Anti-Ambigüedad) — se declara una vez, no se "negocia" línea por línea.

### 5. No inferencia / Canon

¿Todo dato en el PDF (métricas, fechas, nombres, certificaciones) tiene respaldo directo en el Career Canon? Revisa especialmente:

- Certificaciones: solo son válidas `CERT01` (ALDO Group, Montréal, 2014) y `CERT02` (AutoCAD & SketchUp Essentials, LinkedIn Learning, 2024) — `CANON:UF-003`. Cualquier otra certificación en el PDF es FAIL inmediato.
- Métricas (KPI01–KPI09): deben coincidir exactamente con los valores canónicos, sin redondeos ni inflación.
- Email canónico: `mauricio.meyran@icloud.com` (`CANON:UF-002`).
- **Frases vacías (v9.18.0).** Busca en el tagline, los párrafos de perfil y los bullets de Experience cada frase de la "Lista de frases vacías" del idioma del PDF. Una ocurrencia es FAIL, salvo que la frase aparezca literal en el Canon (`CANON:PROFILE-001/002` o `CANON:EXPERIENCE-001` a `-005`, en el idioma activo); esa exención se declara una sola vez en las observaciones del ítem. En el tagline no hay exención. No aplica a Skills, contacto, formación ni certificaciones. Es una segunda llave independiente del Gate 11a de CV-B.

### 6. Formato y completitud

Verificación visual y técnica: ¿el PDF se ve completo (sin cortes de texto, overflow, o secciones a medio renderizar)? Cualquier `[PENDING DATA]` visible en el documento final, o un slot con texto de relleno en lugar de un espacio, es **FAIL sin excepción**. Un slot sin datos debe verse en blanco (ver ítem 1, nota sobre `2:10`).

### 7. Diferenciación de Contenido (Anti-cloning, v9.16.0)

Compara el texto del PDF contra los demás entregables del mismo batch (otros CV-B generados en la misma sesión o corrida). Un match verbatim >80% en la sección Experience frente a cualquier otro entregable del batch resulta en FAIL automático de este ítem — independientemente del Positioning Mode. Si no hay otros entregables del batch disponibles para comparar, marca N/A y anótalo en observaciones.

### 8. Prueba del desconocido (v9.18.0)

Evalúa si un lector que no conoce al candidato entiende a qué se dedica leyendo solo el encabezado y el perfil. Usa **únicamente** el tagline (`2:5`) y los párrafos de perfil (`2:9`, `3:13`, `2:10`) del PDF. No consultes Experience, el JD ni el HANDOFF.

Escribe en el reporte, en una línea, la frase deducida con esta forma fija:

> Se dedica a [función] en [sector o escala].
> 
- **[función]** debe poder extraerse del tagline o del perfil.
- **[sector o escala]** debe poder extraerse del tagline o del perfil (por ejemplo, lujo, retail, LATAM, 270+ puntos de venta).

PASS si ambos elementos se extraen de esos bloques. FAIL si alguno solo puede deducirse de Experience o no aparece. La frase escrita es la evidencia del ítem; si no puedes escribirla sin recurrir a Experience, es FAIL. Este ítem no compara el documento con el JD ni juzga la conveniencia de la vacante.

## Output — Veredicto

Estructura del reporte (en el chat, no requiere archivo descargable salvo que el operador lo pida):

```
## QA Report — [nombre del archivo]

| # | Ítem | Resultado | Observaciones |
|---|---|---|---|
| 1 | Invarianza estructural | PASS/FAIL | |
| 2 | Orden cronológico | PASS/FAIL | |
| 3 | Cobertura JD | PASS/FAIL/N/A | |
| 4 | Hard Blocks | PASS/FAIL | |
| 5 | No inferencia / Canon | PASS/FAIL | |
| 6 | Formato y completitud | PASS/FAIL | |
| 7 | Diferenciación de Contenido | PASS/FAIL/N/A | |
| 8 | Prueba del desconocido | PASS/FAIL | |

Frase deducida (ítem 8): Se dedica a [función] en [sector o escala].

## Observaciones (no afectan el veredicto)

[Requisitos del HANDOFF sin soporte en el Canon (`fit_gaps`), ítems N/A y su razón, exenciones de Canon usadas en el ítem 5. Si no hay nada, "Ninguna".]

## Veredicto: GO / NO-GO

[Si NO-GO: lista priorizada de qué corregir antes de re-someter a QA.
Corrección se ejecuta vía invocación explícita separada de CV-B — ver
Separación QA↔CV-B arriba. Esta skill no regenera el CV.]
```

Regla de veredicto: **un solo FAIL en cualquier ítem = NO-GO.** No hay veredictos parciales o "GO con reservas" — eso viola el invariante de estado binario del brief original. Los N/A no cuentan como FAIL; los puntos de la sección Observaciones tampoco.