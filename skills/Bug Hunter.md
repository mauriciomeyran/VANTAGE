---
name: bug-hunter
description: Audita código de forma estática y no destructiva para identificar bugs, vulnerabilidades y problemas de mantenibilidad, con evidencias y reportes verificables.
---

# BUG HUNTER

> **Estado del documento:** reconstrucción basada en el historial de conversación. No es una recuperación literal del texto original; los detalles que no se conservaron se han reconstruido de forma explícita y conservadora.

## 1. Objetivo

Detectar y documentar defectos potenciales o confirmados en archivos individuales, conjuntos de archivos, directorios o repositorios completos. Los hallazgos deben ser accionables, reproducibles cuando sea posible y respaldados por evidencia concreta.

## 2. Arquitectura recuperada

Estructura de trabajo mencionada en el historial:

```text
bug-hunter/
├── SKILL.md
├── hunt.sh
├── analyzer.py
└── template.html
```

- `hunt.sh`: punto de entrada para iniciar y coordinar la auditoría.
- `analyzer.py`: análisis estático, clasificación de hallazgos y generación de datos del informe.
- `template.html`: plantilla del dashboard HTML autónomo.
- `SKILL.md`: instrucciones operativas del skill.

La existencia de estos nombres se recuperó del historial; no se ha verificado aquí el contenido actual de esos archivos ni que estén presentes en el repositorio.

## 3. Alcance

Analizar, según lo que exista en el objetivo y las capacidades implementadas:

- Python (`.py`)
- JavaScript (`.js`, `.mjs`, `.cjs`)
- TypeScript (`.ts`, `.tsx`)
- HTML (`.html`, `.htm`)
- CSS (`.css`)
- Shell (`.sh`, `.bash`, `.zsh`)
- JSON (`.json`)
- YAML (`.yaml`, `.yml`)

Se pueden auditar archivos individuales, múltiples archivos, directorios o repositorios. Respetar exclusiones explícitas y evitar directorios de dependencias, artefactos generados y archivos binarios, salvo petición expresa.

El soporte declarado para un lenguaje no garantiza análisis semántico completo: el informe debe indicar límites de cobertura y herramientas realmente utilizadas.

## 4. Método de auditoría

1. **Delimitar el objetivo.** Registrar la ruta, el alcance solicitado, exclusiones y límites de la revisión.
2. **Inspeccionar sin modificar.** Leer archivos y metadatos pertinentes. No alterar el árbol de trabajo.
3. **Analizar estáticamente.** Buscar errores de lógica, condiciones límite, manejo incorrecto de datos, fallos de validación, errores de tipos o contratos, problemas de seguridad y defectos de mantenibilidad.
4. **Verificar la evidencia.** Revisar el contexto de cada coincidencia. No considerar un patrón aislado como prueba suficiente.
5. **Clasificar cada hallazgo.** Separar estado, severidad y confianza.
6. **Generar informes.** Producir JSON estructurado y un dashboard HTML autocontenido.
7. **Declarar límites.** Enumerar archivos excluidos, errores de lectura, lenguajes no analizados y verificaciones no realizadas.

No afirmar que una auditoría es exhaustiva si hubo límites de cobertura.

## 5. Estados de los hallazgos

Cada hallazgo debe tener exactamente uno de estos estados:

- `CONFIRMED`: existe evidencia suficiente para afirmar el defecto dentro del contexto inspeccionado.
- `POTENTIAL`: hay indicios concretos, pero falta confirmar una condición necesaria o un comportamiento.
- `NEEDS_REVIEW`: la evidencia o el contexto disponible no permiten clasificarlo de forma fiable; requiere revisión humana.
- `FALSE_POSITIVE`: se evaluó la señal y existe evidencia contextual de que no representa un defecto.

No elevar un hallazgo a `CONFIRMED` solo porque coincida con una regla o patrón. Los falsos positivos deben conservar una explicación breve de la decisión.

## 6. Severidad y confianza

Evaluar estos atributos **de forma independiente**.

### Severidad

- `CRITICAL`: compromiso grave o pérdida de control con impacto amplio y plausible.
- `HIGH`: impacto importante en seguridad, integridad de datos o funcionamiento esencial.
- `MEDIUM`: fallo funcional o riesgo relevante, normalmente con condiciones de activación delimitadas.
- `LOW`: impacto limitado, caso poco frecuente o defecto menor.
- `INFO`: observación útil que no constituye necesariamente un defecto.

### Confianza

- `HIGH`: evidencia directa y contexto suficiente.
- `MEDIUM`: evidencia razonable, pero falta una comprobación importante.
- `LOW`: hipótesis plausible que requiere validación adicional.

La severidad expresa el impacto si el defecto existe; la confianza expresa la solidez de la conclusión. No deben confundirse.

