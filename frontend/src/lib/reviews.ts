// Solo para el servidor: situación de la persona con sesión frente a las reseñas de un libro.

import { backendFetch } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";
import type { MyReview } from "@/types/catalog";

/** null si no hay sesión (o la API no responde): la ficha se muestra igual, sin el formulario. */
export async function getMyReviewStatus(slug: string): Promise<MyReview | null> {
  const token = await getSessionToken();
  if (!token) return null;
  try {
    const response = await backendFetch(`/books/${encodeURIComponent(slug)}/reviews/mine`, { token });
    return response.ok ? ((await response.json()) as MyReview) : null;
  } catch {
    return null;
  }
}
