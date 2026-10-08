# REQUISITO ADICIONAL: ARQUITECTURA DE ACCESO MULTI-AGENTE (MCP + FALLBACK CLI)

## Resumen de Implementación

Se ha implementado una arquitectura de acceso dual para el ecosistema de agentes de VANTAGE:

### Modo 1: Clientes MCP Nativos (Acceso Directo)

**Clientes Soportados:**
- Claude Desktop ✅
- Cursor ✅
- Devin (sesión actual) ✅
- ChatGPT ✅
- Grok ✅
- Windsurf ✅

**Mecanismo:** JSON-RPC sobre stdio transport
**Configuración:** Archivos JSON específicos por cliente en `.devin/mcp-configs/`

**Capacidades:**
- Invocación de herramientas en tiempo real durante la conversación
- Recuperación y almacenamiento automático de contexto
- Búsqueda semántica vía mem0-mcp
- Memoria de proyecto vía vantage-context-sync

---

### Modo 2: Agentes Non-MCP / GitHub-Only / CLI (Context Dump Fallback)

**Clientes Soportados:**
- Gemini
- Perplexity
- Mistral
- Arena
- Hermes
- GitHub Actions
- Cualquier agente sin soporte MCP nativo

**Mecanismo:** Context dump CLI → Inyección en prompt
**Herramienta:** `context-dump.py` (script standalone)

---

## Entregable: context-dump.py

### Ubicación
`/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts/context-dump.py`

### Características
- **Standalone:** No requiere dependencias del runtime VANTAGE (solo Python 3 stdlib + sqlite3)
- **Compacto:** Genera bloques Markdown de ~150-250 tokens (configurable via `--limit`)
- **Dual Source:** Consulta tanto `context-sync.db` como `mem0/memories.sqlite`
- **Flexible:** Soporta salida Markdown o JSON

### Uso

```bash
# Script standalone (recomendado)
python3 context-dump.py --project vantage --limit 5 --format markdown

# Via vantage.py (comando integrado)
python3 vantage.py context-dump --project vantage --limit 5 --format markdown

# Via wrapper Zsh
./vantage-context-dump.zsh --project vantage --limit 5
```

### Argumentos
- `--project`: ID del proyecto para filtrado (default: vantage)
- `--limit`: Máximo de memorias por fuente (default: 5)
- `--format`: Formato de salida - markdown o json (default: markdown)

### Ejemplo de Salida (Markdown)

```markdown
# VANTAGE Context

## Project Memory (Context Sync)
- [decision] test:setup: VANTAGE MCP integration completed successfully

## Semantic Memory (mem0)
- [preference] Use local Ollama for embeddings
- [decision] Store context in SQLite at ~/.vantage/
```

### Ejemplo de Salida (JSON)

```json
{
  "project_id": "vantage",
  "context_sync": [
    "## Project Memory (Context Sync)",
    "- [decision] test:setup: VANTAGE MCP integration completed successfully"
  ],
  "mem0": [],
  "full_output": [...]
}
```

---

## Integración con Prompt de Agentes Non-MCP

### Ejemplo: GitHub Actions

```yaml
- name: Load VANTAGE Context
  run: |
    CONTEXT=$(python3 Layer_1/scripts/context-dump.py --project vantage --limit 3)
    echo "VANTAGE_CONTEXT<<EOF" >> $GITHUB_ENV
    echo "$CONTEXT" >> $GITHUB_ENV
    echo "EOF" >> $GITHUB_ENV

- name: Run Agent with Context
  run: |
    echo "You are working on VANTAGE. Context: $VANTAGE_CONTEXT" | agent-cli
```

### Ejemplo: Gemini / Perplexity / Mistral (Manual)

```bash
# Generar context dump
CONTEXT=$(python3 context-dump.py --project vantage --limit 5)

# Inyectar en prompt
echo "You are working on the VANTAGE project. Here is the relevant context:
$CONTEXT

Current task: [describir tarea aquí]" | agent-api
```

### Ejemplo: Template de Prompt para Agentes

```
You are working on the VANTAGE project. Here is the relevant context:

[insertar salida de context-dump.py aquí]

Current task: [describir tarea]

Please proceed with the task, using the context above as background information.
```

---

## Wrappers Adicionales

