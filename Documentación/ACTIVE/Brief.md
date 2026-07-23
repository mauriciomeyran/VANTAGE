# V | DOCUMENT NAVIGATION BRIEF 

## ID:BRIEF:001
# 1. Propósito y Alcance
## Propósito
Este documento define el contrato oficial de navegación documental de VANTAGE.
Su función es determinar qué documento constituye la Fuente Única de Verdad (SSOT) para cada tipo de conocimiento y establecer la ruta mínima necesaria para recuperar información de forma consistente.
No reemplaza la documentación fundacional; la orquesta.
---
## Alcance
Este documento responde exclusivamente a l2as siguientes preguntas:
- ¿Dónde debe buscarse una determinada información?
- ¿Qué documento tiene autoridad sobre cada dominio?
- ¿Cuál es la profundidad mínima de verificación requerida?
- ¿Qué dependencias documentales deben respetarse?
---
## Fuera de Alcance
Este documento no:
- define contratos operativos (Kernel);
- describe procedimientos paso a paso (Manual);
- documenta el perfil profesional (Career Canon);
- mantiene el inventario de IDs (ID Census);
- registra historial de cambios (Change Log).
---
## ID: BRIEF:002
# 2. Document Authority Matrix

Esta matriz define el documento autorizado para cada dominio del sistema.
| Necesidad | Documento SSOT | Rol |
| --- | --- | --- |
| Arquitectura del sistema | Kernel | Contrato normativo |
| Operación diaria | Manual | Procedimientos |
| Perfil profesional | Career Canon | Identidad profesional |
| Gobernanza IA | System Prompt | Bootstrap |
| Navegación documental | Document Navigation Brief | Routing |
| Inventario documental | Master Index | Descubrimiento |
| IDs canónicos | ID Census | Observabilidad Runtime |
| Alias y nomenclatura | Aliases | Normalización |
| Historial | Change Log | Auditoría |
| Esquemas | Tracker Schema | Modelo de datos |
---
## ID: BRIEF:003
# 3. Ecosistema Documental
Cada documento tiene una única responsabilidad.
| Documento | Responsabilidad |
| --- | --- |
| Navigation Brief | Decide qué documento consultar |
| Master Index | Localiza documentos |
| ID Census | Resuelve entidades e IDs |
| Kernel | Define contratos e invariantes |
| Manual | Explica cómo operar |
| Career Canon | Define el posicionamiento profesional |
| System Prompt | Gobierna el comportamiento de la IA |
| Change Log | Conserva la historia del sistema |
| Aliases | Normaliza terminología |
Ningún documento debe duplicar la responsabilidad de otro.
---
## ID: BRIEF:004
# 4. Navigation Contracts
## Consulta Arquitectónica
Destino: Kernel
Se utiliza para:
- contratos
- reglas
- arquitectura
- ownership
- triggers
- gates
- filosofía
---
## Consulta Operativa
Destino: Manual
Se utiliza para:
- procedimientos
- flujos
- ejecución
- troubleshooting
- operación diaria
---
## Consulta Profesional
Destino: Career Canon
Se utiliza para:
- CV
- posicionamiento
- experiencia
- narrativa profesional
- skeletons
- output contract
---
## Consulta Documental
Destino: Master Index
Se utiliza para:
- localizar documentos
- descubrir documentación
- verificar estructura documental
---
## Consulta de IDs
Destino: ID Census
Se utiliza para:
- validar IDs
- resolver referencias
- localizar secciones
- verificar namespaces
- auditoría documental
---
## Consulta Histórica
Destino: Change Log
Se utiliza para:
- conocer cuándo ocurrió un cambio
- reconstruir decisiones
- auditoría
---
## ID: BRIEF:005
# 5. Domain Architecture
## Housekeeping
Responsabilidad
Mantener la integridad documental y eliminar drift.
Produce
- deduplicación
- archivado
- limpieza
- sincronización
Depende de
Ningún dominio.
Es la base del sistema.
---
## Core Assets
Responsabilidad
Mantener sincronizados todos los activos fundacionales.
Incluye:
- Runtime
- Version Check
- Census
- ACTIVE
- Git
- Bootloader
---
## Discovery
Responsabilidad
Captura y consolidación de oportunidades.
Incluye:
- L1
- L2
- L3
Produce información para Gate Logic.
---
## Gate Logic
Responsabilidad
Evaluación determinista del pipeline.
Incluye:
- URL Gate
- Gate Decision
- Next Action
- Recovery RT-1
---
## CV Pipeline
Responsabilidad
Producción documental posterior al Gate.
Incluye:
- CV-A
- CV-B
- QA
- Handoff
- Export
---
## ID: BRIEF:006
# 6. Verification Depth Contract
Toda modificación debe respetar el nivel mínimo de validación requerido.
| Nivel | Alcance |
| --- | --- |
| L0 | Consulta Read-Only |
| L1 | Verificación documental |
| L2 | Validación Runtime |
| L3 | Validación Pipeline |
| L4 | Validación integral del sistema |
Cada operación debe utilizar el menor nivel posible compatible con su riesgo.
---
## ID: BRIEF:007
# 7. Cross-Document Dependencies
La siguiente matriz define las dependencias estructurales entre los documentos fundacionales.
Una dependencia indica que un cambio en el documento de origen puede afectar la consistencia de uno o más documentos relacionados y requiere una evaluación explícita antes de cerrar la operación.
| Cambio en | Evaluar | Acción mínima requerida |
| --- | --- | --- |
| Kernel | Manual, Navigation Brief, System Prompt | Revisar contratos afectados |
| Manual | Navigation Brief | Verificar que la navegación siga siendo válida |
| Career Canon | CV Skills, Output Contracts | Validar consistencia del pipeline CV |
| Tracker Schema | Runtime, Manual | Verificar compatibilidad del esquema |
| Aliases | Runtime, Resolver Registry | Regenerar índices si aplica |
| Runtime | ID Census | Regenerar artefactos de observabilidad |
| IDs | ID Census | Ejecutar vcensus |
| Bootstrap / System Prompt | Navigation Brief | Validar estrategia de recuperación |
| Estructura documental | Master Index | Actualizar inventario |
---
### 7.1 Impact Assessment Contract
Toda modificación que afecte un documento con dependencias registradas deberá generar una Evaluación de Impacto (Impact Assessment) antes del cierre de la operación.
Como mínimo, la evaluación responderá:
- ¿Qué documentos pueden verse afectados?
- ¿Qué contratos deben verificarse?
- ¿Es necesaria una actualización documental?
- ¿Debe regenerarse algún artefacto de Runtime?
- ¿Debe ejecutarse una validación adicional?
- ¿Se requiere sincronización (vsync_doc, vversions, vcensus)?
---
### 7.2 Mandatory Change Reporting
Cuando una evaluación de impacto determine que existe afectación sobre otro documento o artefacto del sistema, será obligatorio registrar dicha afectación en el Change Log.
El registro deberá incluir, como mínimo:
- Documento modificado.
- Documentos potencialmente afectados.
- Tipo de impacto (Normativo, Operativo, Runtime o Navegación).
- Acción correctiva ejecutada.
- Estado final de la validación.
---
### 7.3 Closure Gate
Una modificación estructural no podrá considerarse cerrada hasta que se cumplan todas las acciones derivadas de su evaluación de impacto.
Si alguna dependencia permanece pendiente de validación, la operación conservará el estado Pending Validation y no deberá marcarse como completamente sincronizada.
---
## ID: BRIEF:008
# 8. Maintenance Contract
Toda modificación estructural debe responder afirmativamente las siguientes preguntas antes de aprobarse.
## Autoridad
- ¿Cuál es el SSOT del cambio?
## Contrato
- ¿Se modifica un contrato existente?
## IDs
- ¿Se crea, modifica o elimina algún ID?
## Runtime
- ¿Debe regenerarse el ID Census?
- ¿Debe ejecutarse Version Check?
## Auditoría
- ¿Debe actualizarse el Change Log?
## Navegación
- ¿Debe actualizarse este Navigation Brief?
---
## ID: BRIEF:009
# 9. Navigation Decision Tree
```plain text
Solicitud

↓

Clasificar tipo de conocimiento

↓

¿Arquitectura?
        → Kernel

¿Operación?
        → Manual

¿Perfil Profesional?
        → Career Canon

¿Documento?
        → Master Index

¿ID o Entidad?
        → ID Census

¿Historial?
        → Change Log

↓

Responder
```
---
## ID: BRIEF:010
# 10. Principios de Navegación
1. Existe una única Fuente de Verdad para cada tipo de conocimiento.
1. La navegación siempre precede a la recuperación de contenido.
1. Se consulta el documento con menor alcance que pueda responder correctamente la solicitud.
1. El Runtime resuelve entidades; no sustituye la documentación.
1. El ID Census pertenece a la capa de observabilidad (L0) y nunca actúa como documentación normativa.
1. El Kernel gobierna contratos; el Manual gobierna procedimientos.
1. El Navigation Brief gobierna exclusivamente la navegación entre documentos.
---
## ID: BRIEF:011
# 11. Resultado Esperado
Al finalizar la lectura de este documento, cualquier operador o sistema de IA debe ser capaz de:
- identificar la fuente de verdad correcta para cualquier consulta;
- navegar el ecosistema documental sin ambigüedad;
- conocer la profundidad mínima de validación requerida;
- entender las dependencias entre documentos;
- minimizar consultas innecesarias y evitar duplicación de conocimiento.
