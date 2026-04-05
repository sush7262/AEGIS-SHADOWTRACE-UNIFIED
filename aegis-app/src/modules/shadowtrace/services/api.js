/**
 * API base: set VITE_API_URL (e.g. http://127.0.0.1:8000) or rely on Vite /api proxy.
 */
export function apiUrl(path) {
  // In the unified project, ShadowTrace APIs are under /api/shadowtrace
  // The React app proxies /api to http://localhost:8000
  const base = process.env.REACT_APP_API_URL || "";
  const prefix = "/api/shadowtrace";
  if (base) {
    return `${base.replace(/\/$/, "")}${prefix}${path.startsWith("/") ? path : `/${path}`}`;
  }
  return `${prefix}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function fetchHealth() {
  let r;
  try {
    r = await fetch(apiUrl("/health"));
  } catch (e) {
    throw new Error(
      `Network error calling ${apiUrl("/health")}. Use "npm run dev" (not file://) and start FastAPI on the proxy port (default 8080). ${e?.message || ""}`
    );
  }
  if (!r.ok) throw new Error(await readApiError(r));
  return r.json();
}

async function readApiError(r) {
  const text = await r.text();
  try {
    const j = JSON.parse(text);
    if (j?.detail) {
      if (Array.isArray(j.detail)) {
        return j.detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
      }
      return String(j.detail);
    }
  } catch {
    /* plain text */
  }
  return text || `${r.status} ${r.statusText}`;
}

const fetchOpts = { cache: "no-store" };

export async function generateData(body = {}) {
  const r = await fetch(apiUrl("/generate-data"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    ...fetchOpts,
  });
  if (!r.ok) throw new Error(await readApiError(r));
  return r.json();
}

export async function analyzeLogs(logs) {
  const r = await fetch(apiUrl("/analyze"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ logs }),
    ...fetchOpts,
  });
  if (!r.ok) throw new Error(await readApiError(r));
  return r.json();
}

export async function fetchGraph() {
  const r = await fetch(apiUrl("/graph"));
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function fetchSummary() {
  const r = await fetch(apiUrl("/summary"));
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function fetchIngestStatus() {
  const r = await fetch(apiUrl("/ingest/status"), { ...fetchOpts });
  if (!r.ok) throw new Error(await readApiError(r));
  return r.json();
}

export async function fetchFullSnapshot() {
  const r = await fetch(apiUrl("/snapshot"), { ...fetchOpts });
  if (!r.ok) throw new Error(await readApiError(r));
  return r.json();
}

/**
 * @param {File} file
 * @param {"replace"|"append"} mode
 */
export async function uploadIngestFile(file, mode = "replace") {
  const fd = new FormData();
  fd.append("file", file);
  const q = new URLSearchParams({ mode });
  const r = await fetch(`${apiUrl("/ingest/upload")}?${q}`, {
    method: "POST",
    body: fd,
    ...fetchOpts,
  });
  if (!r.ok) throw new Error(await readApiError(r));
  return r.json();
}

export async function clearIngestBuffer() {
  const r = await fetch(apiUrl("/ingest/buffer"), { method: "DELETE", ...fetchOpts });
  if (!r.ok) throw new Error(await readApiError(r));
  return r.json();
}
