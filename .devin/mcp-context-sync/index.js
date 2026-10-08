#!/usr/bin/env node
/**
 * VANTAGE Context Sync MCP Server (stdlib)
 *
 * Local-first context memory MCP server using Node.js native node:sqlite.
 * Provides tools for project registration, memory storage, retrieval, and search.
 *
 * All SQL queries use parameterized statements to prevent injection.
 * Database: ~/.vantage/context-sync.db
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const fs = require('fs').promises;
const path = require('path');
const { DatabaseSync } = require('node:sqlite');

// Database path
const DB_PATH = path.join(process.env.HOME || process.env.USERPROFILE, '.vantage', 'context-sync.db');

/**
 * Get or create a database connection.
 * Uses a module-level singleton so we don't open/close per call.
 */
let dbInstance = null;

function getDb() {
  if (!dbInstance) {
    dbInstance = new DatabaseSync(DB_PATH);
    initDb(dbInstance);
  }
  return dbInstance;
}

function initDb(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS memories (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      key TEXT UNIQUE NOT NULL,
      content TEXT NOT NULL,
      category TEXT,
      project_id TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS projects (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      root_path TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);
    CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project_id);
    CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
  `);
}

// Initialize server
const server = new Server(
  {
    name: 'vantage-context-sync',
    version: '1.0.1',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'project_register',
        description: 'Register a project in the context memory',
        inputSchema: {
          type: 'object',
          properties: {
            id: {
              type: 'string',
              description: 'Unique project identifier',
            },
            name: {
              type: 'string',
              description: 'Project name',
            },
            root_path: {
              type: 'string',
              description: 'Absolute path to project root',
            },
          },
          required: ['id', 'name', 'root_path'],
        },
      },
      {
        name: 'memory_save',
        description: 'Save a memory entry',
        inputSchema: {
          type: 'object',
          properties: {
            key: {
              type: 'string',
              description: 'Unique key for the memory',
            },
            content: {
              type: 'string',
              description: 'Memory content',
            },
            category: {
              type: 'string',
              description: 'Memory category (decision, pattern, fact, error, etc.)',
            },
            project_id: {
              type: 'string',
              description: 'Associated project ID',
            },
          },
          required: ['key', 'content'],
        },
      },
      {
        name: 'memory_get',
        description: 'Retrieve a memory by key',
        inputSchema: {
          type: 'object',
          properties: {
            key: {
              type: 'string',
              description: 'Memory key to retrieve',
            },
          },
          required: ['key'],
        },
      },
      {
        name: 'memory_list',
        description: 'List memories with optional filters',
        inputSchema: {
          type: 'object',
          properties: {
            project_id: {
              type: 'string',
              description: 'Filter by project ID',
            },
            category: {
              type: 'string',
              description: 'Filter by category',
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results',
            },
          },
        },
      },
      {
        name: 'memory_search',
        description: 'Search memories by content (simple text search)',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Search query',
            },
            project_id: {
              type: 'string',
              description: 'Filter by project ID',
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results',
            },
          },
          required: ['query'],
        },
      },
      {
        name: 'memory_delete',
        description: 'Delete a memory by key',
        inputSchema: {
          type: 'object',
          properties: {
            key: {
              type: 'string',
              description: 'Memory key to delete',
            },
          },
          required: ['key'],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const db = getDb();

  try {
    switch (name) {
      case 'project_register': {
        const stmt = db.prepare(
          'INSERT OR REPLACE INTO projects (id, name, root_path) VALUES (?, ?, ?)'
        );
        stmt.run(args.id, args.name, args.root_path);
        return {
          content: [
            {
              type: 'text',
              text: `Project "${args.name}" registered successfully`,
            },
          ],
        };
      }

      case 'memory_save': {
        const stmt = db.prepare(
          'INSERT INTO memories (key, content, category, project_id) VALUES (?, ?, ?, ?) ' +
          'ON CONFLICT(key) DO UPDATE SET ' +
          'content = excluded.content, ' +
          'category = excluded.category, ' +
          'project_id = excluded.project_id, ' +
          'updated_at = CURRENT_TIMESTAMP'
        );
        stmt.run(args.key, args.content, args.category || null, args.project_id || null);
        return {
          content: [
            {
              type: 'text',
              text: `Memory "${args.key}" saved successfully`,
            },
          ],
        };
      }

      case 'memory_get': {
        const stmt = db.prepare('SELECT * FROM memories WHERE key = ?');
        const memory = stmt.get(args.key);
        if (!memory) {
          return {
            content: [
              {
                type: 'text',
                text: `Memory "${args.key}" not found`,
              },
            ],
          };
        }
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(memory, null, 2),
            },
          ],
        };
      }

      case 'memory_list': {
        const conditions = [];
        const params = [];

        if (args.project_id) {
          conditions.push('project_id = ?');
          params.push(args.project_id);
        }
        if (args.category) {
          conditions.push('category = ?');
          params.push(args.category);
        }

        let query = 'SELECT * FROM memories';
        if (conditions.length > 0) {
          query += ' WHERE ' + conditions.join(' AND ');
        }
        query += ' ORDER BY updated_at DESC';

        if (args.limit) {
          query += ' LIMIT ?';
          params.push(args.limit);
        }

        const stmt = db.prepare(query);
        const memories = stmt.all(...params);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(memories, null, 2),
            },
          ],
        };
      }

      case 'memory_search': {
        const conditions = ["content LIKE ?"];
        const params = [`%${args.query}%`];

        if (args.project_id) {
          conditions.push('project_id = ?');
          params.push(args.project_id);
        }

        let query = `SELECT * FROM memories WHERE ${conditions.join(' AND ')}`;
        query += ' ORDER BY updated_at DESC';

        if (args.limit) {
          query += ' LIMIT ?';
          params.push(args.limit);
        }

        const stmt = db.prepare(query);
        const memories = stmt.all(...params);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(memories, null, 2),
            },
          ],
        };
      }

      case 'memory_delete': {
        const stmt = db.prepare('DELETE FROM memories WHERE key = ?');
        const result = stmt.run(args.key);
        if (result.changes === 0) {
          return {
            content: [
              {
                type: 'text',
                text: `Memory "${args.key}" not found`,
              },
            ],
          };
        }
        return {
          content: [
            {
              type: 'text',
              text: `Memory "${args.key}" deleted successfully`,
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    throw new Error(`Tool error [${name}]: ${error.message}`);
  }
});

// Start server
async function main() {
  // Ensure database directory exists
  const dbDir = path.dirname(DB_PATH);
  await fs.mkdir(dbDir, { recursive: true });

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('VANTAGE Context Sync MCP server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
