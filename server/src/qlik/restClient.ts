const REST_TIMEOUT_MS = 30_000;
const REST_RETRIES = 2;

export type ListAppsParams = {
  limit?: number;
  next?: string;
  name?: string;
};

export type ListAppsResponse = {
  data: Array<{
    id?: string;
    resourceId?: string;
    name?: string;
    ownerId?: string;
    spaceId?: string;
    resourceType?: string;
    [k: string]: unknown;
  }>;
  links?: {
    next?: { href?: string | null };
    prev?: { href?: string | null };
  };
};

export class QlikRestClient {
  constructor(
    private baseUrl: string,
    private getToken: () => string | null
  ) {}

  private async fetchWithRetry(
    url: string,
    opts: RequestInit,
    retries = REST_RETRIES
  ): Promise<Response> {
    const token = this.getToken();
    if (!token?.trim()) {
      throw new Error("Qlik API token is required. Set QLIK_TOKEN or pass Bearer.");
    }
    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), REST_TIMEOUT_MS);
    try {
      const res = await fetch(url, {
        ...opts,
        signal: controller.signal,
        headers: {
          Authorization: `Bearer ${token.trim()}`,
          "Content-Type": "application/json",
          ...(opts.headers as Record<string, string>),
        },
      });
      if ((res.status === 429 || res.status >= 500) && retries > 0) {
        await new Promise((r) => setTimeout(r, 1000));
        return this.fetchWithRetry(url, opts, retries - 1);
      }
      return res;
    } finally {
      clearTimeout(t);
    }
  }

  async listApps(params: ListAppsParams = {}): Promise<ListAppsResponse> {
    const base = `${this.baseUrl}/api/v1/items`;
    const url =
      params.next && params.next.startsWith("http")
        ? params.next
        : new URL(base);

    if (!params.next || !params.next.startsWith("http")) {
      const search = new URLSearchParams();
      search.set("resourceType", "app");
      search.set("limit", String(Math.min(100, Math.max(1, params.limit ?? 20))));
      if (params.name) search.set("name", params.name);
      (url as URL).search = search.toString();
    }

    const href = typeof url === "string" ? url : url.toString();
    const res = await this.fetchWithRetry(href, { method: "GET" });

    if (!res.ok) {
      let detail: string;
      try {
        const j = await res.json();
        detail = JSON.stringify(j);
      } catch {
        detail = await res.text();
      }
      if (res.status === 401) {
        throw new Error("Invalid or expired Qlik token. Check QLIK_TOKEN.");
      }
      if (res.status === 404) {
        throw new Error(`Qlik API not found. Check tenant URL: ${this.baseUrl}`);
      }
      throw new Error(`Qlik REST error (${res.status}): ${detail}`);
    }

    return (await res.json()) as ListAppsResponse;
  }
}
