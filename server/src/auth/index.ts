import "dotenv/config";

export function getToken(): string | null {
  const raw = process.env.QLIK_TOKEN ?? process.env.QLIK_CLOUD_API_KEY;
  if (!raw || typeof raw !== "string") return null;
  const t = raw.trim();
  return t.length > 0 ? t : null;
}

export function getTenant(): string {
  const u =
    process.env.QLIK_TENANT ??
    process.env.QLIK_CLOUD_TENANT_URL ??
    "";
  return u.replace(/\/$/, "");
}
