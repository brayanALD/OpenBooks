// Solo para el servidor: datos del panel de administración.

import { notFound } from "next/navigation";
import { backendFetch } from "@/lib/backend";
import { getSessionToken, requireUser } from "@/lib/session";
import type { Review } from "@/types/catalog";
import type { AdminBook, AdminBookPage, AdminOrder, AdminPage, AdminSummary } from "@/types/admin";
import type { User } from "@/types/user";

/**
 * Para páginas de administración. Sin sesión redirige al login; con sesión de cliente responde 404,
 * como si `/admin` no existiera. Es la comprobación de verdad: el proxy solo mira que haya cookie,
 * y el backend vuelve a exigir el rol en cada endpoint.
 */
export async function requireAdmin(returnTo: string): Promise<User> {
  const user = await requireUser(returnTo);
  if (user.role !== "admin") notFound();
  return user;
}

async function adminGet<T>(path: string, query: Record<string, string | number | boolean | undefined> = {}): Promise<T | null> {
  const token = await getSessionToken();
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) if (value !== undefined && value !== "") params.set(key, String(value));
  const qs = params.toString();
  const response = await backendFetch(`/admin${path}${qs ? `?${qs}` : ""}`, { token });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Error ${response.status} al pedir ${path} al servidor`);
  return (await response.json()) as T;
}

export const getAdminSummary = () => adminGet<AdminSummary>("/summary") as Promise<AdminSummary>;

export const getAdminBooks = (query: { q?: string; active?: boolean; low_stock?: boolean; sort?: "stock_asc" | "stock_desc"; page?: number }) =>
  adminGet<AdminBookPage>("/books", { ...query, page_size: 15 }) as Promise<AdminBookPage>;

export const getAdminBook = (id: string) => adminGet<AdminBook>(`/books/${encodeURIComponent(id)}`);

export const getAdminOrders = (query: { status?: string; q?: string; page?: number }) =>
  adminGet<AdminPage<AdminOrder>>("/orders", { ...query, page_size: 15 }) as Promise<AdminPage<AdminOrder>>;

export const getAdminOrder = (id: string) => adminGet<AdminOrder>(`/orders/${encodeURIComponent(id)}`);

export const getAdminBookReviews = (bookId: string) => adminGet<Review[]>(`/books/${encodeURIComponent(bookId)}/reviews`);
