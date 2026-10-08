#!/usr/bin/env node
/**
 * VANTAGE MCP-SSE-BRIDGE — v2.0
 *
 * Stdio-to-SSE bridge for local MCP servers (mem0-mcp + context-sync).
 *
 * Implements the MCP-over-SSE protocol:
 *   GET  /sse           → SSE stream; first event carries the POST endpoint URI
 *   POST /message       → JSON-RPC forward to the stdio MCP server; result returned
 *                         directly in the HTTP response body
 *   GET  /health        → server health + MCP child process status
 *
 * All endpoints require a valid Bearer token (Authorization: Bearer <secret>).
 * The secret is auto-generated on first run and persisted to ~/.vantage/mcp-secret.txt.
 *
 * No remote Notion writes — all state is local to the M2 host filesystem.
 */

'use strict';

const express = require('express');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// ── Configuration ──────────────────────────────────────────────────────────
const PORT = process.env.PORT || 8080;
const HOST = process.env.HOST || '127.0.0.1';
const SECRET_FILE = path.join(process.env.HOME, '.vantage', 'mcp-secret.txt');
const LOG_DIR = path.join(process.env.HOME, '.vantage', 'logs');

// MCP Server configurations
const MEM0_SERVER = {
  command: 'node',
  args: ['/Users/mauriciomeyran/.npm-global/lib/node_modules/mem0-mcp/dist/bin/mem0-mcp.js'],
  env: {
    MEM0_STORE_PATH: '/Users/mauriciomeyran/.vantage/mem0',
    OLLAMA_BASE_URL: 'http://127.0.0.1:11434',
    MEM0_EMBED_MODEL: 'nomic-embed-text:latest',
    MEM0_OLLAMA_TIMEOUT_MS: '30000',
  },
};

// context-sync is the custom stdio MCP server at .devin/mcp-context-sync/index.js
const CONTEXT_SYNC_SERVER = {
  command: 'node',
  args: [path.resolve(__dirname, '..', 'mcp-context-sync', 'index.js')],
  env: {},
};

// ── Secret management ──────────────────────────────────────────────────────
function getSecret() {
  const secretDir = path.dirname(SECRET_FILE);
  if (!fs.existsSync(secretDir)) {
    fs.mkdirSync(secretDir, { recursive: true });
  }
  if (fs.existsSync(SECRET_FILE)) {
    return fs.readFileSync(SECRET_FILE, 'utf-8').trim();
  }
  const secret = crypto.randomBytes(32).toString('hex');
  fs.writeFileSync(SECRET_FILE, secret, { mode: 0o600 });
  return secret;
}

const SECRET = getSecret();

// ── Logging ──────────────────────────────────────────────────────────────────
function ensureLogDir() {
  if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
  }
}

function log(level, msg) {
  const ts = new Date().toISOString();
  const line = `[${ts}] [${level}] ${msg}`;
  console.error(line);
  ensureLogDir();
  const logFile = path.join(LOG_DIR, 'mcp-sse-bridge.log');
  fs.appendFileSync(logFile, line + '\n');
}

// ── MCP Server Manager ────────────────────────────────────────────────────
class MCPServer {
  constructor(name, config) {
    this.name = name;
    this.command = config.command;
    this.args = config.args;
    this.extraEnv = config.env || {};
    this.process = null;
    this.pendingRequests = new Map();
    this.requestId = 0;
    this.initialized = false;
  }

