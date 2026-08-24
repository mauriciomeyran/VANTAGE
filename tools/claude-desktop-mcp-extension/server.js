#!/usr/bin/env node

/**
 * VANTAGE Serial Allocation MCP Server for Claude Desktop
 * 
 * This MCP server acts as a bridge between Claude Desktop and the central
 * VANTAGE HTTP serial allocation server.
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');

// Configuration
const HTTP_SERVER_URL = process.env.VANTAGE_SERIAL_HTTP_URL || 'http://localhost:8787';
const TIMEOUT = parseInt(process.env.VANTAGE_SERIAL_TIMEOUT || '10000');

// Create MCP server
const server = new Server(
  {
    name: 'vantage-serial-bridge',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Register tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'allocate_vantage_serial',
        description: 'Allocate the next VANTAGE handoff serial number from GLOBAL_VANTAGE_COUNTER via central HTTP server',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'vantage_serial_status',
        description: 'Get the status of the VANTAGE serial allocation HTTP service',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === 'allocate_vantage_serial') {
      const response = await fetch(`${HTTP_SERVER_URL}/allocate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(TIMEOUT),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(data),
          },
        ],
      };
    } else if (name === 'vantage_serial_status') {
      const response = await fetch(`${HTTP_SERVER_URL}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(TIMEOUT),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(data),
          },
        ],
      };
    } else {
      throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            error: 'HANDOFF_SERIAL_UNAVAILABLE',
            status: 'UNAVAILABLE',
            detail: error.message,
          }),
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('VANTAGE Serial MCP Bridge for Claude Desktop started');
  console.error(`HTTP Server URL: ${HTTP_SERVER_URL}`);
  console.error(`Timeout: ${TIMEOUT}ms`);
}

main().catch((error) => {
  console.error('Fatal error in main():', error);
  process.exit(1);
});
