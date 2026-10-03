# Correcciones de vdoc_nblm y vsum — 2026-10-03

## vdoc_nblm

- Excluye antes de leer: `.env`, `*.env`, variantes/plantillas `.env.*`,
  claves, PEM, secretos, JSON de tokens/credenciales/client secrets,
  `Archive/`, `backups/` y directorios de dependencias/cachés.
- Lista positiva de extensiones de texto; no sigue enlaces simbólicos,
  tampoco en las fuentes Markdown de `Documentación/ACTIVE`.
- Digest atómico con permisos `0600`. Un error de lectura/escritura aborta;
  no se sube un digest parcial ni uno anterior como sustituto.
- `NOTEBOOK_ID` obligatorio, no vacío y validado contra cuadernos accesibles.
  Ya no hay selección automática del primer cuaderno.
- Exit `1` ante errores de configuración, autenticación, generación, listado,
  carga o borrado; exit `0` sólo si termina la sincronización.
- Carga la nueva fuente antes de borrar las anteriores del mismo título.
  Si falla el borrado puede quedar un duplicado y se devuelve error;
  si el cuaderno está lleno la carga falla sin borrar la versión anterior.

Uso: `NOTEBOOK_ID='<id-del-cuaderno>' python Layer_4/scripts/vdoc_nblm.py`.

**Límite de seguridad:** el filtro es por ruta/nombre/extensión; no detecta
secretos pegados dentro de un archivo permitido (por ejemplo código o Markdown).
Revisar esas fuentes antes de exportarlas. No se ejecutó una subida real durante
esta corrección.

**Si se ejecutó la versión anterior con credenciales locales:** eliminar de
NotebookLM las fuentes/digests afectados y las copias locales inseguras, y rotar
las credenciales potencialmente expuestas. Este cambio no revoca secretos ni
elimina copias ya subidas.

## vsum

- `call_ollama` respeta `OLLAMA_TIMEOUT_SEC` (120 segundos por defecto).
- Contabiliza separadores sólo cuando existen al formar chunks.
- Presupuesto por llamada: `MAX_CHARS_PER_CHUNK`, incluyendo sistema,
  plantilla, metadatos e instrucciones de consolidación.
- Consolidación jerárquica, también para resúmenes parciales gigantes.
  No trunca el texto para forzarlo al límite; falla si no hay compresión o si
  se superan 8 niveles, evitando bucles y prompts sobredimensionados.
- Política compartida para chunks y meta-resúmenes:
  Gemini → Ollama con un reintento tras 5 s → Groq sólo con `GROQ_API_KEY`.
  Ollama comienza en su propia etapa; Groq explícito no hace fallback.
  **Con una clave Groq configurada, un fallo persistente de Ollama puede enviar
  texto al servicio externo Groq.**
- El presupuesto es en caracteres, no tokens: no garantiza caber en cualquier
  ventana/tokenizador o configuración de Ollama, ni reserva tokens exactos de salida.

## Validación

- Tests con archivos temporales y clientes simulados, sin red de proveedores.
- Regresiones de filtros antes de lectura, enlaces, permisos, digest previo,
  selección del cuaderno, errores y códigos de salida, orden carga/borrado,
  timeout, fallback, presupuesto y convergencia.
- `Layer_4/scripts.zip` actualizado únicamente en las dos entradas corregidas;
  test de paridad con los scripts fuente.
- Comando: `.venv/bin/python -m pytest tests -q`.