### Python Wrapper (Acceso MCP Completo)
**Ubicación:** `.devin/mcp-tools/vantage-memory.py`
**Propósito:** Acceso completo a herramientas MCP vía JSON-RPC stdio
**Uso:** Para scripts que necesitan toda la superficie de herramientas

### Zsh Wrapper (Acceso Rápido)
**Ubicación:** `.devin/mcp-tools/vantage-context-dump.zsh`
**Propósito:** Acceso rápido de terminal a context-dump.py
**Uso:** Para uso interactivo rápido desde terminal

---

## Configuraciones MCP Generadas

Todos los archivos de configuración MCP están listos en `.devin/mcp-configs/`:

- `claude-desktop.json` - Claude Desktop
- `windsurf.json` - Windsurf
- `vscode-cline.json` - VS Code / Cline
- `cursor.json` - Cursor
- `chatgpt.json` - ChatGPT
- `grok.json` - Grok
- `.mcp.json` - Configuración a nivel de proyecto

---

## Arquitectura de Datos

```
┌─────────────────────────────────────────────────────────────┐
│              Modo 1: Clientes MCP Nativos                    │
│  (Claude Desktop, Cursor, Devin, ChatGPT, Grok, Windsurf) │
└──────────────────────┬──────────────────────────────────────┘
                       │ stdio (JSON-RPC)
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼─────────┐         ┌────────▼─────────┐
│  mem0-mcp Server │         │ Context Sync     │
│  (Semantic LTM)  │         │ (Project Memory) │
└───────┬─────────┘         └────────┬─────────┘
        │                             │
┌───────▼─────────┐         ┌────────▼─────────┐
│  SQLite @       │         │  SQLite @        │
│  ~/.vantage/    │         │  ~/.vantage/     │
│  mem0/          │         │  context-sync.db │
└─────────────────┘         └──────────────────┘
        │
        ▼
  Ollama (nomic-embed)

┌─────────────────────────────────────────────────────────────┐
│              Modo 2: Agentes Non-MCP / CLI                  │
│  (Gemini, Perplexity, Mistral, Arena, Hermes, GitHub)       │
└──────────────────────┬──────────────────────────────────────┘
                       │ context-dump.py CLI
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼─────────┐         ┌────────▼─────────┐
│  SQLite @       │         │  SQLite @        │
│  ~/.vantage/    │         │  ~/.vantage/     │
│  mem0/          │         │  context-sync.db │
└─────────────────┘         └──────────────────┘
        │
        ▼
  Markdown Dump (~150-250 tokens)
        │
        ▼
  Inyección en Prompt
```

---

## Verificación

### Test de context-dump.py

```bash
$ python3 context-dump.py --project vantage --limit 3 --format markdown
# VANTAGE Context

## Project Memory (Context Sync)
- [decision] test:setup: VANTAGE MCP integration completed successfully
```

### Test de formato JSON

```bash
$ python3 context-dump.py --project vantage --limit 3 --format json
{
  "project_id": "vantage",
  "context_sync": [
    "## Project Memory (Context Sync)",
    "- [decision] test:setup: VANTAGE MCP integration completed successfully"
  ],
  "mem0": [],
  "full_output": [...]
}
```

---

## Pasos Siguientes para el Operador

1. **Configurar clientes MCP** (Modo 1):
   - Copiar configs de `.devin/mcp-configs/` a las respectivas aplicaciones
   - Verificar que las herramientas aparecen en la lista de herramientas

2. **Testear context-dump CLI** (Modo 2):
   ```bash
   cd /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts
   python3 context-dump.py --project vantage --limit 5 --format markdown
   ```

3. **Integrar en workflows de agentes non-MCP**:
   - Agregar context-dump a scripts de GitHub Actions
   - Crear templates de prompt que incluyan el context dump
   - Documentar el uso para equipos que usen Gemini, Perplexity, Mistral, etc.

4. **Opcional: Agregar a PATH**:
   ```bash
   # Agregar a ~/.zshrc
   export PATH="$PATH:/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts"

   # Usar desde cualquier lugar:
   context-dump.py --project vantage --limit 5
   ```

---

## Estado

✅ **COMPLETO**

- Modo 1 (MCP nativo): Configuraciones generadas para 6 clientes
- Modo 2 (CLI fallback): Script context-dump.py standalone implementado
- Wradders adicionales: Python (MCP completo) y Zsh (acceso rápido)
- Integración vantage.py: Comando `context-dump` agregado
- Documentación: Guía completa de uso para ambos modos
