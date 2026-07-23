# VANTAGE Skills via MCP

Este directorio contiene las skills de VANTAGE accesibles vía MCP (Model Context Protocol).

## Configuración MCP

Para hacer estas skills accesibles a cualquier IA compatible con MCP (Gemini, Claude, ChatGPT, etc.):

### Devin CLI
```bash
devin mcp add vantage-skills -- npx markdown-mcp-resource@latest https://mauriciomeyran.github.io/VANTAGE/skills/index.json
```

### Otros clientes MCP
Configura el servidor MCP con el comando:
```bash
npx markdown-mcp-resource@latest https://mauriciomeyran.github.io/VANTAGE/skills/index.json
```

## Skills Disponibles

- **prompt-master**: Genera prompts optimizados para herramientas de IA
- **tailored-resume-generator**: Genera currículums personalizados según descripciones de trabajo
- **vantage-create-bug-task**: Crea tickets en Bug Tracker o Task Tracker de VANTAGE
- **vantage-documentacion-transversal-implementacion**: Implementa documentación transversal
- **vantage-documentacion-transversal-propuesta**: Genera propuestas de documentación transversal
- **vantage-documentacion-transversal**: Mantiene documentación transversal en documentos fundacionales
- **vantage-present-handoff**: Genera snapshot de contexto de sesión para continuidad
- **vantage-session-close**: Protocolo de cierre de sesión VANTAGE
- **vantage-session-open**: Protocolo de apertura de sesión VANTAGE
- **vantage-tidy-bug-task-tracker**: Marca tickets para archivado en Bug/Task Tracker
- **vantage-tidy-changelog**: Mantiene el Change Log con las últimas 10 entradas
- **vantage-tidy-opportunities-tracker**: Identifica duplicados y vacantes expiradas en VANTAGE Tracker

## Actualización

Para agregar nuevas skills:
1. Agrega el archivo `.md` a este directorio
2. Actualiza `index.json` con la nueva skill
3. Haz commit y push al repositorio
4. GitHub Pages publicará automáticamente los cambios