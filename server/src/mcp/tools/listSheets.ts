import type { QlikEngineClient, SheetItem } from "../../qlik/engineClient.js";

export const name = "qlik.list_sheets";

export const description =
  "List sheets (tabs) of a Qlik app. Returns sheetId, title, description, published. Read-only.";

export const inputSchema = {
  type: "object" as const,
  properties: {
    appId: {
      type: "string",
      description: "App ID (resourceId from qlik.list_apps)",
    },
  },
  required: ["appId"] as const,
};

export async function execute(
  engine: QlikEngineClient,
  args: { appId: string }
): Promise<SheetItem[]> {
  const appId = args.appId?.trim();
  if (!appId) {
    throw new Error("appId is required");
  }
  const sheets = await engine.getSheets(appId);
  return sheets;
}
