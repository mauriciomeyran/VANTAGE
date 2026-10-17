# V | PROJECT CHARTER

> Qué es este documento y qué no es. Este Charter no dicta cómo operar VANTAGE
(eso es MANUAL) ni qué contratos técnicos rigen (eso es KERNEL). Dicta por qué
existen esos contratos, qué se intentó antes y falló, y hacia dónde va el proyecto.
Si una sección de este documento empieza a acumular comandos, flags o
procedimientos paso a paso, esa sección está mal ubicada — repórtalo, no lo
normalices.
Regla de mantenimiento: toda decisión estructural mayor (no un fix, no un parche puntual) se agrega en el CHARTER LOG (sección Decisiones), con fecha y razón — no solo en una entrada de Changelog que nadie vuelve a leer. Si crea o cambia una regla que todo agente debe respetar, esa regla va además, en una línea, a §4 o §6 de este documento. Si dudas si algo califica, favorece agregarlo en el Log.
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
## 2. Decisiones estructurales — viven en el Charter Log
> La cronología de decisiones vive en V | CHARTER LOG, sección 2 (CHARTER-LOG:DECISIONS). Se consulta bajo demanda; CLAUDE/MAIN la carga junto con este Charter antes de evaluar un ticket CHARTER. Las decisiones con efecto operativo se reflejan como reglas en §4 y §6 y como estado en §7.
---
## 3. CHARTER:FAILURES — Fracasos conocidos (para no repetir)
> Si estás a punto de proponer algo que se parece a uno de estos, revisa primero
por qué no funcionó.
### 3.1 CHARTER:FAILURES-001 — Reaparición de Hard Blocks ya corregidos
El bloqueo de Aéropostale se levantó explícitamente el 2026-08-07, pero volvió a aparecer como exclusión en
al menos un brief operativo posterior, obligando a corregirlo dos veces. Causa
raíz: la corrección vivía solo en una entrada de Changelog y en la memoria de
la sesión que la hizo, sin quedar consolidada en un lugar que un agente nuevo
consultara por default. Mitigación: este Charter, más la disciplina de que los Hard Blocks reales se consultan siempre en Layer_1/config/hard_blocks.json (fuente ejecutable única), nunca se re-derivan de briefs históricos. 
### 3.2 CHARTER:FAILURES-002 — Patrón de reporte optimista (ticket RT-1, Bug Tracker)
Al menos tres episodios documentados donde un agente (Devin en dos ocasiones, Gemini en una)
reportó una corrección o un push/commit como aplicado cuando la verificación
independiente mostró que no lo estaba, o que el bug de sintaxis seguía presente.
Mitigación adoptada: ningún reporte de éxito de otro agente se acepta sin
re-fetch/re-verificación independiente contra la fuente real (repo, Notion,
Terminal) — este es hoy un principio explícito de ways-of-working, nacido
directamente de este patrón repetido.
### 3.3 CHARTER:FAILURES-003 — Cédula de Reconciliación fabricada (primera ronda de auditoría externa, 2026-09-24/25)
Ver CHARTER-LOG:DECISIONS-006 para el detalle. El fracaso no fue solo el dato
fabricado — fue que tenía forma de rigor (citas, tablas, formato profesional)
suficiente para casi pasar sin objeción. Mitigación: todo contrato de sesión con
un agente delegado exige ahora URL/cita verificable específica, no solo nombre
de fuente, y prohíbe explícitamente declarar "PASS"/"Verificado" sin evidencia
citable.
### 3.4 CHARTER:FAILURES-004 — Loop de auto-rechazo QA↔CV-B (detectado 2026-08-19)
Un CV-B generado por Claude fue rechazado por la propia skill de QA de Claude en el mismo turno, y
"corregido" sin cambio real verificable — un ciclo de generar-rechazar-simular
corrección sin progreso genuino. Mitigación estructural: se separó
explícitamente la responsabilidad de QA (audita, no corrige) de CV-B
(construye, no se auto-audita en el mismo turno) — la regeneración tras un
NO-GO requiere invocación explícita separada del operador, nunca colapsarse
en el mismo turno por inercia conversacional.
### 3.5 CHARTER:FAILURES-005 — Documentación que describe código ya retirado
Patrón recurrente, no un incidente único: layer_1_run.py y consolidate_duplicates.py permanecieron
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
### 3.6 CHARTER:FAILURES-006 — CANONICAL declarado sin fila de registro (Career Sites v2.0)
Un release del Change Log (2026-10-06) declaró CANONICAL el contrato PromptA-v2.0+careersites. La verificación del 2026-10-07 encontró la página en CANDIDATE y sin fila en el Prompt Contract Registry, y el operador confirmó que no había promovido nada; el Acta y el brief de Workday repetían el CANONICAL. Causa raíz: los ejecutores reportaron la promoción y el Change Log la registró sin auditarla. Mitigación: solo el operador promueve; una promoción existe únicamente si hay fila con los 11 campos obligatorios y un SHA ligado a su ruta, verificable en git; un Change Log registra, no prueba estado.
---
## 4. CHARTER:NON-NEGOTIABLES — Reglas no negociables (consolidadas)
> Estas reglas ya existen dispersas en KERNEL, MANUAL, System Prompt y
ways-of-working. Se consolidan aquí con su razón de ser — la fuente normativa
exacta sigue siendo el documento original; este Charter no la reemplaza, la
contextualiza.
### 4.1 CHARTER:NON-NEGOTIABLES-001 — Python es dueño exclusivo de los campos Class B
La IA nunca los calcula ni los escribe directamente. Por qué: decisiones reproducibles y auditables
no pueden depender de juicio de lenguaje natural turno a turno.
### 4.2 CHARTER:NON-NEGOTIABLES-002 — APROBAR_WRITE obligatorio antes de cualquier escritura a Notion
Un token de autorización del operador es obligatorio antes de cualquier escritura a Notion; DRY RUN se presenta primero salvo que el operador lo salte explícitamente. Tokens válidos (mayúsculas y minúsculas indistintas; puntuación final tolerada): APROBAR_WRITE · APROBAR · SÍ (con acento) · YEP. Tokens eliminados, no autorizan (RAI-03): OK · GO · YES. Solo el operador emite tokens; ningún agente se auto-autoriza ni interpreta silencio o entusiasmo como autorización. El alcance de cada token (por ejemplo, campos Class A) lo define KERNEL:SCH-APPROVE. Por qué: Mau es el único responsable final de cada cambio en producción; ninguna automatización debe erosionar ese control, y la lista vive aquí porque el Charter es lo que todo agente carga al arrancar.
### 4.3 CHARTER:NON-NEGOTIABLES-003 — Ningún reporte de éxito se acepta sin re-fetch/verificación independiente
Ningún reporte de éxito de otro agente se acepta sin re-fetch/verificación independiente contra la fuente real. Por qué: patrón RT-1 (CHARTER:FAILURES-002) — confiar en la narración sin verificar produjo errores reales repetidos.
### 4.4 CHARTER:NON-NEGOTIABLES-004 — Serial declarado por el operador se adopta sin verificación adicional
Un serial de handoff declarado por el operador en el mismo turno se adopta sin verificación adicional, bajo ninguna circunstancia. Por qué: Mau es operador y transportista único de todo handoff — cuestionar su declaración
directa es trabajo redundante, no cautela (Serial Authority v2, CHARTER-LOG:DECISIONS-003).
### 4.5 CHARTER:NON-NEGOTIABLES-005 — Diagnóstico externo = hipótesis hasta verificación 1:1
Todo diagnóstico externo (auditoría, hallazgo, "Cédula") se trata como hipótesis hasta verificación 1:1 contra fuente primaria real — nunca como verdad operativa por su sola forma o aparente rigor. Por qué: incidente de Cédula fabricada (CHARTER:FAILURES-003).
### 4.6 CHARTER:NON-NEGOTIABLES-006 — Ningún agente delegado resuelve discrepancias por su cuenta; reporta y espera decisión humana
Ningún agente delegado resuelve por su cuenta una discrepancia entre documentos o entre documento y código — la reporta con ambas fuentes citadas y espera decisión humana. Por qué: la resolución unilateral de
ambigüedad es precisamente lo que generó el patrón de "corrección" ficticia
en el loop QA↔CV-B y en la Cédula fabricada.
### 4.7 CHARTER:NON-NEGOTIABLES-007 — tracker_flow.is_mutable() única fuente de verdad de mutabilidad
tracker_flow.is_mutable() es la única fuente de verdad sobre mutabilidad de un registro; ningún guard alternativo debe reimplementar ese criterio.
### 4.8 CHARTER:NON-NEGOTIABLES-008 — Graph/Backlinks solo observabilidad, nunca capa operativa
Graph/Backlinks son artefactos de observabilidad derivados, nunca una capa operativa de resolución o archivado. Por qué: decisión de producto explícita (CHARTER-LOG:DECISIONS-005) — VANTAGE archiva por movimiento de fila, no por grafo.
### 4.9 CHARTER:NON-NEGOTIABLES-009 — VM_Scope binario (Alto/Bajo), sin "Medio"
VM_Scope es binario (Alto/Bajo) — no existe, ni debe reintroducirse, un valor "Medio" ni terminología de escaparatismo.
### 4.10 CHARTER:NON-NEGOTIABLES-010 — Hard Blocks se consultan contra hard_blocks.json vigente
Hard Blocks reales (empleadores que no recontratan) se consultan siempre contra Layer_1/config/hard_blocks.json vigente (fuente ejecutable única, ver CHARTER-LOG:DECISIONS-013); el Manual §10 es su redacción derivada. Nunca se re-derivan de un brief, auditoría o conversación histórica. Por qué: fracaso conocido de reaparición de Aéropostale (CHARTER:FAILURES-001) y cadena circular de autoridad Charter → KERNEL → JSON → Manual, verificada el 2026-10-06/07.
### 4.11 CHARTER:NON-NEGOTIABLES-011 — Sin ubicaciones improvisadas
Los agentes no crean carpetas, ramas ni rutas fuera de la estructura canónica del proyecto. Los entregables de sesión van en el chat o en ubicaciones que ya existen; si hace falta una nueva, se pide al operador antes de crearla. Por qué: la acumulación de carpetas y ramas ad hoc es el mismo patrón de drift que este proyecto corrige (ver CHARTER-LOG:DECISIONS-016).
---
## 5. CHARTER:MILESTONES — Trayectoria esperada — hitos de fase, no lista de tareas
> Esta sección no duplica el Plan de Trabajo (Notion) — ese vive de tareas que
cambian de estado todos los días. Aquí van los hitos que casi nunca
cambian aunque las tareas debajo sí, con su definición explícita de "hecho".
Si te encuentras editando esta sección cada sesión, algo se filtró aquí que
debería vivir en el Plan de Trabajo, no aquí.
Hito 1 — cerrado (2026-09-29). Las 10 preguntas recurrentes sobre Track Beta ya están respondidas y no se reabren desde cero con ningún agente. Consulta CHARTER-LOG:MILESTONES-001 antes de reabrir una.
### 5.2 CHARTER:MILESTONES-002 — Hito 2 — T2.1 (Redacción KERNEL v10) en paralelo a Track Beta
Definición de hecho: T2.1 no espera a que Track Beta cierre al
100% si las piezas de Track Beta que bloquean secciones específicas del KERNEL
(la cifra de documentos fundacionales, la jerarquía de dedup L1>L2>L3, el
scope real de vsync_doc.py) ya están resueltas — lo cual, a la fecha de este
Charter, ya lo están (ver Changelog v9.22.17-19). El resto de Track Beta
(scripts de Layer 4/Dashboard/Raycast) no bloquea el arranque de la redacción
normativa central de KERNEL.
### 5.3 CHARTER:MILESTONES-003 — Hito 3 — MANUAL v10 corre en paralelo a KERNEL v10
Una vez que ambos comparten la misma base de hechos verificados (Cédula de Reconciliación +
output de Track Beta cerrado). No se redacta MANUAL v10 sobre una cifra o un
estado de script que Track Beta aún no ha confirmado.
### 5.4 CHARTER:MILESTONES-004 — Hito 4 — Fase 3 (sync + verificación cruzada) solo con drafts v10 completos
Fase 3 (sync + verificación cruzada) solo arranca cuando KERNEL v10 y MANUAL v10 tienen draft completo, no parches incrementales sobre v9.22.x. Definición de hecho: vsync corre sobre el árbol v10 completo una sola vez,
no sobre fragmentos sueltos — evitar el patrón de esta semana donde cada
parche puntual requería su propio ciclo de vversions --sync / vgit.
### 5.5 CHARTER:MILESTONES-005 — Hito 5 — Este Charter se actualiza en cada decisión estructural mayor
No solo en checkpoints de fase. Ver CHARTER-LOG:DECISIONS para el criterio de qué
califica como "estructural mayor" vs. "fix, no anotar aquí".
### 5.6 CHARTER:MILESTONES-006 — Hito 6 — Repositorio consolidado en main
Definición de hecho: main es la única rama (local y remota) y el historial de las ramas retiradas vive en tags archive/<rama>; la suite de Layer_1 pasa completa; el trabajo de consolidación de Arena (T3, T5 y T6) está fusionado; y ningún documento describe una rama, un script o una carpeta ya retirados (ver CHARTER-LOG:DECISIONS-016). El estado de las tareas vive en el Plan de Trabajo, no aquí.
### 5.7 CHARTER:MILESTONES-007 — Hito 7 — Primera producción controlada de Workday
Definición de hecho: (a) dry-run E2E de Workday/Chanel con feed real y sin escrituras a Notion (✅ 2026-10-11: 11 registros, 10 CLEAN y 1 BLOCKED en la fase de ingesta, 0 escrituras); (b) bloqueo de roles de tienda aplicado en la ingesta (CHARTER-LOG:DECISIONS-017; ✅ 2026-10-15: patrones T11 presentes en main, profile_fit.py en 622b4f5; cableado a la ingesta según Mistral, no verificado por MAIN); (c) un primer --apply acotado, con re-fetch en Notion que confirme los registros creados. LinkedIn queda fuera de este hito: su adquisición corre en el host del agente (ajuste de navegador de la app), no desde el repo.
---
## 6. CHARTER:CONTINUITY — Protocolo de continuidad entre agentes y sesiones
Gatekeeping de cambios al propio Charter (decisión 2026-09-30 — ver CHARTER-LOG:DECISIONS-011 y SP:BOOTLOADER-002). Ningún agente, bajo ninguna vía, escribe
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
ticket sin haber fetcheado el Charter y el Charter Log completos en esa misma sesión — el rol
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
Actualización 2026-10-11: el prefijo CHARTER ya está dado de alta en resolver_registry_v2.json (línea 54, verificado por MAIN con git grep); registry_seed.json no es un registry documental (pertenece al flujo de CV/Figma) y no recibe el alta (Arena, T9). Que vload --route CHARTER:... resuelva está reportado por Arena y MAIN no lo re-ejecutó: confirmarlo con una corrida antes de ofrecerlo como fallback; mientras tanto, el fallback real sigue siendo que el operador adjunte el archivo.
Acceso a skills. Rige la copia del .md de la skill que el operador adjunta en el turno en que se usa (ver CHARTER-LOG:DECISIONS-015); ningún agente asume que su copia residente está al día ni lo reporta como riesgo.
Qué hace un agente delegado al recibir este Charter. Lo trata como
contexto de lectura obligatoria, no como fuente a re-verificar línea por
línea en cada sesión — pero sí puede y debe señalar si alguna instrucción
recibida en su contrato de sesión parece contradecir una Regla No Negociable
(sección 4) o repetir un patrón de Fracaso Conocido (sección 3). Señalarlo
no es exceder su mandato — es exactamente el tipo de "válvula de escape" que
ya rige el protocolo de convivencia con IA de este proyecto.
---
## 7. CHARTER:STATUS — Estado de este documento
Estado vigente (actualizado 2026-10-15 por CLAUDE/MAIN con APROBAR_WRITE del operador). El Charter se partió en este documento y en V | CHARTER LOG; el relato fechado de actualizaciones y verificaciones anteriores vive en CHARTER-LOG:UPDATES. Las propiedades Versión y Fecha de actualización de este documento no se tocaron. Decisiones con efecto operativo vigente, cuyo texto íntegro está en el Log:
- Sync, backup y vl3 se ejecutan a mano bajo demanda; los cron jobs están deshabilitados (CHARTER-LOG:DECISIONS-014).
- Los roles de tienda sin alcance estratégico o multi-tienda se bloquean en la ingesta de Layer 1; implementado en main (CHARTER-LOG:DECISIONS-017).
- El Interview Simulator es una herramienta derivada, sin autoridad sobre fuentes canónicas (CHARTER-LOG:DECISIONS-018).
- Citas al KERNEL: KERNEL:GATE-DECISION-012 y KERNEL:DEDUP-LAYER-UPGRADE se reemplazaron por KERNEL:GATE-MUTABILITY (heading 06.12, confirmado en el KERNEL vivo el 2026-10-15). KERNEL:CVR-NOCLASSB (heading 11.2) y BRIEF:CROSS-DEPENDENCIES-001 siguen citables.
Pendiente de decisión del operador:
- Nombre final del documento y su ubicación jerárquica exacta en Notion.
- Si este Charter reemplaza o convive con el "Tablero" actual de la página TRACKER MANUAL & KERNEL.
- Qué régimen de versión rige: el Kernel (14.3) incluye CHARTER en vversions --length y en vsync_doc, mientras que SP:SYNC-RULE no lo lista entre los documentos de la Regla de Versión Única. El Charter Log hereda el régimen que se decida.
- Actualización de la plantilla de contrato de sesión estándar para incluir una línea de "lee primero V | PROJECT CHARTER" en todo contrato futuro (sección 6).
- Texto de CHARTER-LOG:DECISIONS-019 (retiro de Graph; número reservado).
Pendientes abiertos tras la actualización del 2026-10-15:
- Alta del prefijo CHARTER-LOG: en resolver_registry_v2.json, generate_census.py, verify_versions.py (DOC_KEYS) y vsync_doc.py (DOCS); regenerar ID Census con los IDs de ambos documentos (el Log introduce 23 IDs: 19 migrados desde CHARTER: y 4 nuevos).
- vversions --length marcará ATENCIÓN REQUERIDA en el Charter por la caída esperada de bloques: verificar y actualizar el baseline.
- Actualizar SP:BOOTLOADER (alcance, paso 2, -001 y -004) y Project Instructions según el protocolo de optimización del bootstrap; después, KERNEL:OPS-BOOT y la matriz de ruteo 04.5.
- La fila 3b del Hito 1 (wrapper vdoc.py con 9 etiquetas, en el Log) cambia cuando se fusione la rama de Arena.
- El Corpus Bloque 06 del operador sigue listando Dockers y Aéropostale como bloqueados.
- La resolución de vload --route CHARTER:... y CHARTER-LOG:... sigue sin re-ejecutarse (sección 6).
- Siguen apareciendo commits auto-sync en main posteriores a CHARTER-LOG:DECISIONS-014; el proceso que los genera no está identificado (reporte de Hermes del 2026-10-16, no verificado por MAIN).
