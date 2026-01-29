import { QlikRestClient } from "../qlik/restClient.js";
import { QlikEngineClient } from "../qlik/engineClient.js";
import * as listApps from "./tools/listApps.js";
import * as listSheets from "./tools/listSheets.js";

export type McpRequest = {
  jsonrpc?: string;
  id?: string | number | null;
  method?: string;
  params?: { name?: string; arguments?: Record<string, unknown> };
};

export type McpResponse = {
  jsonrpc: "2.0";
  id: string | number | null;
  result?: unknown;
  error?: { code: number; message: string };
};

const TOOLS: Record<
  string,
  { schema: { name: string; description: string; inputSchema: object }; execute: (a: unknown, args: Record<string, unknown>) => Promise<unknown> }
> = {
  [listApps.name]: {
    schema: {
      name: listApps.name,
      description: listApps.description,
      inputSchema: listApps.inputSchema,
    },
    execute: listApps.execute as (a: unknown, args: Record<string, unknown>) => Promise<unknown>,
  },
  [listSheets.name]: {
    schema: {
      name: listSheets.name,
      description: listSheets.description,
      inputSchema: listSheets.inputSchema,
    },
    execute: listSheets.execute as (a: unknown, args: Record<string, unknown>) => Promise<unknown>,
  },
};

export function createHandler(
  baseUrl: string,
  getToken: () => string | null
) {
  const rest = new QlikRestClient(baseUrl, getToken);

  return {
    async handle(req: McpRequest, tokenOverride: string | null): Promise<McpResponse> {
      const id = req.id ?? null;
      const token = () => tokenOverride ?? getToken();

      if (!req.method) {
        return { jsonrpc: "2.0", id, error: { code: -32600, message: "Missing 'method'" } };
      }

      if (req.method === "initialize") {
        return {
          jsonrpc: "2.0",
          id,
          result: {
            protocolVersion: "2024-11-05",
            capabilities: { tools: {} },
            serverInfo: {
              name: "qlik-mcp-server",
              version: "1.0.0",
              description: "Qlik Cloud MCP – list apps and sheets (read-only)",
            },
          },
        };
      }

      if (req.method === "tools/list") {
        return {
          jsonrpc: "2.0",
          id,
          result: {
            tools: Object.values(TOOLS).map((t) => t.schema),
          },
        };
      }

      if (req.method === "tools/call") {
        const name = req.params?.name;
        const args = (req.params?.arguments ?? {}) as Record<string, unknown>;
        if (!name) {
          return { jsonrpc: "2.0", id, error: { code: -32602, message: "Missing params.name" } };
        }
        const tool = TOOLS[name];
        if (!tool) {
          return { jsonrpc: "2.0", id, error: { code: -32601, message: `Unknown tool: ${name}` } };
        }
        const t = token();
        if (!t?.trim()) {
          return {
            jsonrpc: "2.0",
            id,
            error: {
              code: -32000,
              message: "Missing Qlik token. Set QLIK_TOKEN or Authorization: Bearer <token>.",
            },
          };
        }

        try {
          let out: unknown;
          if (name === listApps.name) {
            out = await tool.execute(rest, args);
          } else {
            const engine = new QlikEngineClient(baseUrl, () => t);
            try {
              out = await tool.execute(engine, args);
            } finally {
              engine.close();
            }
          }
          const text = typeof out === "string" ? out : JSON.stringify(out, null, 2);
          return {
            jsonrpc: "2.0",
            id,
            result: {
              content: [{ type: "text" as const, text }],
            },
          };
        } catch (err) {
          const msg = err instanceof Error ? err.message : String(err);
          return {
            jsonrpc: "2.0",
            id,
            error: { code: -32603, message: msg },
          };
        }
      }

      return {
        jsonrpc: "2.0",
        id,
        error: { code: -32601, message: `Method not found: ${req.method}` },
      };
    },
  };
}
