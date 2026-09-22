// Solo para el servidor (Server Components y Route Handlers): habla con FastAPI.

export const API_URL = process.env.API_URL ?? "http://localhost:8000/api/v1";

type BackendInit = Omit<RequestInit, "body"> & { json?: unknown; formData?: FormData; token?: string };

/**
 * `fetch` al backend: sin caché y con el token de sesión como `Authorization: Bearer`.
 * El cuerpo es JSON (`json`) o un formulario con archivos (`formData`); con `formData` NO se fija content-type:
 * `fetch` añade el suyo con el separador (boundary) correcto.
 */
export function backendFetch(path: string, { json, formData, token, headers, ...init }: BackendInit = {}) {
  return fetch(`${API_URL}${path}`, {
    cache: "no-store",
    ...init,
    headers: {
      ...(json !== undefined && { "content-type": "application/json" }),
      ...(token && { authorization: `Bearer ${token}` }),
      ...headers,
    },
    body: formData ?? (json !== undefined ? JSON.stringify(json) : undefined),
  });
}
