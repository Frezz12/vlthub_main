declare const __API_BASE_URL__: string;

const API_BASE_URL =
  typeof __API_BASE_URL__ !== "undefined" && __API_BASE_URL__
    ? __API_BASE_URL__
    : "https://vlthub.ru";

export function useApi() {
  const auth = useAuthStore();

  function getHeaders(skipContentType = false): Record<string, string> {
    const headers: Record<string, string> = {};
    if (!skipContentType) {
      headers["Content-Type"] = "application/json";
    }
    if (auth.accessToken) {
      headers["Authorization"] = `Bearer ${auth.accessToken}`;
    }
    return headers;
  }

  async function request<T>(
    url: string,
    options: RequestInit = {},
  ): Promise<T> {
    const isFormData = options.body instanceof FormData;
    const res = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers: { ...getHeaders(isFormData), ...options.headers },
    });

    if (res.status === 401) {
      const refreshed = await auth.refresh();
      if (refreshed) {
        return request<T>(url, options);
      }
      throw new Error("Unauthorized");
    }

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      const detail = error.detail;
      const message = Array.isArray(detail)
        ? detail.map((d: any) => d.msg).join("; ")
        : detail || "Request failed";
      throw new Error(message);
    }

    if (res.status === 204) return undefined as T;
    return res.json();
  }

  return {
    get: <T>(url: string) => request<T>(url),
    post: <T>(url: string, body?: unknown) =>
      request<T>(url, {
        method: "POST",
        body: body ? JSON.stringify(body) : undefined,
      }),
    patch: <T>(url: string, body?: unknown) =>
      request<T>(url, {
        method: "PATCH",
        body: body ? JSON.stringify(body) : undefined,
      }),
    delete: <T>(url: string) => request<T>(url, { method: "DELETE" }),
    upload: <T>(url: string, formData: FormData) =>
      request<T>(url, {
        method: "POST",
        body: formData,
        headers: {}, // let browser set content-type
      }),
  };
}
