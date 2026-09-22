// Solo para el servidor: el librero (libros comprados) del usuario con sesión.

import { backendFetch } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";
import type { Library } from "@/types/library";

export async function getMyLibrary(): Promise<Library> {
  const token = await getSessionToken();
  if (!token) return { items: [], unavailable: [] };
  const response = await backendFetch("/library", { token });
  if (!response.ok) throw new Error(`No se pudo cargar el librero (${response.status})`);
  return (await response.json()) as Library;
}
