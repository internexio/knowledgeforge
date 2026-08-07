---
title: VS Code Extension Local-Server Spawn-and-Capture Auth Pattern
source_mode: builder
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-11
domain: integration
topic: desktop-extension-api-integration
tags: vscode, local-server, auth-token, sse-streaming, child-process, http-client
related_entries: []
---

# VS Code Extension Local-Server Spawn-and-Capture Auth Pattern

## What it is

A framework for VS Code extensions (and similar desktop-embedded contexts) that need to:
1. Spawn a local HTTP+SSE server as a child process
2. Establish a shared secret without user intervention or static config files
3. Proxy all API calls through that server, keeping the API key server-side

The key insight: the server generates a per-launch random token, prints it to stdout, and the extension captures it from stdout before any requests are made. The token is never stored on disk, never visible in the webview, and never passed to any client that isn't the extension host.

## Implementation pattern (TypeScript/Node.js)

Extension side (ServerProxy.ts):
```typescript
export class ServerProxy {
  private proc: ChildProcess | null = null;
  private token = '';
  private readonly readyPromise: Promise<void>;

  constructor(private readonly serverScript: string, private readonly apiKey: string, private readonly port = 9877) {
    this.readyPromise = new Promise((resolve, reject) => { /* store resolve/reject */ });
  }

  start(): void {
    this.proc = spawn('node', [this.serverScript], {
      env: { ...process.env, MY_SERVICE_API_KEY: this.apiKey, MY_SERVICE_PORT: String(this.port) }
    });

    let tokenCaptured = false;
    this.proc.stdout?.on('data', (chunk: Buffer) => {
      for (const line of chunk.toString().split('\n')) {
        if (line.startsWith('MY_SERVICE_TOKEN=')) {
          this.token = line.slice('MY_SERVICE_TOKEN='.length).trim();
          tokenCaptured = true;
        }
        if (line.includes('listening') && tokenCaptured) {
          this.readyResolve();
        }
      }
    });
  }

  // All HTTP calls await this.readyPromise before proceeding
  async createSession(): Promise<string> {
    await this.readyPromise;
    // ... http.request with Authorization: Bearer ${this.token}
  }
}
```

Server side (Node.js):
```typescript
const token = randomBytes(32).toString('hex');
// ... set up HTTP server ...
server.listen(port, '127.0.0.1', () => {
  process.stdout.write(`kf-server listening on http://127.0.0.1:${port}\n`);
  process.stdout.write(`MY_SERVICE_TOKEN=${token}\n`);
});
```

## SSE streaming (async generator pattern)

The extension uses Node.js's async iteration over IncomingMessage (Node 12+ supports `for await (const chunk of res)`):

```typescript
async *sendStream(sessionId: string, content: string): AsyncGenerator<SSEEvent> {
  const res = await new Promise<IncomingMessage>((resolve, reject) => {
    const req = http.request({ hostname: '127.0.0.1', port: this.port, path: '...', method: 'POST',
      headers: { Authorization: `Bearer ${this.token}`, ... } }, resolve);
    req.on('error', reject);
    req.write(body); req.end();
  });

  let buf = '', currentEvent = '';
  for await (const chunk of res as AsyncIterable<Buffer>) {
    buf += chunk.toString();
    const lines = buf.split('\n'); buf = lines.pop() ?? '';
    for (const line of lines) {
      if (line.startsWith('event: ')) currentEvent = line.slice(7).trim();
      else if (line.startsWith('data: ')) {
        yield { event: currentEvent, data: JSON.parse(line.slice(6)) } as SSEEvent;
        currentEvent = '';
      }
    }
  }
}
```

## Security properties

- Server binds to 127.0.0.1 only — no network exposure
- Host header validation in server prevents DNS rebinding attacks
- Token is per-launch random (32 bytes hex) — no static secret in config
- API key never leaves the server process — webview/browser clients only see the session token flow
- Cancel: `currentReq.destroy()` immediately aborts the HTTP request, plus a fire-and-forget POST to `/cancel` endpoint

## When This Applies

- Desktop extensions (VS Code, JetBrains, Electron) that need to call an external API but want to keep the API key server-side
- Scenarios where the webview/renderer runs in a sandboxed context and cannot hold secrets
- Any "extension as thin UI client, local server as backend" architecture where ephemeral session tokens are preferable to stored credentials
- Multi-window or multi-tab scenarios where a single server instance mediates access

## When This Does NOT Apply

- Remote/cloud deployments — the server is localhost-only
- Cases where the extension host already has a secure credential store (e.g., VS Code's `secrets` API for simple string storage without a separate process)
- Multi-user scenarios — one server instance per extension activation, not shared across users
- Scenarios where latency to a local server is prohibitive (SSE streaming is inherently streaming, not request-response)

## Source Context

Implemented in kf-vscode (source_mode: builder, session: kf-vscode-phase4-kf-plj) wiring the KnowledgeForge VSCode extension to the kf-plj backend server. TypeScript, typechecks clean, both server (ESM/Node16) and extension (CommonJS) verified at commit 834ace8.
