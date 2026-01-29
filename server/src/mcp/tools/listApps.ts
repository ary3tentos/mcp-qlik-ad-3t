import type { QlikRestClient } from "../../qlik/restClient.js";

export const name = "qlik.list_apps";

export const description =
  "List Qlik Cloud apps. Returns appId, name, spaceId, owner. Use appId with qlik.list_sheets to list sheets. Read-only.";

export const inputSchema = {
  type: "object" as const,
  properties: {
    limit: {
      type: "integer",
      description: "Max number of apps (1–100)",
      minimum: 1,
      maximum: 100,
    },
    next: {
      type: "string",
      description: "Cursor or next-page URL from previous response",
    },
    name: {
      type: "string",
      description: "Filter by name (case-insensitive)",
    },
  },
};

export type NormalizedApp = {
  appId: string;
  name: string;
  spaceId: string;
  owner: string;
};

export async function execute(
  rest: QlikRestClient,
  args: { limit?: number; next?: string; name?: string }
): Promise<{
  apps: NormalizedApp[];
  nextCursor?: string | null;
}> {
  const limit = args.limit ?? 20;
  const res = await rest.listApps({
    limit: Math.min(100, Math.max(1, limit)),
    next: args.next,
    name: args.name,
  });

  const apps: NormalizedApp[] = (res.data ?? []).map((item) => ({
    appId: (item.resourceId ?? item.id ?? "").trim() || "",
    name: (item.name ?? "Unnamed app").trim(),
    spaceId: (item.spaceId ?? "").trim(),
    owner: (item.ownerId ?? "").trim(),
  })).filter((a) => a.appId);

  const nextHref = res.links?.next?.href ?? null;
  return {
    apps,
    nextCursor: nextHref ?? undefined,
  };
}
