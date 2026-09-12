# V | CHANGELOG

Tipo: [FIX] [DOC] [OPS]
Documento modificado: vantage-present-handoff/SKILL.md, vantage-session-open/SKILL.md, vantage-session-close/SKILL.md (repo GitHub, v1.0.0→v1.1.0→v1.2.0 en dos pasadas) · tracker_flow.py (repo, fix de bug real) · Tasks Tracker (Notion, 1 alta) · KERNEL:HANDOFF-SERIAL (Notion, pendiente de edición manual por el operador — markdown entregado, no aplicado por MCP en esta sesión).
Documentos potencialmente afectados: SP:SKILL-VERSION-PIN (tabla en v1.0.0 para los 3 skills de sesión, desalineada contra el repo tras este cambio — pendiente de sync, no ejecutado en esta sesión).
Tipo de impacto: Normativo + Operativo — cierre de una fricción de diseño real detectada esta sesión: instancias receptoras de handoff re-verificaban exhaustivamente estado ya reportado por el operador (incluyendo el propio serial del handoff), consumiendo tokens de forma desproporcionada sin mejorar la fiabilidad, dado que Mau es operador único y transportista único de todo handoff en el sistema.
Causa raíz: El diseño original de vantage-present-handoff/vantage-session-close no distinguía entre "estado no verificado" y "estado declarado por la única fuente de autoridad posible". Sin un campo de evidencia adjunta ni una regla explícita de adopción, cada instancia por defecto trataba todo como no verificado — incluyendo la resolución de serial, que en la práctica depende de vías (MCP allocate_vantage_serial, Terminal allocate_vantage_serial.py next) confirmadas no funcionales en esta sesión.
Acción correctiva ejecutada:
1. S4-EVIDENCE + Regla de Adopción (v1.1.0): los 3 skills de sesión (vantage-present-handoff, vantage-session-close — ambos con sección S4 — y bump de versión en vantage-session-open, que no emite S4) reciben una subsección S4-EVIDENCE obligatoria para afirmaciones verificables (comando exacto + output crudo, sin campo de timestamp propio — el orden queda implícito por ser Mau el único transportista de handoffs) y una Regla de Adopción: la instancia receptora de un handoff con S4-EVIDENCE completo adopta esa evidencia sin re-ejecutar verificación, salvo contradicción explícita del operador o inconsistencia interna de la evidencia misma.
1. Serial Authority v2 (v1.2.0, extensión del mismo patch): la ruta MCP/HTTP para resolución de serial se elimina del diseño (no se degrada a fallback — se retira por no ser funcional en la práctica operativa). vserial vía Terminal se conserva como la única vía canónica para obtener un serial nuevo. Nueva Prioridad 0: serial declarado directamente por el operador en el mismo turno, autoridad máxima, adoptado sin verificación adicional bajo ninguna circunstancia. Si el operador no declara uno, debe obtenerse mediante vserial vía Terminal; si esa ruta no está disponible, declarar HANDOFF_SERIAL_UNAVAILABLE y detener la emisión — nunca inventar ni interpolar por continuidad secuencial con el handoff anterior.
1. Fix real de bug en tracker_flow.py: run_outcome_status_sync() (F13b) llamaba a notion_client.databases.query() — endpoint inexistente en la versión instalada de notion-client contra API version 2025-09-03, donde ese método se movió a client.data_sources.query(). Confirmado mediante introspección directa del cliente (dir(client.databases) → sin query; dir(client.data_sources) → con query). Corregido cuerpo de la función y docstring (parámetro database_id debe recibir el DATA SOURCE ID 442938be-fc42-828f-b72e-076818d65a5b, no el DATABASE ID 596938be-fc42-836b-aea7-814a1491bd47 — no intercambiables). Verificado con py_compile tras el fix.
1. DRY RUN real ejecutado contra producción (Terminal, operador): script standalone reutilizando normalize_record() de tracker_flow.py sobre las 24 filas del Tracker vía data_sources.query() — checked=24, would_sync=0, skipped=24, sin invocar apply_status_sync_writeback en ningún momento. Consistente con verificación independiente previa (sync_status_contratado.py, mismo resultado: 0 filas con Outcome=Contratado pendientes de reconciliar — el campo Outcome simplemente no está poblado en ninguna fila real hoy, no es un bug de query).
1. Investigación de campo Holding: snapshot previo (HO-000042) reportaba 13 filas pendientes de limpieza; verificación directa contra Notion (24 filas totales) encontró 16 filas con Holding no vacío: 13 = Investigar (placeholder), 1 = Genérico (placeholder distinto, tratamiento sin confirmar), 2 = datos reales de holding corporativo (Nike Inc., LVMH) que NO deben tratarse como placeholder. Task creado en Tasks Tracker (3d8938be-fc42-81dc-8ada-c7afec89bec9) documentando el desglose completo y bloqueando ejecución de limpieza hasta que el operador confirme criterio de tratamiento para cada categoría.
1. Verificación de integridad post-migración de schema Status (heredado de HO-000042, cerrado esta sesión con evidencia real): query directa de las 24 filas del Tracker confirmó 0 filas con Status vacío/huérfano tras el rename de opciones (Target→Objetivo, REVIEW_NEEDED→Por Revisar, etc.) — sin pérdida de datos.
IDs afectados: Alta de 1 registro operativo (Tasks Tracker, Holding). Ninguna alta/baja de ID canónico en Kernel/Manual/SP/Canon en esta pasada — el cambio de KERNEL:HANDOFF-SERIAL (Notion) queda como edición manual pendiente del operador, markdown ya entregado en sesión, no ejecutado vía MCP.
Estado final de la validación: Fix de tracker_flow.py verificado con py_compile + DRY RUN real contra Notion producción (evidencia cruda capturada). Patch de los 3 skills de sesión verificado vía git diff en cada pasada, commit confirmado por el operador (vgit, no re-verificado con git log en esta sesión — adoptado por declaración directa del operador bajo la nueva Regla de Adopción que este mismo changelog documenta). Pendiente explícito: sync de SP:SKILL-VERSION-PIN (Notion) a v1.2.0 para los 3 skills de sesión, y aplicación manual del markdown de KERNEL:HANDOFF-SERIAL v2 por el operador. Sin DRY RUN de Changelog presentado ni aprobación por turno adicional, por instrucción explícita del operador (optimización de tokens) — version bump y esta entrada ejecutados en una sola pasada.
---
Tipo: [OPS] [SYNC]
Alcance: script_hash_baseline.json (8 hashes), skill_hash_baseline.json (5 hashes), bodies Notion de vantage-present-handoff / vantage-session-open / vantage-session-close; Script Library + Skill Library altas previas de assets sync.
Contexto: Cierre de content-drift detectado vs baselines locales. Bodies de session skills alineados a disco (v1.1.0 S4-EVIDENCE + Regla de Adopción). Baselines de hash actualizados en clone local (requiere commit/push del operador para persistir en repo remoto).
Cambios:
1. Script content-drift cerrado: allocate_vantage_serial.py, feed_processor.py, layer_1_run.py, layer_3_mail.py, mcp_vantage_serial_server.py, open-figma-template.sh, profile_evolution.py, verify_versions.py.
1. Skill content-drift cerrado en baseline: vantage-cv-a, vantage-cv-b, present-handoff, session-close, session-open (bodies Notion actualizados para las 3 session skills).
1. Version bump CHANGELOG → v9.21.55.
Pendientes: commit/push baselines en repo; bodies completos de vantage-cv-a/cv-b en Notion (archivos >10k, omitidos por tamaño en esta pasada MCP); 10 scripts missing-on-disk del baseline histórico (legacy) sin acción.
IDs afectados: Ninguno.
Estado: APLICADO — baselines locales + bodies session skills + propiedad Versión CHANGELOG.
---
Tipo: [REVERT] [CODE]
Alcance: layer_3_mail.py, layer_3.env
Contexto:
- Revert intencional de la migración v9.21.52 (Groq → Gemini): retorno a Groq como proveedor de LLM.
- Razón del revert: Inestabilidad y errores de esquema/deprecación en el endpoint de Gemini. Se migró a Groq aprovechando el modelo qwen/qwen3.8-27b para garantizar JSON estructurado estricto.
Cambios observados:
1. Variables de configuración restablecidas a nomenclatura GROQ_* (GROQ_API_KEY, GROQ_MODEL, GROQ_MIN_DELAY_SEC).
1. Actualización de modelo activo a qwen/qwen3.8-27b y ajuste del delay entre peticiones a 5.0s para evitar el rate limit por Tokens Per Minute (TPM).
1. Implementación de sanitización ASCII en el cuerpo del correo previo al payload JSON para eliminar errores 400 Bad Request por caracteres de control.
Estado: APLICADO Y VALIDADO EN PRODUCCIÓN — Pipeline ejecutado con éxito en la rama main (🏁 VL3 terminó — no quedan correos pendientes), procesando y deduplicando alertas de empleo en Notion sin errores de red o sintaxis.
IDs afectados: Ninguno (refactor de código de backend/pipeline).
Pendientes:
- Ejecutar commit y push a GitHub (vgit) para sincronizar el estado local verificado con el repositorio remoto.
---
Tipo: [OPS]
Documento modificado: Ninguno en Notion — auditoría de 15 PDFs finales del batch (Beyond, Confidencial GVM, Confidencial Gte.Nacional VM, Eurokor, GDC Inmobiliaria, H&M Junior Retail Designer, IKEA, Inditex, Intimissimi, Juguetron, SARELLY, ServiciosAndrei/Moygo, Tendam, Walmart, ZaraHome).
Documentos potencialmente afectados: Ninguno — trabajo de auditoría de entregables, no de especificación normativa.
Tipo de impacto: Operativo — checklist canónico de 7 ítems (vantage-qa v9.17.0) corrido sobre los 15 PDFs sin HANDOFF de CV-A disponible para ninguno (Ítem 3 = N/A en los 15). Ítem 7 (Anti-cloning) evaluado por comparación cruzada entre los 15 archivos del batch.
Acción ejecutada:
1. Verificación de orden cronológico C01→C05 intacto en los 15.
1. Hard Blocks confirmados PASS en los 15 — L'Oréal/Levi's/Palacio de Hierro presentes solo como historial (C01/C03/C05), ninguna vacante target pertenece a esas marcas.
1. Certificaciones (CERT01/CERT02) y email canónico verificados sin desviación en los 15.
1. Métricas (+43%/+18%/-74%/-33%/17 punch-list/21 reportes/270+ PDV/6 países) verificadas sin inflación ni redondeo.
1. Sin [PENDING DATA] visible en ningún PDF.
1. Anti-cloning: pares con headers de título similares (Beyond/GDC; IKEA/Juguetron) verificados con bullets de Experience reescritos con ángulo distinto — ningún par supera 80% de coincidencia verbatim.
IDs afectados: Ninguno (auditoría de contenido, sin alta/baja de ID canónico).
Estado final de la validación: 15/15 PDFs con veredicto GO. Corrección de conteo aplicada en la misma sesión (reporte inicial erróneo de "14/14" corregido a 15/15 tras verificación directa del conteo de archivos). Sin DRY RUN presentado ni aprobación por turno adicional, por instrucción explícita del operador (optimización de tokens) — version bump y esta entrada ejecutados en una sola pasada.
---
Tipo: [MIGRATION] [CODE]
Alcance: layer_3_mail.py (migración completa Groq → Gemini) + layer_3.env
Contexto:
- Problema de backoff exponencial (12s → 1,217s) en retries de Groq, causando tiempos de espera no viables.
- Cuota insuficiente de Groq incluso tras implementar pre-filtrado y backoff cap.
- Investigación de proveedores alternativos determinó que Gemini Flash-Lite ofrece mejor free tier (15-30 RPM vs ~10 RPM de Groq) y OpenAI-compatibility.
Cambios ejecutados:
1. Migración de proveedor: Reemplazo completo de cliente Groq por cliente Gemini:
- extract_jobs_with_groq() → extract_jobs_with_gemini()
- _groq_throttle() → _gemini_throttle()
- _groq_wait_seconds() → _gemini_wait_seconds()
- GroqFatalError → GeminiFatalError
- Endpoint: https://api.groq.com/openai/v1/chat/completions → https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
- Payload format: OpenAI-style → Gemini native (contents/generationConfig)
1. Configuración renombrada (layer_3.env):
- GROQ_API_KEY → GEMINI_API_KEY (usando key existente en .env principal)
- GROQ_MODEL → GEMINI_MODEL (gemini-3.5-flash-lite)
- GROQ_MIN_DELAY_SEC → GEMINI_MIN_DELAY_SEC (8s, reducido de 12s)
- GROQ_MAX_RETRIES → GEMINI_MAX_RETRIES (3)
- GROQ_MAX_BACKOFF_SEC → GEMINI_MAX_BACKOFF_SEC (20s, reducido de 30s)
- GROQ_MAX_EMAILS_PER_RUN → GEMINI_MAX_EMAILS_PER_RUN (5)
- GROQ_BODY_MAX_CHARS → GEMINI_BODY_MAX_CHARS
1. Pre-filtrado preservado: Función should_skip_groq() → should_skip_gemini() mantiene lógica de filtrado de correos sin indicadores de vacante.
1. VM keywords preservadas: _VM_KEYWORDS expandido con equivalentes españoles (exhibición visual, escaparatismo, coordinador visual, etc.) implementados en sesión previa.
Validación:
- Pipeline ejecutado sin intervención manual en correos de prueba.
- Sin rate limits observados con Gemini (vs persistentes con Groq).
- Latencia mejorada: 8s delay vs 12s anterior.
- Modelo gemini-3.5-flash-lite estable y disponible.
Pendientes post-escritura:
- Ejecutar vversions --sync para propagar cambios a documentos fundacionales.
- Monitorear cuota de Gemini (usos/hora) tras despliegue.
- Considerar backup provider (DeepSeek) como fallback si se requiere mayor throughput.
IDs afectados: Ninguno (migración de proveedor sin alta/baja de ID canónico — no dispara KERNEL:CENSUS-SYNC Regla 1).
---
Tipo: [DOC] [INFRA]
Documento modificado: V | SYSTEM PROMPT (§01.1 SP:BOOTLOADER-001 — agregado Hermes a Familia MCP-Notion) · .hermes.md (repo local, new file)
Documentos potencialmente afectados: Ninguno — extensión de alcance de familia de agente existente, sin impacto en contratos documentales.
Tipo de impacto: Operativo + Normativo — cierre de gap de capacidad de agente: Hermes ahora consume el manifiesto VANTAGE vía notion-fetch igual que el resto de la Familia MCP-Notion, y declara identidad HERMES/DEFAULT conforme al Contrato de Sesión y Handoff (SP:BOOTLOADER-002, v1.0).
Acción correctiva ejecutada:
1. V | SYSTEM PROMPT §01.1 — línea "Familia MCP-Notion (Claude, Cursor, Devin, ChatGPT, Littlebird, Grok, Hermes)" actualizada para incluir a Hermes en el registro de familias con acceso a notion-fetch.
1. .hermes.md creado en raíz del repo VANTAGE — instrucciones persistentes de proyecto que Hermes carga automáticamente al iniciar sesión: identidad declarada (agent.family: HERMES, agent.instance: DEFAULT, identity.confirmation_mode: CONFIGURED_NO_REPROMPT), protocolo de Bootloader (BOOTLOADING... → notion-fetch SYSTEM PROMPT + ID CENSUS → BOOTLOADED), y restricciones operativas generales alineadas al Kernel.
1. Sin DRY RUN presentado ni APROBAR_WRITE por turno adicional, por instrucción explícita del operador (optimización de tokens) — version bump y esta entrada ejecutados en una sola pasada.
IDs afectados: Ninguno (sin alta/baja de ID canónico — extensión de texto existente en SP:BOOTLOADER-001 + nuevo archivo .hermes.md en repo local).
Estado final de la validación: .hermes.md verificado en disco (ruta: /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/.hermes.md). SP:BOOTLOADER-001 actualizado en Notion. Sin Census pendiente (sin alta/baja de ID). 23:50 CDMX.
Handoff de referencia: HO-000045 (emitido en esta sesión, este es el handoff de cierre de la sesión de Bootloader Hermes).
---
Tipo: [OPS] [FIX]
Documento modificado: 4 archivos CV-B (Eurokor VM Skincare, ServiciosAndreiMoygo, Tendam, Multicont Visual Merchandiser — repo local) · 3 archivos CV-B EN (SARELLY, HM Retail Designer, HM Junior Retail Designer — bold/métrica, nunca auditados antes) · saneamiento_reports/triajev3.py (3 correcciones de raíz) · V | Saneamiento CV-B.md (reporte de estado, v1.0→v1.2)
Documentos potencialmente afectados: Ninguno en Kernel/Manual/SP/Canon — continuación operativa del saneamiento retroactivo iniciado en v9.21.49, sin cambios normativos.
Tipo de impacto: Operativo — cierre de los 4 pendientes explícitos dejados en el handoff HO-000036 (Gates 6/7 en los 3 CV-B EN, Auditoría de Identidad Figma nunca ejecutada, revisión sistemática de doble-bold, persistencia de "Flagship Store" en FRASES_EXENTAS).
Acción correctiva ejecutada:
1. 4 archivos ALTA restantes del batch de contenido (Eurokor, ServiciosAndreiMoygo, Tendam, Multicont VM) corregidos: idioma mixto real (bloques íntegros en inglés traducidos con redacción diferenciada entre archivos por Anti-cloning Guard sobre el mismo hecho de Canon C03), tiempo verbal (L'Oréal en pretérito, rol cerrado), métricas sin bold, nombre/empresas/roles/períodos sin bold+italic.
1. Los 3 CV-B EN (SARELLY, HM Retail Designer, HM Junior Retail Designer) — nunca auditados en ninguna sesión previa porque el script de triaje los excluye por diseño (falso positivo de idioma). Auditoría manual: SARELLY ya tenía formato correcto, solo 5 métricas sin bold; HM Retail Designer y HM Junior Retail Designer tenían el mismo bug de formato que los archivos ES (nombre/empresas/roles/períodos sin bold+italic) más 3 métricas sin bold cada uno. Los 3 corregidos.
1. triaje_v3.py — 3 causas raíz corregidas (no parches por archivo): (a) FRASES_EXENTAS sin "Flagship Store", causaba falsos positivos de IDIOMA_MIXTO_REAL en 11+ archivos; (b) limpiar_exentas() case-sensitive, "flagship store" en minúsculas no quedaba exento (2 casos: ServiciosAndreiMoygo, GDC); (c) PRESENTE_PROHIBIDO marcaba "Desarrollo" como verbo en frases nominales ("Desarrollo de Tienda", "Desarrollo y apertura de...", "Desarrollo de Equipos") — 6 falsos positivos en 2 archivos. Corregido con lookahead/lookbehind. Re-corrida post-fix: 14/14 archivos ES → LIMPIO, confirmado en terminal por el operador.
1. Auditoría de Identidad Figma — nunca ejecutada en ninguna iniciativa anterior sobre ninguno de los 18 archivos. Ejecutada esta sesión contra registry_seed.json (68 nodos), validada adicionalmente contra un CV-B de control ya confirmado funcional en Figma (Dior/Christian Dior LVMH v2, 100% idéntico al registry). Resultado: 18/18 archivos con conteo 68/68, membership idéntico, orden de secuencia idéntico al control, 0 duplicados de figma_text_id.
1. Verificación sistemática (no muestral) de doble-bold (****) y bold asimétrico en los 18 archivos: 0 casos.
IDs afectados: Ninguno (sin alta/baja de ID canónico — trabajo de contenido/formato/auditoría estructural, no de especificación normativa).
Estado final de la validación: 18/18 CV-B del Batch Septiembre completos: idioma + tiempo verbal + Gates 6/7 + Identidad Figma. Los 4 pendientes obligatorios de HO-000036 quedan cerrados sin excepción. Sin próximos pasos obligatorios pendientes de esta iniciativa. Write-back de V | Saneamiento CV-B.md verificado vía re-fetch en vivo tras escritura. Sin DRY RUN presentado ni aprobación por turno adicional, por instrucción explícita del operador (optimización de tokens) — version bump y esta entrada ejecutados en una sola pasada.
Handoff de referencia: HO-000036 (recibido al inicio de sesión, superseded por el cierre documentado aquí).
---
Tipo: [OPS] [FIX]
Documento modificado: 18 archivos CV-B (repo local, carpeta Batch septiembre/CV-B) · 1 archivo CV-A (GDC, campo Próximo paso resuelto) · V | Saneamiento CV-B.md (reporte de estado, actualizado)
Documentos potencialmente afectados: Ninguno en Kernel/Manual/SP/Canon — trabajo de saneamiento de contenido, no de especificación normativa (esa parte ya se cerró en v9.21.48 con el rewrite de vantage-cv-b a v10.2.0).
Tipo de impacto: Operativo — barrido retroactivo sobre los 18 CV-B generados antes del rewrite v10.2.0, para llevarlos al estándar de Auto-Verificación Mecánica recién especificado. Ejecutado vía Desktop Commander con acceso directo al filesystem local.
Hallazgo sistémico adicional (caso GDC): el HANDOFF-A de GDC Inmobiliaria declaraba explícitamente Próximo paso: REVISIÓN HUMANA REQUERIDA antes de CV-B — por discrepancia de VM_Scope y flag de integridad de registro AGREGADOR_STATUS_401 (posible vacante caída). El CV-B se había generado de todos modos, saltando ese gate de bloqueo explícito. Operador confirmó en esta sesión: (1) vacante sigue activa, (2) autoriza continuar pese a desalineación de seniority. Corregido después de esa autorización, no antes.
Acción correctiva ejecutada:
1. Triaje mecánico v1→v3: primeras dos versiones del script de detección tenían falsos positivos severos (nombres propios de campaña, términos técnicos de industria como "Store Design"/"Flagship Store", títulos oficiales de certificación). v3 excluye estos patrones y es la versión confiable para continuidad.
1. Idioma y tiempo verbal: 15/18 archivos corregidos o confirmados limpios tras inspección de contexto real (no solo conteo de regex). 3/18 (HM Junior Retail Designer, HM Retail Designer, SARELLY) confirmados EN legítimo vía HANDOFF.idioma=EN — excluidos del saneamiento de idioma.
1. Gates 6/7 (bold de métricas cuantificadas, formato estructural de secciones/años): aplicados sobre 14 archivos en español vía reemplazo con regex (cifras tipo "N años", "N países", "N+ puntos de venta", etc. envueltas en bold; títulos de sección en bold; años de formación en italic). Pendiente explícito: los 3 archivos EN no fueron auditados en Gates 6/7 — el script usado es español-only: no se corrió verificación de bold/italic en inglés sobre ellos.
1. GDC: CV-A actualizado con decisión de operador documentada en el campo Próximo paso; CV-B corregido de idioma (perfil 2:10 y Skills 2:15/2:16, que estaban en inglés corrido pese a HANDOFF.idioma=ES).
IDs afectados: Ninguno (sin alta/baja de ID canónico — trabajo sobre archivos de contenido, no sobre documentos fundacionales).
Estado final de la validación: 15/18 CV-B completos (idioma + tiempo verbal + Gates 6/7). 3/18 (los EN) pendientes de auditoría de Gates 6/7 en inglés. Auditoría de Identidad Figma (membership/secuencia/conteo contra registry_seed.json) NO ejecutada en esta iniciativa sobre ninguno de los 18 — próximo paso obligatorio antes de dar cualquier archivo por listo para Figma Sync. Reporte de estado completo entregado como handoff a instancias siguientes en V | Saneamiento CV-B.md. Sin DRY RUN presentado ni aprobación por turno adicional, por instrucción explícita del operador (optimización de tokens, sesión en rango 77-82% de uso) — version bump y esta entrada ejecutados en una sola pasada.
Handoff de cierre de esta sesión: HO-000036.
---
Tipo: [DOC] [OPS] [FIX]
Documento modificado: V | SYSTEM PROMPT (nueva §01.3 SP:SKILL-VERSION-PIN) · vantage-cv-b/SKILL.md (GitHub, rewrite v10.2.0) · vantage-session-open/SKILL.md, vantage-session-close/SKILL.md, vantage-present-handoff/SKILL.md (GitHub, versionado inicial v1.0.0)
Documentos potencialmente afectados: Ninguno adicional en Kernel/Manual/Canon.
Tipo de impacto: Normativo + Operativo — cierre de dos gaps distintos detectados en batch de corrección de CV-B "Confidencial VM Manager" (2026-09-05): (1) la Verificación Pre-Entrega de vantage-cv-b v10.1.1 era autodeclarada por el mismo turno que generaba el contenido, sin evidencia mecánica — 8 rondas de corrección post-entrega detectadas por el operador (punchline-titular no solicitado, tiempo verbal incorrecto en rol cerrado, idioma mixto en 2 slots, bold ausente en keywords/métricas/secciones/empresas/tagline/licenciatura, italic ausente en años de formación) pese a que el skill ya prohibía explícitamente la mayoría; (2) agentes que resuelven skills desde memoria de contexto en vez de fetch en vivo carecían de una referencia de versión mínima aceptable, exponiendo al sistema a generación con skills obsoletos sin mecanismo de detección.
Causa raíz: No fue vacío de especificación — el skill v10.1.1 ya cubría la mayoría de las reglas violadas. El fallo fue de auditoría autodeclarada sin evidencia mecánica: el mismo turno que redactaba el contenido declaraba "PASS" en el footer sin correr un chequeo real contra el texto ya escrito.
Acción correctiva ejecutada:
1. vantage-cv-b/SKILL.md — rewrite completo v10.2.0: la "Verificación Pre-Entrega" narrada de v10.1.1 se reemplaza por "Auto-Verificación Mecánica Obligatoria", 10 gates con criterio de PASS/FAIL basado en patrón detectable (membership/secuencia heredados + nuevos: Gate 3 idioma vs stopwords, Gate 4 tiempo verbal por rol con fecha de cierre, Gate 5 elegibilidad de etiqueta bold en Experience con umbral de alerta 40%, Gate 6 bold obligatorio en toda cifra cuantificada, Gate 7 formato estructural consolidado tagline/secciones/empresas/licenciatura/años). Nueva Regla de Elegibilidad de Etiqueta: la etiqueta temática en bold en Experience es síntesis de 2+ hechos dispares, nunca titular decorativo por defecto — distinto del comportamiento obligatorio de bold en categorías de Skills, que se mantiene sin cambio. Nueva regla de tiempo verbal: pretérito uniforme en todo rol con fecha de cierre, presente solo en rol activo. Footer ahora reporta los 10 gates individualmente, no un "PASS" genérico.
1. V | SYSTEM PROMPT — nueva subsección §01.3 SP:SKILL-VERSION-PIN, inmediatamente después de 01.2 (Identidad de Agente y Serial de Handoff): tabla de versión vigente para los 6 skills de generación de contenido/sesión. Regla dura: ningún agente genera con versión inferior a la listada; si no puede confirmar coincidencia contra su memoria, declara SKILL_VERSION_UNVERIFIED y detiene hasta hacer fetch. Mantenimiento: la tabla se actualiza en el mismo turno que sube la versión de cualquier skill listado.
1. vantage-session-open/SKILL.md, vantage-session-close/SKILL.md, vantage-present-handoff/SKILL.md — las tres carecían de versionado numérico, generando ambigüedad en la tabla de pin. Versionado inicial v1.0.0 (2026-09-05) agregado a cada una vía patch quirúrgico (línea de ID Canónico + Trigger + Versión de alineación insertada tras el título), sin tocar el resto del contenido operativo.
IDs afectados: Alta de 1 ID nuevo (SP:SKILL-VERSION-PIN, §01.3). Sin baja de IDs.
Estado final de la validación: Write-Back Verification pendiente de re-fetch post-escritura (siguiente paso inmediato en esta misma sesión). Census pendiente de actualización por el alta de SP:SKILL-VERSION-PIN. Sin DRY RUN presentado ni aprobación por turno adicional, por instrucción explícita del operador (optimización de tokens, sesión al 72% de uso) — version bump y esta entrada ejecutados en una sola pasada junto con la escritura de contenido.
---
Tipo: [DOC] [OPS]
Documento modificado: V | KERNEL (§12.2 KERNEL:CV-PIPELINE-002) · V | MANUAL (§12.1 MANUAL:FIGMA-SYNC-DIAGNOSTIC) · vantage-cv-b/SKILL.md (GitHub, v10.1.1)
Documentos potencialmente afectados: Ninguno adicional — sin referencias cruzadas a estos nodos en System Prompt/Career Canon que requieran actualización.
Tipo de impacto: Normativo + Operativo — cierre del gap detectado en el batch "Plan Saneamiento": un conteo correcto de tags (68/68) no garantiza identidad estructural; un schema heredado puede conservar la cantidad esperada mientras usa IDs obsoletos, slots fusionados o slots desplazados.
Acción correctiva ejecutada:
1. KERNEL:CV-PIPELINE-002 (12.2) — agregada "Auditoría de Registry Membership" inmediatamente después de la auditoría de conteo: cada figma_text_id del output debe pertenecer literalmente al registry_seed.json vigente y cada ID del registry debe aparecer una sola vez en el output. Un conteo coincidente no prueba identidad ni secuencia; si membership, unicidad o correspondencia exacta contra el Skeleton falla, abortar y re-mapear antes de declarar PASS_FOR_FIGMA.
1. MANUAL:FIGMA-SYNC-DIAGNOSTIC (12.1) — agregado "Guard de identidad estructural" al inicio de la matriz de errores: un conteo de tags coincidente no valida el archivo; comparar ID por ID contra el registry vigente y contra la secuencia del Golden Skeleton; un schema heredado puede mantener la cantidad total mientras usa IDs obsoletos o representa slots fusionados/desplazados.
1. vantage-cv-b/SKILL.md (GitHub) — rewrite completo v10.1.1: consolidación de secciones duplicadas (Language Policy, cv_b_eligible), eliminación de redundancias (verbos de ownership repetidos), sección nueva "Auditoría de identidad" que unifica los cuatro criterios (conteo, membership, unicidad, secuencia) y los integra como gate obligatorio antes de declarar PASS_FOR_FIGMA. Sin cambios de lógica operativa — solo consolidación y alineación explícita con los dos parches de Notion.
IDs afectados: Ninguno (sin alta/baja de ID canónico — ambas ediciones de Notion extienden nodos existentes; el SKILL.md no introduce nuevos IDs).
Estado final de la validación: Write-Back Verification PASS — confirmado vía re-fetch en vivo de KERNEL y MANUAL post-escritura, ambos parches presentes sin mismatch. Archivo vantage-cv-b_SKILL.md generado y entregado al operador para reemplazo local + vgit + sync. Census no aplica (sin altas/bajas de ID). Sin DRY RUN presentado por instrucción explícita del operador (optimización de tokens).
---
Tipo: [DOC] [OPS] [FIX]
Documento modificado: 2 archivos CV-B (GitHub, Beyond y Multicont Supervisor — fix estructural de tags)
Documentos potencialmente afectados: Ninguno en Notion — hallazgo y corrección viven en el repo GitHub, fuera de documentos fundacionales.
Tipo de impacto: Normativo + Operativo — cierre definitivo de la auditoría del batch de 17 CV-B iniciada en v9.21.45, mediante verificación nodo-por-nodo contra registry_seed.json que v9.21.45 no había ejecutado (esa entrada verificó contenido/idioma/claims vía grep quirúrgico, no estructura completa de tags).
Causa raíz nueva detectada (post v9.21.45): 2 de los 17 archivos (Beyond, Multicont Supervisor) usaban un tag schema obsoleto — rol+período fusionados en un solo tag (2:23, 2:33, 2:40, 2:47), header de Palacio de Hierro con ID inexistente (2:54), Palacio de Hierro colapsado a un solo rol en vez de los dos que documenta CANON:EXPERIENCE-005/CANON:CAREER-TIMELINE (Asesor 2012–2014 + Coordinador 2014–2017), y Educación/Cursos fusionados. Ninguno de estos 16 IDs existe en registry_seed.json (68 nodos vigentes) — root cause: ambos archivos heredaron su schema de un export anterior a la actualización del registry, y el rebuild de contenido de sesión previa (traducción ES) preservó esa estructura sin saber que estaba obsoleta.
Acción correctiva ejecutada:
1. Verificación cruzada contra un archivo de referencia que sí pasa en Figma (Dior, aportado por el operador) — confirmó que el schema correcto separa rol/período en tags independientes y usa IDs de la serie 10:xxx/4:xxx para experiencia posterior a Dockers.
1. Confirmado contra el Golden Skeleton documentado en CANON:OUTPUT-CONTRACT-002 y contra registry_seed.json — ambos idénticos, tercer punto de verificación independiente.
1. Reconstrucción completa de Beyond y Multicont Supervisor con schema correcto (contacto en tags separados 8:56–8:63, rol/período separados, Palacio de Hierro dividido en 2 roles con bullets redistribuidos, Educación/Cursos en tags individuales) — contenido preexistente conservado, solo estructura corregida.
1. Auditoría final exhaustiva: script de verificación nodo-por-nodo corrido contra los 17 archivos activos (+ Walmart, archivado) tras git pull de cada fix — match exacto de 68/68 IDs contra el registry, sin duplicados ni IDs extraños, en los 17.
IDs afectados: Ninguno en Notion. Repo GitHub: 2 archivos CV-B con estructura de tags corregida.
Estado final de la validación: Write-Back Verification PASS — confirmado vía git pull post-vgit del operador + re-ejecución del script de auditoría, 17/17 archivos activos en PASS estructural exacto (68/68 nodos, 0 faltantes, 0 extras, 0 duplicados). Walmart confirmado sin tocar (ARCHIVE_DO_NOT_REBUILD). Corrige y cierra con evidencia dura el estado "16/17 PASS_FOR_FIGMA" declarado en v9.21.45, que no había sido verificado a nivel de nodo. Sin DRY RUN presentado ni aprobación por turno, por instrucción explícita del operador (optimización de tokens) — version bump y esta entrada ejecutados en una sola pasada.
Estado del batch: 17/17 PASS_STRUCTURAL (validación de tags/registry). Pendiente aparte, no cubierto por esta entrada: verificación de renderizado real en Figma por archivo (competencia del operador) y checklist de 7 ítems de vantage-qa sobre los PDF ya renderizados.
---
Tipo: [DOC] [OPS]
Documento modificado: REPORTE DE NO CONFORMIDADES (Notion, FASE 2 reemplazada v2→v3) · vantage-cv-b/SKILL.md (GitHub, R2.1 aplicado) · 9 archivos CV-B (GitHub, rebuild de contenido/idioma/tags)
Documentos potencialmente afectados: Ninguno adicional en Kernel/Manual/Canon — el batch vive en la carpeta de trabajo "Plan Saneamiento" del repo, fuera de los documentos fundacionales.
Tipo de impacto: Normativo + Operativo — cierre completo de la auditoría de los 17 pares CV-A/CV-B iniciada esta sesión contra REPORTE DE NO CONFORMIDADES (fuente: Perplexity/Sonnet 5 Thinking). Verificación cruzada por grep quirúrgico contra el repo real en cada pasada, sin lectura completa de archivo.
Acción correctiva ejecutada:
1. Auditoría inicial (grep quirúrgico + registry_seed.json): 3 falsos positivos del reporte original corregidos (tag 2:28| válido; Eurokor N3 ya tenía override de operador; conteo de archivos corregido 16→17); 1 causa raíz nueva detectada (mismatch de idioma en Multicont Supervisor); 1 bug de plantilla nuevo detectado (placeholder figma_text_id sin ID en IKEA/Inditex/Zara Home); 3 archivos con downgrade de severidad tras verificación directa (Confidencial Nacional/Gerente, Multicont VM).
1. Entregables generados en sandbox y presentados como descargables (Contrato de Sesión HO-000031, Brief de Findings, Plan de Saneamiento v2) para inyección manual del operador en Notion, por optimización de tokens.
1. Operador/instancias siguientes ejecutaron el rebuild: 7 archivos con sustituciones de claims (S1.1/S1.4/S1.5/S1.6), 2 archivos con traducción completa a ES (Beyond, Multicont Supervisor), fix del gate TAG_SCHEMA en vantage-cv-b/SKILL.md (R2.1 — ahora valida solo el ID entre paréntesis), Intimissimi resuelto con ángulo de gestión estratégica regional (decisión de operador posterior a esta sesión, distinta a la documentada originalmente) + fix de Anti-cloning Guard en 4 slots.
1. Verificación de cierre (esta pasada): git pull + grep de conteo exacto contra los 13 archivos con acción — 0 ocurrencias de tag placeholder roto en los 13; footer de Andrei Moygo confirmado completo con 6/6 campos PASS (corrección a nota previa de "sin footer"); nota de Tendam "pendiente vgit" confirmada obsoleta (ya pusheado, commit 06fc125, 2026-09-03 21:25 CDMX).
1. FASE 2 de REPORTE DE NO CONFORMIDADES (Notion) actualizada a v3 con tabla de estado final y hallazgos de verificación de cierre.
IDs afectados: Ninguno en Notion (sin alta/baja de ID canónico). Repo GitHub: 9 archivos CV-B con contenido corregido, 1 SKILL.md con gate corregido.
Estado final de la validación: Write-Back Verification PASS — confirmado vía re-fetch en vivo de REPORTE DE NO CONFORMIDADES post-escritura, ambas ediciones de Fase 2 presentes sin mismatch. 13/17 archivos del batch confirmados PASS_FOR_FIGMA mediante verificación directa contra el repo (no contra notas de sesión previas). 3/17 reclasificados OUT_OF_SCOPE_CV_PIPELINE (bloqueados por falta de PDF renderizado en Figma). 1/17 (Walmart) permanece ARCHIVE_DO_NOT_REBUILD, sin tocar. Sin DRY RUN presentado por instrucción explícita del operador (optimización de tokens). Version bump y esta entrada ejecutados en una sola pasada por la misma instrucción.
Autorización de handoff a Figma: los 13 archivos PASS_FOR_FIGMA quedan autorizados para Figma Sync — verificación de contenido, tags y footer completa contra el repo real.
Corrección post-cierre (mismo día, antes de vversions): los 3 archivos reclasificados OUT_OF_SCOPE_CV_PIPELINE (Confidencial Nacional, Confidencial Gerente, Multicont VM) fueron etiquetados por error — esa etiqueta implicaba bloqueo de entrada a Figma, cuando en realidad su contenido ya estaba verificado limpio (downgrade confirmado en la misma auditoría) y el único pendiente real es el checklist de 7 ítems de vantage-qa, que se ejecuta sobre el PDF ya renderizado, no como condición de entrada a Figma. Corregidos a PASS_FOR_FIGMA en REPORTE DE NO CONFORMIDADES (Notion). Estado final del batch: 16/17 PASS_FOR_FIGMA, 1/17 ARCHIVE_DO_NOT_REBUILD (Walmart). Operador procede a Figma Sync de los 16 y regresa con los 16 PDF para correr vantage-qa.
---
Tipo: [DOC]
Documento modificado: V | MANUAL (§04 MANUAL:SETUP Paso 2, §12 MANUAL:TROUBLESHOOTING)
Documentos potencialmente afectados: Ninguno adicional — Kernel, System Prompt y Career Canon no referencian este contrato; MANUAL:SCRIPT-GLOSSARY-L1 (§22.1) queda con gap paralelo (web_ui.py no documentado), no incluido en este parche.
Tipo de impacto: Normativo — cierre de gap detectado entre el README de Scout Layer 1 (candidato a reemplazo) y el Manual, que no documentaba instalación desde cero (venv, pip install, Playwright, .env) ni el modo de ejecución vía UI web.
Acción correctiva ejecutada:
1. MANUAL:SETUP (Paso 2) — agregada ruta de primera instalación (python3 -m venv .venv, pip install -r requirements.txt, playwright install chromium, cp .env.example .env) junto a la ruta existente de reinstalación; agregada mención del modo de ejecución vía UI web (web_ui.py/Flask) como alterno a la CLI.
1. MANUAL:TROUBLESHOOTING (§12) — agregada entrada "Scraping L1 No Corre (Playwright)" con 5 síntomas/soluciones (dependencias, Playwright, API key, timeout BROWSER_MAX_STEPS, rate limiting), en el mismo formato plano que las entradas vecinas.
IDs afectados: Ninguno (sin alta/baja de ID canónico — ambas ediciones extienden nodos existentes, MANUAL:SETUP y MANUAL:TROUBLESHOOTING, por decisión explícita de invisibilidad estructural sobre alta de subsección nueva).
Estado final de la validación: Write-Back Verification PASS — confirmado vía re-fetch en vivo de ambos nodos, contenido presente sin mismatch. Census no aplica (sin altas/bajas de ID). DRY RUN presentado y aprobado explícitamente por el operador (yep) antes de escritura.
---
Tipo: [DOC]
Documento modificado: V | KERNEL (§14, KERNEL:NAMING-CONVENTION)
Documentos potencialmente afectados: Ninguno adicional — sin referencias cruzadas a esta sección en Manual/SP/Canon que requieran actualización.
Tipo de impacto: Normativo — aclaración de regla existente, no alta de concepto nuevo.
Causa raíz: La prosa de "Reglas de normalización" no explicitaba que Marca_normalizada y Vacante_normalizada son secuencias de palabras separadas por guión bajo entre sí — el ejemplo ya lo mostraba correctamente (Gucci_VM_Coordinator_LATAM) pero la regla en prosa dejaba ambigüedad, causando drift observado en esta sesión (stems generados como palabras concatenadas sin separador interno).
Acción correctiva ejecutada: Agregada regla explícita en §14 — "Cada componente del stem (Marca_normalizada, Vacante_normalizada) se separa internamente por guión bajo entre cada palabra — no es un solo token concatenado. El guión bajo es el único separador, tanto entre componentes del stem como dentro de cada componente." Reutilización de ID existente (KERNEL:NAMING-CONVENTION), sin alta de subsección nueva.
IDs afectados: Ninguno (sin alta/baja de ID canónico — extensión de nodo existente).
Estado final de la validación: Write-Back Verification PASS — confirmado vía re-fetch en vivo de §14, regla nueva presente sin mismatch. Census no aplica (sin altas/bajas de ID). Sin DRY RUN presentado en el mismo turno de aprobación por instrucción explícita del operador (yep).
---
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
