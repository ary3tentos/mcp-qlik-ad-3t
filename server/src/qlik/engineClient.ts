import WebSocket from "ws";

const WS_TIMEOUT_MS = 25_000;

type JsonRpcRequest = {
  jsonrpc: "2.0";
  id: number;
  method: string;
  params?: unknown[];
};

type JsonRpcResponse = {
  jsonrpc: "2.0";
  id: number;
  result?: unknown;
  error?: { code?: string | number; message?: string };
};

export type SheetItem = {
  sheetId: string;
  title: string;
  description: string;
  published: boolean;
};

export class QlikEngineClient {
  private ws: WebSocket | null = null;
  private nextId = 1;
  private pending = new Map<number, { resolve: (v: JsonRpcResponse) => void; reject: (e: Error) => void }>();

  constructor(
    private baseUrl: string,
    private getToken: () => string | null
  ) {}

  private wsUrl(appId: string): string {
    const wss = this.baseUrl.replace(/^https:\/\//, "wss://").replace(/^http:\/\//, "ws://");
    return `${wss}/app/${appId}`;
  }

  private connect(appId: string): Promise<WebSocket> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return Promise.resolve(this.ws);
    }
    const token = this.getToken();
    if (!token?.trim()) {
      return Promise.reject(new Error("Qlik API token is required for Engine."));
    }
    const url = this.wsUrl(appId);
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(url, {
        headers: { Authorization: `Bearer ${token.trim()}` },
      });
      const t = setTimeout(() => {
        ws.removeAllListeners();
        ws.close();
        reject(new Error("Engine WebSocket connection timeout."));
      }, WS_TIMEOUT_MS);
      ws.on("open", () => {
        clearTimeout(t);
        this.ws = ws;
        ws.on("message", (data: Buffer | string) => {
          try {
            const msg = JSON.parse(data.toString()) as JsonRpcResponse;
            const p = this.pending.get(msg.id as number);
            if (p) {
              this.pending.delete(msg.id as number);
              p.resolve(msg);
            }
          } catch {
            // ignore parse errors for non-request responses
          }
        });
        resolve(ws);
      });
      ws.on("error", (err) => {
        clearTimeout(t);
        reject(err);
      });
      ws.on("close", () => {
        this.ws = null;
      });
    });
  }

  private send(method: string, params: unknown[] = []): Promise<JsonRpcResponse> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error("Engine WebSocket not open."));
        return;
      }
      const id = this.nextId++;
      const req: JsonRpcRequest = { jsonrpc: "2.0", id, method, params };
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify(req));
    });
  }

  async getSheets(appId: string): Promise<SheetItem[]> {
    const ws = await this.connect(appId);
    const openRes = await this.send("OpenDoc", [appId]);
    if (openRes.error) {
      const msg = openRes.error.message ?? String(openRes.error);
      throw new Error(`Engine OpenDoc failed: ${msg}`);
    }
    const getRes = await this.send("GetSheets", []);
    if (getRes.error) {
      const msg = getRes.error.message ?? String(getRes.error);
      if (String(getRes.error.code ?? "").includes("QEP-104") || String(msg).includes("QEP-104")) {
        throw new Error("Engine auth/permission error (QEP-104). Check token has Engine access.");
      }
      throw new Error(`Engine GetSheets failed: ${msg}`);
    }

    let raw: { qItems?: Array<{ qInfo?: { qId?: string }; qMeta?: { title?: string; description?: string; published?: boolean } } } | undefined;
    const r = getRes.result;
    if (typeof r === "number") {
      const layoutRes = await this.send("GetLayout", [r]);
      if (layoutRes.error) throw new Error(`Engine GetLayout failed: ${layoutRes.error.message ?? layoutRes.error}`);
      raw = layoutRes.result as typeof raw;
    } else {
      raw = r as typeof raw;
    }
    const items = raw?.qItems ?? [];
    return items.map((s) => ({
      sheetId: s.qInfo?.qId ?? "",
      title: s.qMeta?.title ?? "",
      description: s.qMeta?.description ?? "",
      published: Boolean(s.qMeta?.published),
    }));
  }

  close(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    for (const p of this.pending.values()) {
      p.reject(new Error("Engine client closed."));
    }
    this.pending.clear();
  }
}
