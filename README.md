# VANTAGE

Sistema operativo personal para Discovery, evaluación determinista y producción documental de oportunidades profesionales.

VANTAGE integra Runtime, Discovery, Gate Logic, CV Pipeline, Version Control e infraestructura documental alrededor de una fuente de verdad canona.

> **README = mapa operativo.**
>
> El detalle normativo vive en Kernel, Manual, Brief, Aliases y Career Canon.

---

## 01 · SESSION CYCLE

Inicio del entorno:

```bash
start
```

Bootstrap del contexto operativo:

```bash
vversions --bootstrap
```

Sincronizacin de versiones:

```bash
vversions --sync
```

Modos adicionales de `vversions`:

```bash
vversions --scripts
vversions --skills
vversions --length
vversions --update-baseline
```

`--update-baseline` requiere `--length` y confirmacin explcita cuando corresponde. El catlogo completo de modos y sus contratos vive en `Aliases.md`.

**Bootstrap ≠ Session Open.**

El Bootstrap carga contexto operativo. La apertura formal del Session Ledger es una operacin distinta y opt-in.

---

## 02 · SYSTEM MAP

```text
                              VANTAGE
                                 │
                         ┌───────┴───────┐
                         │   L0 Runtime  │
                         └───────┬───────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
             L1                 L2                 L3
          Active             Strategic           Passive
          Search              Search              Intake
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                            Gate Logic
                                 │
                           CV Pipeline
                                 │
                       CV-A → Handoff → CV-B
                                 │
                                QA
                                 │
                              Export
                                 │
              L4 · Version Control & Infrastructure
              └── documentacin · Git · sync · assets
```

L1, L2 y L3 alimentan Discovery y convergen antes de Gate Logic.

**L4 es infraestructura transversal, no una etapa de bsqueda.**

---

## 03 · L0 · VANTAGE RUNTIME

L0 es la capa de Runtime, consulta y observabilidad.

### Consulta y contexto

```text
vload
vask
vquery
vresolve
vcontext
```

### Estado y observabilidad

```text
vstatus
vcensus
vdigest
vsource
```

### Versiones e integridad

```text
vversions
vlength
vupdatebaseline
```

### Runtime / navegacin

```text
vtrig
vgolden
vcheat
vscope
vdataflow
vrouting
```

### Control

```text
vunlock
vlock
```

Runtime, Version Check y Census son mecanismos de observabilidad y consulta ReadOnly sobre la infraestructura documental.

---

## 04 · L1 / L2 · DISCOVERY

Discovery captura y consolida oportunidades para alimentar Gate Logic.

### L1 · Active Search

```text
vl1
vl1status
vl1analytics
vl1batch
vl1recovery
vl1profile
vl1feed
vl1backfill
vl1app
```

L1 procesa el resultado consolidado del ciclo de Active Recon y lo incorpora al Tracker mediante el pipeline correspondiente.

### L2 · Strategic Search

L2 opera como bsqueda estratgica semanal.

```text
Gemini · You.com · Grok
          ↓
     Perplexity
 Consolidation & Dedup
          ↓
         FEED
          ↓
   feed_processor.py
          ↓
       Notion
```

Su funcin es reconciliar resultados de mltiples motores y reducir ruido antes de alimentar el pipeline.

### Assembly

```text
vassemble
```

Materializa los prompts semanales desde la Prompt Library para los motores de Discovery.

---

## 05 · L3 · PASSIVE INTAKE

```text
vl3
vl3app
```

Flujo:

```text
Gmail / .Jobs
      ↓
Layer 3
      ↓
Notion
      ↓
Pipeline
```

L3 no deduplica por s mismo. Entra al punto de convergencia del pipeline, donde se resuelve la jerarqua entre capas.

---

## 06 · GATE LOGIC

Gate Logic realiza la evaluacin determinista del pipeline.

```text
URL Gate
   ↓
Gate Decision
   ↓
Next Action
   ↓
Recovery RT-1
```

Gate Logic es independiente de Discovery y del CV Pipeline.

CV-A comienza despus del Gate y no sustituye ni reevala la decisin determinista del pipeline.

---

## 07 · L4 · VERSION CONTROL & DOCUMENTATION

L4 es infraestructura transversal para control de versiones, sincronizacin documental y mantenimiento de activos.

### Git

```text
vgit
```

Sincroniza el repositorio mediante el mecanismo de Git de VANTAGE.

### Documentacin

```text
vdoc
vsync-doc
vhyperlinks
```

- `vdoc` → orquesta la sincronizacin documental.
- `vsync-doc` → motor de sincronizacin documento por documento.
- `vhyperlinks` → aplica cross-references sobre bloques de Notion preservando sus IDs.

### Skills / Runtime

```text
vtriggers
```

Mantiene `skills/triggers.json`, utilizado por el Bootloader para resolver triggers y cargar skills.

### Utilities

```text
vserial
vsum
vprint
cleancaches
```

- `vserial` → genera seriales de handoff.
- `vsum` → utilidad de gestin de transcripts / Inbox.
- `vprint` → lista oportunidades con `Gate_Decision = CREATE`.
- `cleancaches` → limpia cachs regenerables.

---

## 08 · DASHBOARD

```text
vd
vdapp
```

Se utiliza como herramienta operativa de recuperacin para oportunidades bloqueadas.

---

## 09 · CV PIPELINE

```text
Gate
 ↓
CV-A
 ↓
Handoff
 ↓
CV-B
 ↓
QA
 ↓
Export
```

