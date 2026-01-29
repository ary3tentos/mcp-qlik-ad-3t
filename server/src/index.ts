import "dotenv/config";
import express, { Request, Response } from "express";
import { getToken, getTenant } from "./auth/index.js";
import { createHandler } from "./mcp/handler.js";

const port = Number(process.env.MCP_SERVER_PORT ?? "8082");
const host = process.env.MCP_SERVER_HOST ?? "0.0.0.0";

const baseUrl = getTenant();
const handler = createHandler(baseUrl, getToken);

const app = express();
app.use(express.json({ limit: "1mb" }));

function tokenFromRequest(req: Request): string | null {
  const key = req.headers["x-api-key"];
  if (typeof key === "string" && key.trim()) return key.trim();
  const auth = req.headers.authorization;
  if (typeof auth === "string" && auth.toLowerCase().startsWith("bearer ")) {
    return auth.slice(7).trim();
  }
  return null;
}

app.get("/", (_req: Request, res: Response) => {
  res.json({
    service: "Qlik Cloud MCP Server",
    routes: { "GET /health": "Health check", "POST /mcp": "MCP JSON-RPC (initialize, tools/list, tools/call)" },
  });
});

app.get("/health", (_req: Request, res: Response) => {
  res.json({ status: "ok" });
});

app.post("/mcp", async (req: Request, res: Response) => {
  let body: unknown;
  try {
    body = req.body;
    if (!body || typeof body !== "object") {
      return res.status(400).json({
        jsonrpc: "2.0",
        id: null,
        error: { code: -32700, message: "Invalid JSON" },
      });
    }
  } catch {
    return res.status(400).json({
      jsonrpc: "2.0",
      id: null,
      error: { code: -32700, message: "Invalid JSON" },
    });
  }

  const method = (body as { method?: string }).method;
  const token = tokenFromRequest(req);
  const out = await handler.handle(body as Parameters<typeof handler.handle>[0], token);
  const err = (out as { error?: { code?: number } }).error;
  console.log(JSON.stringify({ method, hasToken: !!token, errorCode: err?.code ?? null }));
  res.json(out);
});

if (!baseUrl) {
  console.warn("QLIK_TENANT (or QLIK_CLOUD_TENANT_URL) not set; list_apps/list_sheets will fail until configured.");
}

app.listen(port, host, () => {
  console.log(`Qlik MCP Server listening on ${host}:${port}`);
});
