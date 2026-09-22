// Solo para el servidor: recomendaciones de portada. El backend decide el modo (genérico o personalizado)
// según si hay sesión y compras pagadas; aquí solo se reenvía el token si existe.

import { backendFetch } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";
import type { BookSummary } from "@/types/catalog";

export async function getRecommendedBooks(limit = 8): Promise<BookSummary[]> {
  const token = await getSessionToken();
  const response = await backendFetch(`/books/recommended?limit=${limit}`, { token });
  if (!response.ok) throw new Error(`No se pudieron cargar las recomendaciones (${response.status})`);
  return (await response.json()) as BookSummary[];
}