## 7. Contenido mínimo de cada hallazgo

Cada hallazgo debe incluir, cuando la información esté disponible:

- `id`: identificador estable dentro del informe.
- `title`: resumen específico del problema.
- `status`: estado definido en la sección 5.
- `severity`: severidad definida en la sección 6.
- `confidence`: confianza definida en la sección 6.
- `file`: ruta relativa al objetivo auditado.
- `line_start` y `line_end`: líneas pertinentes, si se pueden determinar.
- `evidence`: fragmento mínimo o descripción precisa de la evidencia, sin exponer secretos.
- `description`: qué ocurre y bajo qué condiciones.
- `impact`: consecuencia plausible y alcance.
- `recommendation`: corrección propuesta, sin aplicarla.
- `verification`: método concreto para comprobar la hipótesis o validar la corrección.
- `limitations`: incertidumbres relevantes, cuando existan.

No inventar líneas, rutas, resultados de pruebas ni evidencia. Si un dato no está disponible, declararlo como desconocido o nulo.

## 8. Formatos de salida

Generar:

1. **`scan_report.json`**: fuente estructurada de los hallazgos, cobertura y metadatos de ejecución.
2. **`scan_report.html`**: dashboard autónomo basado en `template.html`, sin dependencias de CDN ni recursos externos obligatorios.

El informe debe incluir resumen ejecutivo, recuentos por estado y severidad, hallazgos con evidencia, alcance analizado, exclusiones, limitaciones y recomendaciones. Los recuentos deben derivarse de los datos del JSON, no mantenerse manualmente por separado.

### Esquema orientativo del JSON

```json
{
  "schema_version": "1.0",
  "tool": "bug-hunter",
  "target": "ruta-del-objetivo",
  "mode": "static_read_only",
  "summary": {
    "files_discovered": 0,
    "files_analyzed": 0,
    "findings_total": 0
  },
  "coverage": {
    "languages": [],
    "excluded_paths": [],
    "limitations": []
  },
  "findings": [
    {
      "id": "BH-001",
      "title": "Descripción breve",
      "status": "POTENTIAL",
      "severity": "MEDIUM",
      "confidence": "MEDIUM",
      "file": "src/example.py",
      "line_start": 10,
      "line_end": 12,
      "evidence": "Evidencia mínima y redactada",
      "description": "Comportamiento observado e hipótesis",
      "impact": "Impacto plausible",
      "recommendation": "Corrección propuesta, no aplicada",
      "verification": "Comprobación sugerida",
      "limitations": []
    }
  ]
}
```

El ejemplo es ilustrativo, no una declaración de que el esquema original tuviera exactamente estos campos.

## 9. Seguridad y límites de ejecución

Por defecto, el modo de trabajo es estático, no destructivo y de solo lectura.

Sin autorización explícita, está prohibido:

- modificar, crear, eliminar o formatear archivos del objetivo;
- ejecutar el código auditado, scripts del repositorio o pruebas;
- instalar dependencias o cambiar el entorno;
- crear commits, cambiar de rama, hacer push o desplegar;
- alterar configuraciones, datos, permisos o servicios;
- ampliar el alcance solicitado.

La generación de los informes debe dirigirse a una ubicación de salida acordada que no sobrescriba archivos del proyecto. Si esto no está definido, solicitar confirmación antes de escribir.

### Secretos y datos sensibles

- No incluir tokens, contraseñas, claves privadas, credenciales ni valores sensibles completos en los informes.
- Redactar los valores detectados, conservando solo el contexto mínimo necesario.
- No copiar contenido sensible al HTML, logs o mensajes de error.
- No enviar código ni resultados a servicios externos sin autorización explícita.

## 10. Criterios de aceptación

Una ejecución se considera entregada correctamente cuando:

- el objetivo y las exclusiones quedan registrados;
- el informe distingue archivos descubiertos, analizados, omitidos y fallidos;
- cada hallazgo tiene estado, severidad y confianza separados;
- los hallazgos accionables contienen evidencia, impacto, recomendación y método de verificación;
- los falsos positivos no se presentan como bugs confirmados;
- el JSON es válido y los totales coinciden con sus registros;
- el HTML se puede abrir localmente sin depender de CDN;
- secretos y datos sensibles aparecen redactados;
- no se han realizado cambios ni ejecuciones no autorizadas;
- las limitaciones de cobertura se declaran de forma visible.

## 11. Regla de comunicación

Entregar primero los hallazgos de mayor impacto y confianza. Ser preciso y conciso. Diferenciar siempre entre:

- lo que se observó directamente;
- lo que se infiere;
- lo que no se pudo comprobar.

No afirmar que una corrección funciona si no se verificó. Las correcciones son propuestas hasta que el usuario autorice su aplicación y se complete una verificación posterior.