  start() {
    if (this.process) return;

    const env = { ...process.env, ...this.extraEnv };
    log('INFO', `Starting MCP server: ${this.name} (${this.command} ${this.args.join(' ')})`);

    this.process = spawn(this.command, this.args, {
      env,
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    this.process.stdout.on('data', (data) => {
      this._handleOutput(data);
    });

    this.process.stderr.on('data', (data) => {
      log('DEBUG', `[${this.name}] ${data.toString().trim()}`);
    });

    this.process.on('close', (code) => {
      log('WARN', `MCP server ${this.name} exited with code ${code}`);
      this.process = null;
      this.initialized = false;
      // Reject all pending requests
      for (const [id, pending] of this.pendingRequests) {
        pending.reject(new Error(`MCP server ${this.name} exited unexpectedly`));
      }
      this.pendingRequests.clear();
    });

    // Initialize: send initialize request
    setTimeout(() => {
      if (this.process) {
        this._sendInitialize();
      }
    }, 500);
  }

  async _sendInitialize() {
    try {
      const result = await this.call('initialize', {
        protocolVersion: '2024-11-05',
        capabilities: {
          tools: {},
          prompts: {},
          resources: {},
        },
        clientInfo: {
          name: 'vantage-mcp-sse-bridge',
          version: '2.0.0',
        },
      });
      log('INFO', `MCP server ${this.name} initialized: ${JSON.stringify(result?.result?.serverInfo || {})}`);
      this.initialized = true;

      // Send initialized notification
      this._sendNotification('initialized', {});
    } catch (error) {
      log('WARN', `MCP server ${this.name} initialization failed: ${error.message}`);
    }
  }

  _sendNotification(method, params = {}) {
    if (!this.process) return;
    const msg = { jsonrpc: '2.0', method, params };
    this.process.stdin.write(JSON.stringify(msg) + '\n');
  }

  async call(method, params = {}) {
    if (!this.process) {
      this.start();
      // Wait for process to be ready
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    const id = ++this.requestId;
    const message = {
      jsonrpc: '2.0',
      id,
      method,
      params,
    };

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.pendingRequests.delete(id);
        reject(new Error('MCP request timeout (30s)'));
      }, 30000);

      this.pendingRequests.set(id, { resolve, reject, timeout });

      try {
        this.process.stdin.write(JSON.stringify(message) + '\n');
      } catch (error) {
        clearTimeout(timeout);
        this.pendingRequests.delete(id);
        reject(error);
      }
    });
  }

  _handleOutput(data) {
    const text = data.toString();
    const lines = text.split('\n').filter(line => line.trim());
    for (const line of lines) {
      try {
        const message = JSON.parse(line);
        if (message.id !== undefined && this.pendingRequests.has(message.id)) {
          const pending = this.pendingRequests.get(message.id);
          clearTimeout(pending.timeout);
          this.pendingRequests.delete(message.id);
          pending.resolve(message);
        } else if (message.method) {
          // Server-initiated notification — log it
          log('DEBUG', `[${this.name}] Notification: ${message.method}`);
        }
      } catch (error) {
        // Ignore non-JSON lines (stdout/stderr noise)
      }
    }
  }

  stop() {
    if (this.process) {
      log('INFO', `Stopping MCP server: ${this.name}`);
      this.process.kill();
      this.process = null;
    }
    this.initialized = false;
  }

  isRunning() {
    return !!this.process && this.process.pid && !this.process.killed;
  }

  getStatus() {
    return {
      running: this.isRunning(),
      initialized: this.initialized,
      pendingRequests: this.pendingRequests.size,
    };
  }
}

// ── Initialize MCP servers ─────────────────────────────────────────────────
const mcpServers = {
  mem0: new MCPServer('mem0', MEM0_SERVER),
  'context-sync': new MCPServer('context-sync', CONTEXT_SYNC_SERVER),
};

// ── Express app ────────────────────────────────────────────────────────────
const app = express();
app.use(express.json({ limit: '10mb' }));

// Bearer token middleware
function requireBearerToken(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing or invalid Authorization header. Expected: Authorization: Bearer <token>' });
  }
  const token = authHeader.substring(7);
  if (token !== SECRET) {
    return res.status(403).json({ error: 'Invalid token' });
  }
  next();
}

// Health check (no auth — needed for initial connectivity checks)
app.get('/health', (req, res) => {
  const servers = {};
  for (const [name, server] of Object.entries(mcpServers)) {
    servers[name] = server.getStatus();
  }
  res.json({
    status: 'ok',
    port: PORT,
    servers,
  });
});

