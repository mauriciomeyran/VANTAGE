# PROMPTS_GLAZE-v3 — actualización incremental de VANTAGE BitTorrent Search

**Base:** PROMPTS_GLAZE-v2.md  
**Backend:** commit local 81fc301, “Add LimeTorrents pagination with tests”  
**Objetivo:** actualizar la app existente, sin reconstruirla ni alterar sus funciones que ya trabajan.

## Hallazgo técnico obligatorio

El backend Python ya admite el parámetro opcional `paginas=1` en `buscar_torrents_limetorrents`. El valor predeterminado conserva el comportamiento anterior; si se piden más páginas, el motor acumula resultados, deduplica por magnet y se detiene al encontrar una página posterior vacía.

Pero el CLI que consume la app todavía NO expone una opción para configurar ese parámetro. En `main.py` no existe una opción como `--limetorrents-pages`, y `scripts/vantage-search` solo reenvía los argumentos al CLI. Por tanto, la app no puede activar la paginación mediante un cambio de UI únicamente.

**No le pidas a Glaze que invente el flag, simule paginación ni implemente scraping en Swift.** Primero debe existir y probarse el puente CLI. Conserva PROMPTS_GLAZE-v2.md intacto; utiliza este archivo como actualización incremental.

---

## PROMPT 4 — Preflight de integración (Plan Mode)

Pega este prompt primero en Glaze. No le permitas modificar archivos en esta fase.

```markdown
This is an incremental update to the EXISTING VANTAGE BitTorrent Search macOS app, not a rebuild.

The Python engine changed in commit 81fc301:
- buscar_torrents_limetorrents(..., paginas=1) accepts a positive integer page count.
- The default of 1 preserves existing behavior.
- Additional pages are accumulated and deduplicated by magnet in the backend.
- Pagination stops when a later page is empty.
- All scraping, parsing, filtering, deduplication, and sorting remain backend responsibilities.

The app integrates only through this local CLI:
"/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Bittorrent_Search/scripts/vantage-search" "<query>" --json

Before proposing UI changes:
1. Inspect the actual backend CLI help using scripts/vantage-search --help-backend or main.py --help.
2. Verify whether a CLI option exists to configure the LimeTorrents page count.
3. The current revision does not expose such an option. Do not invent --limetorrents-pages or any other flag, and do not create a UI control that cannot work.
4. Do not modify backend Python, CLI code, project files, or app files in this preflight phase.
5. Report the exact missing integration point and stop. Wait until the CLI contract is implemented and verified before building the UI control.

Keep all existing app functionality unchanged. All user-facing text remains Spanish (es-MX).
```

### Prerrequisito fuera de Glaze

Antes de continuar, el backend debe exponer y probar una opción CLI explícita para configurar el número de páginas de LimeTorrents, por ejemplo `--limetorrents-pages N`, y propagarla exclusivamente a ese motor.

Contrato esperado:
- Predeterminado: 1, sin cambiar el comportamiento actual.
- Aceptar solo enteros positivos dentro de un rango documentado.
- Rechazar valores inválidos con un error de argumentos claro.
- No alterar el número de páginas de ningún otro motor.
- Mostrar la opción en la ayuda del CLI y pasarla desde `scripts/vantage-search`.
- Añadir pruebas de CLI/integración que demuestren que el valor llega al motor LimeTorrents y que los demás motores conservan su comportamiento.
- No considerar el puente listo hasta que las pruebas reales pasen.

No le encargues esta parte a Glaze: el wrapper de UI no debe reimplementar backend. Implementar este puente requiere un cambio backend separado y autorizado.

---

## PROMPT 5 — Control de páginas de LimeTorrents (Build Mode)

**Usar únicamente después de que el prerrequisito CLI esté implementado y verificado.**

```markdown
Update the EXISTING VANTAGE BitTorrent Search macOS app incrementally. Do not rebuild the app or redesign working screens.

Prerequisite: the actual backend CLI help confirms that --limetorrents-pages N is implemented and tested. Verify this before coding. If the option is absent, STOP and report the blocker. Do not fake it.

Add one optional advanced setting:
- Spanish label: "Páginas de LimeTorrents"
- Integer stepper or numeric input.
- Default: 1, preserving the current behavior.
- Allowed range: 1–10.
- Help text: "Consulta más páginas de LimeTorrents. Puede tardar más y traer más resultados."
- When the value is 1, omit the new CLI flag to preserve the existing command exactly.
- When the value is greater than 1, append --limetorrents-pages and the selected number as separate Process arguments.
- Pass process arguments directly; never concatenate user input into a shell command.
- Keep --json and use the existing JSON response contract.
- Do not paginate, scrape, parse HTML, deduplicate, or filter results in Swift/macOS. The backend remains the sole source of search logic.
- Do not change YTS, EZTV, Nyaa, MagnetDL, relevance filtering, minimum seeders, or existing settings.
- Preserve asynchronous execution, cancellation, diagnostics, history, export, and full magnet copying.
- Do not change unrelated UI, copy, architecture, or backend files.

Acceptance checks:
1. At value 1, the app invokes the existing CLI command without the new flag.
2. At value 3, the app passes --limetorrents-pages and 3 as separate arguments.
3. Existing searches and settings continue to behave as before.
4. If the backend rejects the flag, show the actual error. Never silently pretend pagination occurred.
5. Results and diagnostics still come from CLI JSON. Do not claim extra pages were fetched unless the CLI accepted the option.
6. All visible UI text remains Spanish (es-MX).

Before editing, list the exact files you plan to change and wait for my approval. Then implement only the setting and argument wiring. Report the changed files and the verification actually performed.
```

## Criterio de cierre

El motor Python ya está implementado y sus pruebas pasan. La actualización de UI queda bloqueada hasta que el CLI exponga el parámetro. No marques la integración como terminada antes de verificar ese puente.
