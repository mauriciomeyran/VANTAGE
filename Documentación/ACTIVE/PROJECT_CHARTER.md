# V | PROJECT CHARTER

> Qué es este documento y qué no es. Este Charter no dicta cómo operar VANTAGE
(eso es MANUAL) ni qué contratos técnicos rigen (eso es KERNEL). Dicta por qué
existen esos contratos, qué se intentó antes y falló, y hacia dónde va el proyecto.
Si una sección de este documento empieza a acumular comandos, flags o
procedimientos paso a paso, esa sección está mal ubicada — repórtalo, no lo
normalices.
Regla de mantenimiento: toda decisión estructural mayor (no un fix, no un
parche puntual) se agrega aquí en la sección 2, con fecha y razón — no solo en
una entrada de Changelog que nadie vuelve a leer. Si dudas si algo califica,
favorece agregarlo: el costo de un Charter ligeramente inflado es menor que el
de un drift que se repite por tercera vez sin que nadie lo sepa.
---
## 1. CHARTER:PURPOSE — Génesis y propósito
Qué problema humano resuelve VANTAGE. Mauricio (Mau) Meyrán es profesional de
Visual Merchandising y Brand Execution en retail de lujo/premium, con más de una
década de trayectoria (L'Oréal Luxe, Levi's/Dockers LATAM, Bisonte/Adidas Brand
Center, Aéropostale, Palacio de Hierro/ALDO Group). VANTAGE nació para sistematizar
su búsqueda activa de un puesto de Dirección de VM — no como proyecto de ingeniería
por sí mismo, sino como una herramienta que debía liberar tiempo y carga cognitiva
de un proceso manual (rastrear vacantes, evaluar fit, producir CVs a la medida)
para que Mau pudiera enfocar ese tiempo en la búsqueda estratégica y en su propio
desarrollo profesional en paralelo.
Por qué existe como sistema multi-agente. El diseño no partió de "vamos a
construir un pipeline técnico elegante" — partió de la constatación de que ninguna
IA individual, en una sola sesión, podía sostener el contexto necesario para
correr discovery, evaluación determinista, producción de CV y mantenimiento
documental a la vez sin degradar calidad o inflar costo de tokens. De ahí la
arquitectura de capas (L1/L2/L3 discovery, Python determinista para Class B,
Runtime documental separado) y la práctica de dividir el trabajo entre múltiples
agentes (Claude, Perplexity, Devin, Gemini, Mistral, Copilot, Arena, GROK, Hermes)
bajo contratos de sesión acotados.
Qué constituye éxito. No es "tener una arquitectura de documentación
impecable" — eso es instrumental. Éxito es: (a) que el pipeline identifique y
capture vacantes relevantes sin ruido ni trabajo manual repetitivo; (b) que la
producción de CV por vacante sea rápida, precisa contra el Career Canon, y sin
alucinación; (c) que el sistema documental no le cueste a Mau más tiempo
mantenerlo del que le ahorra operarlo. Cuando el mantenimiento documental empieza
a consumir sesiones enteras sin mover el pipeline hacia adelante — como ha
ocurrido en la semana reciente de reconciliación — es una señal de que el
instrumento se está anteponiendo al fin.
Por qué la documentación creció como creció. KERNEL y MANUAL no nacieron
sobredimensionados por descuido — crecieron por acumulación orgánica de
decisiones tomadas sesión a sesión, cada una razonable en el momento, sin que
existiera (hasta este Charter) una capa que preservara el por qué fuera del
cuerpo normativo mismo. El resultado — documentado en las auditorías de
Perplexity y ChatGPT de 2026-09-29 — es que KERNEL y MANUAL terminaron hacien do
simultáneamente el trabajo de especificación normativa, manual de uso, registro
de evolución, catálogo de scripts, índice de navegación, reporte de auditoría,
backlog de deuda, y contrato de implementación. Este Charter es la corrección
estructural a esa causa raíz: separar el "por qué histórico" en su propio
documento para que KERNEL/MANUAL puedan, en su reescritura v10, dejar de cargar
ese peso.
---
## 2. CHARTER:DECISIONS — Cronología de decisiones estructurales mayores
> Formato: [Fecha] Decisión — Razón — Qué se descartó y por qué.
Solo decisiones que cambiaron el modelo, no fixes de código ni parches
documentales puntuales (esos viven en el Changelog).
[2026-07 aprox., fecha exacta no registrada] CHARTER:DECISIONS-001 — Separación Class A / Class B.
Python es dueño exclusivo de los campos calculados deterministamente (Score,
Gate_Decision, VM_Scope, Role_Class, Next_Action, etc.); la IA nunca los escribe
directamente. Razón: evitar que juicio de lenguaje natural determine decisiones
que deben ser reproducibles y auditables. Se descartó el modelo alternativo de
"la IA sugiere, Python valida después" porque permitía que una sugerencia mal
calibrada de la IA se colara como escritura antes de la validación.
[2026-08-07] CHARTER:DECISIONS-002 — Aéropostale removido de Hard Blocks. Confirmado con el operador
que Aéropostale, a diferencia de L'Oréal/Levi's-Dockers/Palacio de Hierro, sí
recontrata y no debía excluirse de vacantes nuevas. Cualquier referencia previa
que lo incluyera como Hard Block era un error, no una versión histórica válida.
Este error reapareció después en al menos un brief operativo — ver sección 3,
"Fracasos conocidos", primer ítem — razón directa por la que este Charter existe.
[2026-09-11] CHARTER:DECISIONS-003 — Serial Authority v2 — operador como Prioridad 0. Se eliminó del
diseño la vía MCP/HTTP de asignación de seriales de handoff (no degradada a
fallback, retirada por no ser funcional en la práctica) y se estableció que un
serial declarado directamente por el operador en el mismo turno se adopta sin
verificación adicional bajo ninguna circunstancia. Razón: instancias receptoras
de handoff estaban re-verificando exhaustivamente estado ya reportado por la
única fuente de autoridad posible (Mau es operador y transportista único de todo
handoff en el sistema) — consumiendo tokens sin mejorar fiabilidad. Se acompañó
de la introducción de S4-EVIDENCE (comando + output crudo) y la Regla de
Adopción: una instancia que recibe evidencia completa la adopta sin re-ejecutar
verificación, salvo contradicción explícita o inconsistencia interna de la
evidencia misma.
[2026-09-12, commit 7ce685ee] CHARTER:DECISIONS-004 — Retiro de layer_1_run.py / consolidate_duplicates.py (G6).
Consolidación del pipeline Layer 1 en layer_1_orchestrator.py como único activo;
los scripts anteriores se archivaron formalmente en Archive/Legacy_Scripts/ con
README de retiro. Razón: reducir superficie de scripts duplicados que generaban
ambigüedad sobre cuál era la vía operativa vigente. Este retiro no se propagó
consistentemente a la documentación — ver sección 3.
[2026-09-24, v9.22.12] CHARTER:DECISIONS-005 — Cierre E2E de Runtime/Lazy Loader — Graph declarado SUSPENDED.
Decisión de producto explícita: VANTAGE usa movimiento mutuamente excluyente entre
TRACKER y ARCHIVO_TRACKER para archivado, no relaciones de grafo. Graph/Backlinks
quedan como artefactos de observabilidad derivados, con graph_edges/backlinks_count
en 0 por diseño — no como una capa operativa pendiente de arreglar. Se descartó
la alternativa de invertir esfuerzo en hacer funcional el grafo porque el modelo
de archivado por movimiento de fila ya cumplía la función sin esa complejidad
adicional.
[2026-09-24 a 09-25] CHARTER:DECISIONS-006 — Detección de fabricación en auditoría externa — origen de
la disciplina de verificación 1:1. Una primera ronda de auditoría delegada a
Perplexity produjo una "Cédula de Reconciliación" con datos plausibles (versión
v9.21.40, estados PASS) sin fuente verificable — patrón de fabricación
detectado y rechazado antes de que contaminara cualquier decisión. A partir de
este incidente se estableció como principio rector de todo el proceso de
reconciliación v10: ningún diagnóstico externo (de cualquier agente) se trata
como hecho hasta verificación 1:1 contra fuente primaria real (Notion vivo,
GitHub real, Terminal real). Se descartó confiar en la "buena forma" de un
reporte (citas, tablas, aparente rigor) como sustituto de la verificación —
la segunda ronda de Perplexity, con URLs reales y admisiones honestas de
FUENTE NO ACCESIBLE, demostró que la forma correcta sí es alcanzable y se
volvió el estándar exigido en todo contrato de sesión posterior.
[2026-09-25] CHARTER:DECISIONS-007 — Dedup_Flag migrado de select a checkbox — drift documental
cerrado con evidencia dura. El campo cambió de tipo en Notion (registrado en
Changelog v9.22.3) pero KERNEL nunca se actualizó en consecuencia, y esa
discrepancia sobrevivió sin resolverse durante meses hasta la auditoría de
reconciliación. Razón para registrarlo aquí (no solo como fix): es el caso
de referencia de cómo un cambio de código sin la disciplina de propagación
documental puede persistir invisible hasta una auditoría dedicada.
[2026-09-27 a 09-29] CHARTER:DECISIONS-008 — Reconciliación v10 — modelo de tracks paralelos. Se
adoptó el modelo Track Alpha (normativo/KERNEL) + Track Beta (código/scripts)
corriendo en paralelo durante Fase 1 y 2, convergiendo en Fase 3. Razón: evitar
que la corrección de contradicciones documentales avance desacoplada de la
verificación del código real que esas contradicciones describen — el patrón que
ya había fallado antes (documentación "corregida" sobre un estado de código no
verificado).
[2026-09-29] CHARTER:DECISIONS-009 — Blueprint de reescritura KERNEL/MANUAL v10 — adopción híbrida.
Se decidió no adoptar un solo diagnóstico externo en bloque; se usa el blueprint
estructural de ChatGPT (12 secciones para KERNEL, 9-10 para MANUAL, con matriz
sección-por-sección KEEP/REWRITE/MOVE/MERGE/SPLIT/REMOVE) como plan de
construcción, y la tabla de contradicciones X-01..X-10 de Perplexity como lente
de validación de riesgo antes de mover cualquier sección. Razón: cada auditoría
por separado tenía un punto ciego que la otra cubría (ChatGPT no consolidaba
duplicaciones cruzadas con la misma trazabilidad; Perplexity no proponía
estructura de reemplazo ejecutable).
[2026-09-29] CHARTER:DECISIONS-010 — Creación de este Charter. Ver sección 1 para la razón completa.
Decisión explícita del operador tras notar que saltar entre sesiones y entre
instancias de agente (para economizar contexto/tokens) estaba erosionando la
continuidad de objetivos, decisiones y prioridades — el mismo contexto de
génesis que permitió detectar los drifts de esta semana solo existía en una
instancia de Claude, no en ningún documento del proyecto.
[2026-09-30] CHARTER:DECISIONS-011 — CLAUDE/MAIN declarado gatekeeper exclusivo de cambios al
Charter — vía SP:BOOTLOADER-002 y Bootstrap Universal. Ningún agente
escribe directamente sobre este documento; todo cambio entra como ticket
Task Tracker tipo CHARTER, evaluado únicamente por CLAUDE/MAIN, aplicado
únicamente por el operador. Se descartó un modelo más flexible (cualquier
instancia de Claude activa podría evaluar, declarándolo explícitamente) por
innecesario: VANTAGE tiene un operador único que controla directamente a qué
instancia entrega cada ticket, así que la garantía de enrutamiento correcto
no requiere un mecanismo automático — depende del propio operador, hecho que
el operador asumió explícitamente como suficiente. Motivo de la decisión:
sin un punto único de continuidad editorial, el propio Charter quedaría
expuesto al mismo patrón de drift que existe para corregir (ver el caso
Littlebird/v9.22.20 como ejemplo de edición externa bien ejecutada, pero que
motivó la pregunta de qué pasa cuando una edición no está tan bien
verificada).
---
## 3. CHARTER:FAILURES — Fracasos conocidos (para no repetir)
> Si estás a punto de proponer algo que se parece a uno de estos, revisa primero
por qué no funcionó.
CHARTER:FAILURES-001 — Reaparición de Hard Blocks ya corregidos. El bloqueo de Aéropostale se
levantó explícitamente el 2026-08-07, pero volvió a aparecer como exclusión en
al menos un brief operativo posterior, obligando a corregirlo dos veces. Causa
raíz: la corrección vivía solo en una entrada de Changelog y en la memoria de
la sesión que la hizo, sin quedar consolidada en un lugar que un agente nuevo
consultara por default. Mitigación: este Charter, más la disciplina de que
Hard Blocks reales se declaran una sola vez en el KERNEL vigente, nunca se
re-derivan de briefs históricos.
CHARTER:FAILURES-002 — Patrón de reporte optimista (ticket RT-1, Bug Tracker). Al menos tres
episodios documentados donde un agente (Devin en dos ocasiones, Gemini en una)
reportó una corrección o un push/commit como aplicado cuando la verificación
independiente mostró que no lo estaba, o que el bug de sintaxis seguía presente.
Mitigación adoptada: ningún reporte de éxito de otro agente se acepta sin
re-fetch/re-verificación independiente contra la fuente real (repo, Notion,
Terminal) — este es hoy un principio explícito de ways-of-working, nacido
directamente de este patrón repetido.
CHARTER:FAILURES-003 — Cédula de Reconciliación fabricada (primera ronda de auditoría externa,
2026-09-24/25). Ver sección 2 para el detalle. El fracaso no fue solo el dato
fabricado — fue que tenía forma de rigor (citas, tablas, formato profesional)
suficiente para casi pasar sin objeción. Mitigación: todo contrato de sesión con
un agente delegado exige ahora URL/cita verificable específica, no solo nombre
de fuente, y prohíbe explícitamente declarar "PASS"/"Verificado" sin evidencia
citable.
CHARTER:FAILURES-004 — Loop de auto-rechazo QA↔CV-B (detectado 2026-08-19). Un CV-B generado por
Claude fue rechazado por la propia skill de QA de Claude en el mismo turno, y
"corregido" sin cambio real verificable — un ciclo de generar-rechazar-simular
corrección sin progreso genuino. Mitigación estructural: se separó
explícitamente la responsabilidad de QA (audita, no corrige) de CV-B
(construye, no se auto-audita en el mismo turno) — la regeneración tras un
NO-GO requiere invocación explícita separada del operador, nunca colapsarse
en el mismo turno por inercia conversacional.
CHARTER:FAILURES-005 — Documentación que describe código ya retirado. Patrón recurrente, no un
incidente único: layer_1_run.py y consolidate_duplicates.py permanecieron
documentados como scripts activos en MANUAL semanas después de su retiro real
(commit 7ce685ee, 2026-09-12). Detectado independientemente por dos auditorías
externas y confirmado contra el repo real. Causa raíz: no existe (todavía) un
paso obligatorio de "actualizar MANUAL:SCRIPT-GLOSSARY" como parte del checklist
de retirar un script — es una tarea pendiente de Fase 3, no resuelta aún.
Discrepancia de versión no bloqueante tratada como bloqueante, y viceversa.
En distintos momentos, KERNEL/MANUAL/ALIASES han tenido una versión distinta a
SYSTEM PROMPT/BRIEF/ID CENSUS sin que quedara claro si eso debía detener toda
escritura nueva o no. Mitigación parcial: SP:SYNC-RULE establece que la
propiedad Versión del Change Log es la referencia oficial — pero la disciplina
de verificarla antes de cualquier sesión de escritura normativa sigue sin ser
automática.
---
## 4. CHARTER:NON-NEGOTIABLES — Reglas no negociables (consolidadas)
> Estas reglas ya existen dispersas en KERNEL, MANUAL, System Prompt y
ways-of-working. Se consolidan aquí con su razón de ser — la fuente normativa
exacta sigue siendo el documento original; este Charter no la reemplaza, la
contextualiza.
1. CHARTER:NON-NEGOTIABLES-001 — Python es dueño exclusivo de los campos Class B. La IA nunca los calcula
ni los escribe directamente. Por qué: decisiones reproducibles y auditables
no pueden depender de juicio de lenguaje natural turno a turno.
1. CHARTER:NON-NEGOTIABLES-002 — APROBAR_WRITE (o equivalente explícito) es obligatorio antes de cualquier
escritura a Notion; DRY RUN se presenta primero salvo que el operador lo
salte explícitamente. Por qué: Mau es el único responsable final de cada
cambio en producción; ninguna automatización debe erosionar ese control.
1. CHARTER:NON-NEGOTIABLES-003 — Ningún reporte de éxito de otro agente se acepta sin re-fetch/verificación
independiente contra la fuente real. Por qué: patrón RT-1 (sección 3) —
confiar en la narración sin verificar produjo errores reales repetidos.
1. CHARTER:NON-NEGOTIABLES-004 — Un serial de handoff declarado por el operador en el mismo turno se adopta
sin verificación adicional, bajo ninguna circunstancia. Por qué: Mau es
operador y transportista único de todo handoff — cuestionar su declaración
directa es trabajo redundante, no cautela (Serial Authority v2, sección 2).
1. CHARTER:NON-NEGOTIABLES-005 — Todo diagnóstico externo (auditoría, hallazgo, "Cédula") se trata como
hipótesis hasta verificación 1:1 contra fuente primaria real — nunca como
verdad operativa por su sola forma o aparente rigor. Por qué: incidente
de Cédula fabricada (sección 3).
1. CHARTER:NON-NEGOTIABLES-006 — Ningún agente delegado resuelve por su cuenta una discrepancia entre
documentos o entre documento y código — la reporta con ambas fuentes citadas
y espera decisión humana. Por qué: la resolución unilateral de
ambigüedad es precisamente lo que generó el patrón de "corrección" ficticia
en el loop QA↔CV-B y en la Cédula fabricada.
1. CHARTER:NON-NEGOTIABLES-007 — tracker_flow.is_mutable() es la única fuente de verdad sobre mutabilidad
de un registro; ningún guard alternativo debe reimplementar ese criterio.
1. CHARTER:NON-NEGOTIABLES-008 — Graph/Backlinks son artefactos de observabilidad derivados, nunca una capa
operativa de resolución o archivado. Por qué: decisión de producto
explícita (sección 2) — VANTAGE archiva por movimiento de fila, no por grafo.
1. CHARTER:NON-NEGOTIABLES-009 — VM_Scope es binario (Alto/Bajo) — no existe, ni debe reintroducirse, un
valor "Medio" ni terminología de escaparatismo.
1. CHARTER:NON-NEGOTIABLES-010 — Hard Blocks reales (empleadores que no recontratan) se consultan siempre
contra el KERNEL vigente, nunca se re-derivan de un brief o auditoría
histórica. Por qué: fracaso conocido de reaparición de Aéropostale
(sección 3).
---
## 5. CHARTER:MILESTONES — Trayectoria esperada — hitos de fase, no lista de tareas
> Esta sección no duplica el Plan de Trabajo (Notion) — ese vive de tareas que
cambian de estado todos los días. Aquí van los hitos que casi nunca
cambian aunque las tareas debajo sí, con su definición explícita de "hecho".
Si te encuentras editando esta sección cada sesión, algo se filtró aquí que
debería vivir en el Plan de Trabajo, no aquí.
CHARTER:MILESTONES-001 — Hito 1 — Track Beta (código) cerrado de una sola vez. ✅ CERRADO 2026-09-29,
vía Arena.IA Agent Mode, evidencia línea-por-línea contra HEAD=cef2de7.
Las 10 preguntas recurrentes quedan respondidas para siempre — no se vuelven a
levantar desde cero en ninguna sesión futura, con cualquier agente:
Motivo explícito de este hito (palabras del operador, 2026-09-29): hartazgo
genuino de responder la misma pregunta a distintos agentes en distintos
momentos sin que ninguno recordara la respuesta anterior. Con esta tabla, esa
pregunta deja de repetirse — cualquier agente que la levante de nuevo se
remite aquí.
CHARTER:MILESTONES-002 — Hito 2 — T2.1 (Redacción KERNEL v10) arranca en paralelo a Track Beta, no
después. Definición de hecho: T2.1 no espera a que Track Beta cierre al
100% si las piezas de Track Beta que bloquean secciones específicas del KERNEL
(la cifra de documentos fundacionales, la jerarquía de dedup L1>L2>L3, el
scope real de vsync_doc.py) ya están resueltas — lo cual, a la fecha de este
Charter, ya lo están (ver Changelog v9.22.17-19). El resto de Track Beta
(scripts de Layer 4/Dashboard/Raycast) no bloquea el arranque de la redacción
normativa central de KERNEL.
CHARTER:MILESTONES-003 — Hito 3 — MANUAL v10 corre en paralelo a KERNEL v10 una vez que ambos
comparten la misma base de hechos verificados (Cédula de Reconciliación +
output de Track Beta cerrado). No se redacta MANUAL v10 sobre una cifra o un
estado de script que Track Beta aún no ha confirmado.
CHARTER:MILESTONES-004 — Hito 4 — Fase 3 (sync + verificación cruzada) solo arranca cuando KERNEL v10
y MANUAL v10 tienen draft completo, no parches incrementales sobre v9.22.x.
Definición de hecho: vsync corre sobre el árbol v10 completo una sola vez,
no sobre fragmentos sueltos — evitar el patrón de esta semana donde cada
parche puntual requería su propio ciclo de vversions --sync / vgit.
CHARTER:MILESTONES-005 — Hito 5 — Este Charter se actualiza en cada decisión estructural mayor,
no solo en checkpoints de fase. Ver sección 2 para el criterio de qué
califica como "estructural mayor" vs. "fix, no anotar aquí".
---
## 6. CHARTER:CONTINUITY — Protocolo de continuidad entre agentes y sesiones
Gatekeeping de cambios al propio Charter (decisión 2026-09-30 — ver sección
2 y SP:BOOTLOADER-002). Ningún agente, bajo ninguna vía, escribe
directamente sobre este documento — ni siquiera Claude. Toda propuesta de
cambio entra exclusivamente como ticket en Task Tracker, tipo CHARTER.
Cualquier agente puede proponer y redactar el bloque de texto sugerido; solo
CLAUDE/MAIN evalúa consistencia editorial del ticket contra el contenido
íntegro del Charter, y solo el operador aplica el cambio en Notion vía
APROBAR_WRITE (los dos contratos conviven: uno gobierna qué cambia, el
otro gobierna si se escribe). No existe mecanismo automático de
enrutamiento del ticket a CLAUDE/MAIN — VANTAGE tiene un operador único, y
la garantía de que el ticket llega a la instancia correcta depende
exclusivamente de que el operador lo entregue ahí. CLAUDE/MAIN no evalúa un
ticket sin haber fetcheado el Charter completo en esa misma sesión — el rol
declarado en el System Prompt no sustituye la lectura real.
Regla general — quién lee esto y cuándo. Todo agente que opere sobre
VANTAGE (Claude en cualquier instancia, Perplexity, Devin, Mistral, Copilot,
Arena, GROK, Hermes, o cualquier otro que se incorpore después) lee este
Charter antes de tocar KERNEL, MANUAL, cualquier tracker, o cualquier
decisión que dependa de contexto histórico — no solo quien abre sesión formal
de Claude. Esto incluye agentes invocados solo para una tarea puntual y
acotada (ej. un contrato de sesión de una sola pregunta): si la tarea toca
una de las Reglas No Negociables (sección 4) o un Fracaso Conocido (sección
3), el contrato de sesión correspondiente debe citarlos explícitamente, no
asumir que el agente los conoce.
Vía primaria de acceso — MCP a Notion. La mayoría de los agentes en uso
hoy tienen alguna forma de MCP con acceso de fetch a Notion, aunque con
herramientas y límites de carga distintos entre sí. Esa es la vía primaria
para leer este Charter (y cualquier documento fundacional): fetch directo
contra la página viva, nunca contra una copia de memoria del agente ni contra
un mirror local sin confirmar que está sincronizado.
Fallback — degradación reportada, no asumida. Si un agente no tiene
acceso MCP a Notion, o su MCP falla, no debe asumir contenido ni proceder
sin él. El protocolo es:
1. El agente reporta explícitamente la degradación (qué documento necesitaba,
por qué no pudo fetchearlo) — nunca continúa silenciosamente con una
versión de memoria o inferida.
1. El agente entrega al operador el comando específico que el operador
puede correr en su propia Terminal para resolver el fetch con el menor
costo de tokens posible (ej. vload --route PREFIX:CLAVE para un
documento fundacional ya dado de alta en el registry documental).
1. El operador corre el comando, procesa el resultado, y se lo entrega de
vuelta al agente en el chat.
Excepción explícita — este Charter todavía no tiene ruta de Lazy Loader.
A la fecha de creación de este documento, el Charter no tiene un prefijo
canónico dado de alta en document_registry/registry_seed.json — por lo
tanto, el fallback de vload --route CHARTER:... no funciona todavía y
no debe prometerse como si existiera. Hasta que se decida y ejecute esa alta
(tarea de Track Beta / Fase 3, no resuelta en este documento), el único
fallback real para el Charter es que el operador lo adjunte manualmente como
archivo en la sesión. Cualquier agente que reporte no poder fetchear el
Charter vía MCP debe recibir instrucción de pedir el archivo directamente,
no un comando vload que aún no resuelve a nada.
Qué hace un agente delegado al recibir este Charter. Lo trata como
contexto de lectura obligatoria, no como fuente a re-verificar línea por
línea en cada sesión — pero sí puede y debe señalar si alguna instrucción
recibida en su contrato de sesión parece contradecir una Regla No Negociable
(sección 4) o repetir un patrón de Fracaso Conocido (sección 3). Señalarlo
no es exceder su mandato — es exactamente el tipo de "válvula de escape" que
ya rige el protocolo de convivencia con IA de este proyecto.
---
## 7. CHARTER:STATUS — Estado de este documento
Ya importado a Notion por el operador (draft inicial). Fact-checkeado contra
fuentes primarias por el propio operador (sesión 2026-09-29, vía Notebook)
para las secciones 1-4; ese fact-check citó varios IDs canónicos sin
verificación independiente en el momento. Estado de esos IDs, actualizado
2026-09-30 v9.22.20 por LITTLEBIRD/DEFAULT (WRITE aplicado directo en
Notion, no en este sandbox — ver Change Log para el registro completo):
- KERNEL:CV-GOLDEN-RULES-002 — ✅ confirmado 1:1 contra KERNEL v9.22.19,
sección 10.2 ("Regla de Oro #2"). Citable hacia adelante.
- BRIEF:CROSS-DEPENDENCIES-001 — ✅ confirmado 1:1 contra BRIEF v9.22.19,
sección 07.1 ("Impact Assessment Contract"). Citable hacia adelante.
- KERNEL:GATE-DECISION-012 — conservado explícitamente como referencia no
operativa/huérfana (el Kernel vigente usa KERNEL:DEDUP-LAYER-UPGRADE en
09.12). No se reactiva, no se cita como válido, no entra al Census.
- Deprecación de auto_archive.py — sigue pendiente, no se cita como
hecho confirmado.
Esta corrección fue puntual (solo esos dos IDs) y no convirtió al Charter en
documento canónico versionado: sin prefijo asignado, sin alta en Census,
sin cambio de propiedad Versión/Fecha de actualización — todas las
decisiones de gobernanza de la lista de abajo siguen abiertas.
Numeración de nodos e IDs (propuesta de Mistral, 2026-09-30) — aplicada en
este documento, alta en Census pendiente. El prefijo CHARTER: y los IDs
insertados en cada sección/subsección de este documento (CHARTER:PURPOSE,
CHARTER:DECISIONS-001..011, CHARTER:FAILURES-001..005,
CHARTER:NON-NEGOTIABLES-001..010, CHARTER:MILESTONES-001..005,
CHARTER:CONTINUITY, CHARTER:STATUS) siguen la estructura que Mistral
propuso, con dos ajustes: (a) la cronología corrió de 9 a 11 entradas
(sumando la creación del propio Charter y la decisión de gatekeeping
CLAUDE/MAIN del 2026-09-30); (b) el bloqueo original de Mistral — Census
local en GitHub desalineado del KERNEL vivo (03.8/03.13 con significados
distintos en cada lado) — quedó resuelto por la sesión de trabajo con
Littlebird el 2026-09-30: fetch fresco (cache-busted) confirmó 9/9 nombres
nuevos presentes en KERNEL vivo, 0/7 nombres viejos remanentes en el Census
de GitHub, Census Notion↔GitHub idénticos, y 03.8/03.13 alineados
(re-verificado independientemente vía fetch directo a V | ID CENSUS,
propiedad Versión v9.22.20, sin huérfanos detectados). Pendiente real
restante, no resuelto por lo anterior: el alta formal del prefijo
CHARTER: en resolver_registry_v2.json/registry_seed.json y su
incorporación al ID Census — eso habilita vload --route CHARTER:...
(hoy inexistente, ver sección 6) y sigue siendo tarea de Fase 3 / próximo
ticket tipo CHARTER, no de este documento.
Pendiente de decisión del operador:
- Nombre final del documento y su ubicación jerárquica exacta en Notion.
- Si el Charter recibe su propio prefijo canónico en el registry documental
(CHARTER: o equivalente) — y si es así, alta correspondiente en
document_registry, registry_seed.json, y ID Census.
- Si este Charter reemplaza o convive con el "Tablero" actual de la página
TRACKER MANUAL & KERNEL.
- Si entra o no a la vigilancia de vversions/Regla de Versión Única de los
documentos fundacionales, o si mantiene su propio ciclo de versión
independiente.
- Actualización de la plantilla de contrato de sesión estándar para incluir
una línea de "lee primero V | PROJECT CHARTER" en todo contrato futuro
(sección 6).
