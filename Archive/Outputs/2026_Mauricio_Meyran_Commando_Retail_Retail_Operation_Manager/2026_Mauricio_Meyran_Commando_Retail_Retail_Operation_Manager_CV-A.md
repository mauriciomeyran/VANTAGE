# HANDOFF CV-A — Commando Retail / Retail Operation Manager

## Metadata
- URL vacante: sin URL pública directa (registro Tracker: https://app.notion.com/p/3dc938befc4281aab0c6e2d669b069be). JD tomado de la propiedad `JD` del registro (JD_Quality: JD Completo); el cuerpo de la página está vacío.
- Fecha de análisis: 2026-09-21
- Idioma detectado (ES/EN): ES
- Positioning Mode seleccionado: N4 · Commercial VM & Field Leadership

## Positioning Mode — Justificación

`JD_keywords_top6` y mapeo contra anclas de `CANON:POSITIONING`:

| # | Keyword del JD | N1 | N2 | N3 | N4 |
|---|---|---|---|---|---|
| 1 | Operación y ejecución comercial/visual de puntos de venta | | | | ✔ (estandarización operativa, cobertura de tiendas) |
| 2 | Liderar, capacitar y dar seguimiento a equipos de Retail | | | | ✔ (team management, coaching, training; CF06) |
| 3 | Múltiples puntos de venta | | | ✔ (multi-store rollout) | ✔ (store coverage; CF07) |
| 4 | Estándares de Visual Merchandising de la marca | ✔ (brand consistency) | | ✔ (standardization / guidelines) | ✔ (VM leadership, standardization) |
| 5 | Montajes, lanzamientos, promociones y cambios de colección | ✔ (NPI / campaign execution) | ✔ (installation, openings) | | |
| 6 | Análisis de ventas, stock, rotación y productividad por PDV | | | | ✔ (commercial KPIs, performance) |

Conteo: **N4 = 5** · N1 = 2 · N3 = 2 · N2 = 1. Sin empate; el paso 1 de la Regla de Desempate resuelve.

Señales de alarma:
- N4: no activada — el JD involucra equipos de campo y métricas comerciales (ventas, productividad).
- N1: activada — marca athleisure / boutique fitness, sin componente multi-marca de lujo.
- N3: el texto del JD no declara alcance multi-país (las Notas del registro mencionan 35 estudios en México/España).
- N2: el JD solo menciona "montajes", sin obra física, planos ni coordinación con arquitectos.

Anclas N4 (`CANON:POSITIONING-004`): C04 (21 reportes directos, +43% tráfico, +18% conversión) y C05 (17 tiendas retail + 12 corners, capacitación de personal de piso), con C03 como complemento de liderazgo regional y field enablement.

## Gap Analysis

### Matches directos
- Liderar, capacitar y dar seguimiento a equipos de Retail → C04 · CF06 (área de VM desde cero, 17 subgerentes de VM + 4 supervisores de zona); C05 (programas de capacitación para personal de piso; coordinadora Jr. con reporte directo); C03 (equipo de 3 directas + 3 indirectas; herramientas digitales para field teams, KPI04).
- Múltiples puntos de venta → C04 · CF07 (17 tiendas); C05 (17 tiendas retail + 12 corners wholesale); C03 · CF05 (270+ POS / 6 países).
- Implementar y mantener estándares de VM de la marca → C03 (estandarización regional, manuales de Zoning & Mapping, KPI04); C04 (planogramas estandarizados Denim & Lifestyle); C01 (consistencia de marca).
- Supervisar montajes, lanzamientos y cambios de colección → C01 (despliegue nacional NPI 2025: Born in Roma, Stronger With You); C03 (actualización de floorsets, KPI04); C05 (aperturas, remodelaciones y rotaciones de vitrinas); C02 (Adidas Brand Center Madero, KPI07 · CF03 · CF04).
- Perfil comercial → C04 · KPI01 (+43% tráfico) y KPI02 (+18% conversión).
- 3+ años en retail, moda/sportswear/lifestyle → KPI08 (14+ años); C02 (Adidas, sportswear), C03 (Levi's/Dockers), C04 (Aéropostale), C05 (ALDO).

### Matches parciales
- Supervisar operación y ejecución de puntos de venta; experiencia en operación y piso de venta → C04 y C05 respaldan coordinación de red de tiendas y capacitación de personal de piso desde VM. Falta: gestión diaria de operación de tienda (ventas, P&L de tienda) documentada en el Canon.
- Analizar ventas y productividad por punto de venta → KPI01/KPI02 (tráfico, conversión) y planogramas alineados a objetivos de ventas mensuales (C04). Falta: análisis de stock, rotación y sell-through.
- Promociones → C01 (materiales POP y displays para lanzamientos y campañas estacionales). Falta: ejecución de mecánicas promocionales específicas.
- Coordinarse con Buying, Planning, Operaciones y Warehouse → C01 (Marketing y Trade Marketing, proveedores); C02 (producción y logística de materiales). Falta: interacción documentada con Buying, Planning o Warehouse.

### Gaps (fit_gaps)
- Control de inventarios, movimientos y disponibilidad de producto — sin soporte en el Canon.
- Análisis de stock, rotación y sell-through — sin soporte en el Canon (el Canon solo cuantifica tráfico y conversión).
- Coordinación con Buying, Planning y Warehouse — sin soporte en el Canon.
- Operación comercial directa de tienda (piso de venta, P&L de tienda) — el Canon es VM-céntrico; sin registro explícito.
- Vertical athleisure / boutique fitness — solo evidencia indirecta vía sportswear (C02, proyecto Adidas Brand Center).

## Validación de exclusiones
- Empleador: Commando Retail — PASA
- Alcance del rol: multi-punto de venta (el JD pide "liderando equipos y múltiples puntos de venta"; Notas: 35 estudios) — PASA

## Observaciones
1. Fuente del JD: el registro Tracker no tiene URL pública (campo URL = placeholder; Notas: "Sin URL directa, solo captura de pantalla"). Se usó el JD completo de la propiedad `JD`; no se ejecutó `web_fetch` por ausencia de URL válida.
2. Discrepancia en el registro: las Notas contienen la marca "[ARCHIVO] Razón: URL Gate: NO_URL", mientras `Status = Objetivo`, `Next_Action = Optimizar` y `Archivar = NO`. Se documenta sin recomendación.
3. `tono_marca` derivado solo del JD y las Notas del registro (perfil "comercial, analítico, hands-on"; marca athleisure / boutique fitness); no se consultó material de marca externo.
4. Anti-overselling (`CANON:POSITIONING-005`): N4 ancla en liderazgo de VM y equipos de campo; CV-B no debe afirmar operación de tienda, control de inventario ni análisis de sell-through.
5. Nota de proceso: el skill adjunto incluye `cv_b_eligible`, `block_reason` y la Naming Convention (`KERNEL:FILE-NAMING-001`), y su cabecera sigue en v9.16.0 (igual que `SP:SKILL-VERSION-PIN`). No se verificó contra el Kernel en esta corrida.

## Próximo paso
Listo para CV-B.

## HANDOFF (JSON)

```json
{
  "empresa": "Commando Retail",
  "rol": "Retail Operation Manager",
  "JD_keywords_top6": [
    "operación y ejecución comercial/visual de puntos de venta",
    "liderazgo y capacitación de equipos de retail",
    "múltiples puntos de venta",
    "estándares de Visual Merchandising de la marca",
    "montajes, lanzamientos, promociones y cambios de colección",
    "análisis de ventas, stock, rotación y productividad por punto de venta"
  ],
  "fit_gaps": [
    "Control de inventarios, movimientos y disponibilidad de producto — sin soporte en Canon",
    "Análisis de stock, rotación y sell-through — sin soporte en Canon (solo tráfico/conversión)",
    "Coordinación con Buying, Planning y Warehouse — sin soporte en Canon",
    "Operación comercial directa de tienda (piso de venta, P&L de tienda) — Canon VM-céntrico, sin registro explícito",
    "Vertical athleisure / boutique fitness — solo evidencia indirecta vía sportswear (C02)"
  ],
  "tono_marca": "Comercial, operativo, analítico y hands-on; marca athleisure / boutique fitness (derivado del JD y Notas del registro)",
  "idioma": "ES",
  "positioning_rationale": "N4 · Commercial VM & Field Leadership — 5 de 6 keywords mapean a anclas C04/C05 (liderazgo de equipos, cobertura de tiendas, estándares VM, KPIs comerciales); N1=2, N3=2, N2=1; sin empate. Anclas: CF06, CF07, KPI01, KPI02, C05.",
  "observaciones": "JD tomado de la propiedad JD del registro Tracker (sin URL pública). Notas del registro contienen marca '[ARCHIVO] Razón: URL Gate: NO_URL' con Status=Objetivo, Next_Action=Optimizar, Archivar=NO. tono_marca derivado solo de JD/Notas. Anti-overselling aplica: no afirmar operación de tienda, inventario ni sell-through.",
  "cv_b_eligible": true,
  "block_reason": []
}
```
