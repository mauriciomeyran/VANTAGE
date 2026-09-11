# CONTRATO DE SESIÓN — Verificación obligatoria (capa de gobernanza)

**Serial:** DEVIN-20260911-02 · **Fecha:** 2026-09-11 · **De:** auditoría Arena · **Para:** Devin
**Prevalencia:** este documento gobierna el CÓMO se demuestra el trabajo. El QUÉ técnico sigue vigente en `handoffs/CONTRATO_DEVIN_REFACTOR_TRACKER_2026-09-11.md` (alcance) + hallazgos abiertos en namespaces canónicos B/A/R (`RESPUESTA_DEVIN_PLAN_REFACTOR_2026-09-11.md`) y F1–F15 (`REREVIEW_DEVIN_V3_2026-09-11.md`). En conflicto de mecanismo de entrega, prevalece este contrato. Nada aquí autoriza escritura a Notion de producción ni a `main`.
**Estado verificado al emitir:** `main` = `467af9c8bdef1b120ba1fba095a35931624f6236`; `devin/plan-refactor-tracker-v2` = `56a9f3552256ea8eb99cab2e4cb4095e9d225e07` (base stale, delta vs main: 311 archivos / −687K líneas — ver §0.4).

## §0 — PASO 0 OBLIGATORIO: entorno antes que diseño

0.1. Antes de tocar cualquier diseño o código, ejecutar y pegar output literal en el handoff:
`git fetch origin main && git rev-parse origin/main && git log --oneline -1 origin/main`
0.2. El SHA obtenido debe ser `467af9c8…` o un descendiente fast-forward del mismo. Si es descendiente, registrar el nuevo SHA y trabajar sobre él; si diverge, parar y reportar.
0.3. Crear rama FRESCA desde ese SHA (`git checkout -b devin/<nombre-nuevo> <SHA>`), nombre libre con prefijo `devin/`. Pegar el comando y su output.
0.4. **Prohibido** reusar `devin/plan-refactor-tracker-v2` como base o mergearla (su linaje pre-Sep-10 destruiría main). Sus docs solo se reutilizan copiando archivos puntuales a la rama fresca.
0.5. Handoff de cierre sin el transcript de §0 = rechazo automático (ver §7-R1).

## §1 — EVIDENCIA DE EJECUCIÓN PEGADA, NO DECLARADA

1.1. Por cada módulo nuevo o modificado: pegar literalmente comando + output completo de `python3 -c "import <modulo>"` (o `from <modulo> import *`). Un solo transcript por módulo basta; un transcript puede amparar varios ítems.
1.2. Si hay traceback, se pega ÍNTEGRO y sin editar, junto con el fix y su re-ejecución. Traceback oculto o resumido = evidencia inválida.
1.3. Frases como "corrí el import y funcionó", "testeado localmente", "verificado" sin output pegado carecen de valor probatorio: el ítem que solo tenga eso cuenta como NO resuelto.
1.4. Todo sketch de código en el handoff debe existir como archivo real en la rama, con ruta exacta. Código que solo existe en prosa no existe.

## §2 — TABLA DE TRAZABILIDAD OBLIGATORIA

2.1. El handoff de cierre incluye una tabla con UNA fila por cada hallazgo declarado resuelto, claveado por ID canónico (B-/A-/R-/F-):
`| ID | archivo:línea(s) exactas | diff (§4) | evidencia ejecución (§1/§3) |`
2.2. **Regla de rechazo:** declaración de "resuelto" sin cita `archivo:línea` verificable en la rama = automáticamente NO resuelto, sin pasar a revisión de contenido.
2.3. Citas a líneas que no contienen lo declarado, o a archivos inexistentes en la rama, invalidan la fila completa.

## §3 — TESTS QUE SE EJECUTAN, NO QUE SE NOMBRAN

3.1. Pegar el comando `pytest` real y su output completo (conteo pass/fail/error + tiempo). Una sola invocación puede amparar todos los ítems.
3.2. Cada test citado debe existir como archivo en la rama. Test nombrado-pero-ausente = fila inválida (§2.3).
3.3. Incluir mapa cobertura `test ↔ ID(s) de hallazgo` (una línea por test basta). Sin mapa, los tests no amparan ningún ítem.
3.4. Por defecto: unitarios con fakes, cero llamadas de red. Integración contra Notion no-productivo solo si se resuelve Q-G1.

## §4 — DIFFS REALES, NO RESÚMENES

4.1. Todo cambio respecto a la versión previa se presenta como `git diff` real (unificado, con rutas) — pegado en el handoff (≤200 líneas) o como archivo(s) en la rama con ruta citada.
4.2. Los resúmenes en prosa son epígrafes de los diffs, nunca sustitutos. "Conforme al contrato anterior" / "ajustado según revisión" sin diff visible = declaración nula.
4.3. El diff debe permitir verificar cada fila de la tabla §2 sin leer prosa.

## §5 — RESTRICCIONES VIGENTES (por referencia, no se redefinen)

Siguen en vigor las restricciones de rondas anteriores: cero escritura a Notion de producción · cero `input()` en pipeline · PR lo abre Devin, lo mergea Mau · frase de conformidad obligatoria al cierre (§8). Violar cualquiera = rechazo automático.

## §6 — PREGUNTAS ABIERTAS DE GOBERNANZA

- **Q-G1:** ¿Quién aprovisiona token/entorno Notion NO-productivo si Devin propone tests de integración? Default vigente: no se proponen; unitarios con fakes. Dato de cierre: URL/token o "se mantiene default".

## §7 — CRITERIOS DE RECHAZO AUTOMÁTICO

Sin revisión de contenido, se rechaza el handoff si: **R1** falta transcript §0 · **R2** rama reusada/stale como base (§0.4) · **R3** algún "resuelto" sin fila §2 con cita verificable · **R4** evidencia de ejecución parafraseada en vez de pegada (§1.3) · **R5** tests nombrados sin archivo o sin output `pytest` (§3) · **R6** "conforme/ajustado" sin diff (§4.2) · **R7** violación de §5 · **R8** falta frase §8 textual.

## §8 — FRASE DE CONFORMIDAD (textual, obligatoria)

> Declaro bajo el contrato DEVIN-20260911-02 que cada ítem marcado resuelto tiene cita archivo:línea, diff visible y evidencia de ejecución pegada; lo que no tenga las tres, no está resuelto.