// SSE endpoint — MCP-over-SSE transport
app.get('/sse', requireBearerToken, (req, res) => {
  const { server = 'mem0' } = req.query;

  if (!mcpServers[server]) {
    return res.status(404).json({ error: `Unknown server: ${server}` });
  }

  // SSE headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', 'null');

  const sessionId = crypto.randomUUID();

  // Send endpoint discovery message
  const endpoint = `/message?server=${server}&sessionId=${sessionId}`;
  const endpointData = JSON.stringify({ type: 'endpoint', url: endpoint, sessionId });
  res.write(`data: ${endpointData}\n\n`);

  // Start MCP server if not running
  if (!mcpServers[server].isRunning()) {
    mcpServers[server].start();
  }

  log('INFO', `SSE client connected: server=${server}, sessionId=${sessionId}`);

  // Handle client disconnect
  req.on('close', () => {
    log('INFO', `SSE client disconnected: sessionId=${sessionId}`);
  });

  // Keep connection alive with periodic heartbeat
  const heartbeat = setInterval(() => {
    if (res.writableEnded) {
      clearInterval(heartbeat);
      return;
    }
    res.write(`data: ${JSON.stringify({ type: 'heartbeat', sessionId })}\n\n`);
  }, 30000);

  req.on('close', () => {
    clearInterval(heartbeat);
  });
});

// JSON-RPC message endpoint — forwards to stdio MCP servers
app.post('/message', requireBearerToken, async (req, res) => {
  const { server = 'mem0', sessionId } = req.query;

  if (!mcpServers[server]) {
    return res.status(404).json({ error: `Unknown server: ${server}` });
  }

  const rpcBody = req.body;

  if (!rpcBody || !rpcBody.jsonrpc || !rpcBody.jsonrpc === '2.0') {
    return res.status(400).json({ error: 'Invalid JSON-RPC request body' });
  }

  // For notifications (no id), don't return a response
  if (rpcBody.id === undefined) {
    if (rpcBody.method) {
      mcpServers[server]._sendNotification(rpcBody.method, rpcBody.params || {});
    }
    return res.status(200).json({ status: 'accepted' });
  }

  // Forward request to the MCP stdio server
  try {
    const result = await mcpServers[server].call(rpcBody.method, rpcBody.params || {});
    res.json(result);
  } catch (error) {
    log('ERROR', `MCP call failed: server=${server}, method=${rpcBody.method}, error=${error.message}`);
    res.status(500).json({
      jsonrpc: '2.0',
      id: rpcBody.id,
      error: {
        code: -32603,
        message: error.message || 'Internal error',
      },
    });
  }
});

// Root endpoint — service info
app.get('/', requireBearerToken, (req, res) => {
  res.json({
    service: 'vantage-mcp-sse-bridge',
    version: '2.0.0',
    endpoints: {
      sse: 'GET /sse?server=mem0|context-sync',
      message: 'POST /message?server=mem0|context-sync',
      health: 'GET /health',
    },
    servers: Object.keys(mcpServers),
  });
});

// Start server
const httpServer = app.listen(PORT, HOST, () => {
  log('INFO', `VANTAGE MCP SSE Bridge listening on http://${HOST}:${PORT}`);
  log('INFO', `Available servers: ${Object.keys(mcpServers).join(', ')}`);
  log('INFO', `Secret configured at ${SECRET_FILE}`);
  console.error(`VANTAGE MCP SSE Bridge listening on http://${HOST}:${PORT}`);
  console.error(`Endpoints:`);
  console.error(`  SSE:     GET  http://${HOST}:${PORT}/sse?server=<mem0|context-sync>`);
  console.error(`  Message: POST http://${HOST}:${PORT}/message?server=<mem0|context-sync>`);
  console.error(`  Health:  GET  http://${HOST}:${PORT}/health`);
  console.error(`  Config:  Authorization: Bearer <token>`);
  console.error(`(Token stored in ${SECRET_FILE} — do not share)`);
});

// ── Graceful shutdown ──────────────────────────────────────────────────────
function shutdown(signal) {
  log('INFO', `Received ${signal}, shutting down...`);
  for (const server of Object.values(mcpServers)) {
    server.stop();
  }
  httpServer.close(() => {
    log('INFO', 'HTTP server closed');
    process.exit(0);
  });
  // Force shutdown after 5 seconds
  setTimeout(() => {
    log('ERROR', 'Forced shutdown after timeout');
    process.exit(1);
  }, 5000);
}

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));