### CV-A · Analysis

```text
CV-A [URL/JD]
```

CV-A:

- procesa la vacante;
- extrae keywords y gaps;
- analiza tono de marca;
- determina Positioning Mode N1–N4;
- genera el HANDOFF para CV-B.

Algoritmo de Positioning Mode:

```text
keywords
   ↓
mapping
   ↓
counting
   ↓
tie-break
```

El HANDOFF requiere `positioning_rationale`.

### CV-B · Construction

```text
CV-B [HANDOFF]
```

CV-B construye el CV final a partir del HANDOFF de CV-A.

**No ejecutar CV-B sin HANDOFF previo.**

### QA

```text
QA [PDF]
```

QA audita el PDF terminado.

Si QA falla:

```text
QA FAIL
   ↓
correcciones
   ↓
invocacin separada de CV-B
```

QA y regeneracin de CV-B son operaciones separadas.

### Preparacin mecnica

```text
adapt_tracker_export.py
cv_a_batch_agent.py
cv_a_prep.py
```

No tienen alias corto.

Este tooling prepara scaffolds, pero no sustituye CV-A. Cada vacante sigue requiriendo su propia invocacin de CV-A.

---

## 10 · DEDUP & OPPORTUNITIES

```text
vdedup
vopport
```

Auditora manual:

```bash
./scripts/dedup_audit.sh
```

Jerarqua de convergencia:

```text
L1 > L2 > L3
      ↓
punto nico de convergencia
```

L1 y L3 no realizan la deduplicacin final de forma independiente.

---

## 11 · WEEKLY OPERATING RHYTHM

### Lunes

```text
L1 + L2
  ↓
Feed
  ↓
Pipeline
```

### Martes

```text
vd
```

### Mircoles

```text
CV-A
 ↓
CV-B
 ↓
QA
```

### Jueves

```bash
~/vantage_pipeline.sh
```

### Viernes

```bash
~/vantage_pipeline.sh analytics
```

La cadencia organiza el trabajo del operador. No constituye una condicin adicional del Gate.

---

## 12 · DOCUMENTATION MAP

| Fuente | Consulta para |
|---|---|
| `System Prompt.md` | gobernanza y comportamiento de la IA |
| `Kernel.md` | arquitectura, contratos e invariantes |
| `Manual.md` | procedimientos, operacin y troubleshooting |
| `Brief.md` | navegacin y routing documental |
| `Master Index` | localizar documentos y estructura documental |
| `ID Census` | resolver IDs, referencias y namespaces |
| `Aliases.md` | interfaz Terminal y nomenclatura |
| `Career Canon.md` | verdad y posicionamiento profesional |
| `Change Log.md` | historial y auditora de cambios |
| `Changelog Archivo.md` | historial archivado |

Regla prctica:

```text
Dnde est?
      ↓
Brief / Master Index

Qu regla aplica?
      ↓
Kernel

Cmo se ejecuta?
      ↓
Manual

Qu comando uso?
      ↓
Aliases

Qu dato profesional es cannico?
      ↓
Career Canon

Qu ID / referencia?
      ↓
ID Census

Cundo cambi?
      ↓
Change Log
```

El Brief establece explcitamente esta separacin de responsabilidades.

---

## 13 · REPOSITORY MAP

```text
VANTAGE/
├── Documentacin/
│   └── ACTIVE/
├── Layer_1/
├── Layer_3/
├── Layer_4/
├── Dashboard/
├── skills/
├── tools/
├── src/
├── tests/
├── Raycast/
├── templates/
├── prompts/
├── state/
├── handoffs/
└── Archive/
```

| Directorio | Funcin |
|---|---|
| `Documentacin/ACTIVE/` | documentacin normativa activa |
| `Layer_1/` | implementacin L1 |
| `Layer_3/` | implementacin L3 |
| `Layer_4/` | infraestructura L4 |
| `skills/` | skills + triggers |
| `Dashboard/` | recovery tooling |
| `Archive/` | material histrico |

---

## 14 · CORE RULES

- Notion es la fuente documental de verdad.
- Kernel define contratos y arquitectura.
- Manual define procedimientos.
- Brief define navegacin.
- Aliases define la interfaz Terminal.
- Career Canon define la verdad profesional.
- Runtime observa, consulta y resuelve.
- Census verifica referencias e IDs.
- Version Check verifica versiones e integridad documental.
- Discovery alimenta Gate Logic.
- Gate precede al CV Pipeline.
- CV-A y CV-B son sesiones separadas.
- QA y regeneracin de CV-B son operaciones separadas.
- L4 mantiene infraestructura, no constituye una etapa de bsqueda.

---

## 15 · WHEN IN DOUBT

Primero verificar:

```text
vstatus
vversions
vcensus
```

Despus consultar la fuente documental apropiada:

```text
Brief / Master Index
        ↓
Kernel / Manual / Aliases / Career Canon / ID Census
        ↓
Execution
```

No reconstruir contratos desde memoria.

No asumir que la existencia histrica de un script implica que sigue siendo la interfaz vigente.

---

## 16 · VERSION... La versin operativa se consulta desde VANTAGE:

```bash
vversions
```

No hardcodear aqu una versin que pueda quedar obsoleta.

---

# VANTAGE

**Personal operating map.**

README = orientacin.

Kernel = contrato.

Manual = procedimiento.

Aliases = interfaz.

Career Canon = verdad profesional.