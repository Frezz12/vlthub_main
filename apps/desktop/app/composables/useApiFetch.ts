const BASE =
  typeof __API_BASE_URL__ !== "undefined" && __API_BASE_URL__
    ? __API_BASE_URL__
    : "http://localhost:8000";

export function useApiFetch<T = any>(url: string, opts?: any): Promise<T> {
  return $fetch<T>(url, { baseURL: BASE, ...opts });
}

export function resolveApiUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  return path.startsWith("/") ? `${BASE}${path}` : path;
}
