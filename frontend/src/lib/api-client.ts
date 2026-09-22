import type { BookDetail, BookSort, BookSummary, Category, Page, Review } from "@/types/catalog";

import { API_URL } from "@/lib/backend";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type Query = Record<string, string | number | boolean | undefined>;

async function request<T>(path: string, query: Query = {}): Promise<T> {
  const url = new URL(`${API_URL}${path}`);
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
  }
  // El catálogo cambia desde el panel de administración: sin caché mientras el backend sea local.
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new ApiError(res.status, `${res.status} ${res.statusText} en ${path}`);
  return (await res.json()) as T;
}

/** Devuelve null si el recurso no existe; cualquier otro error se propaga. */
async function orNull<T>(promise: Promise<T>): Promise<T | null> {
  try {
    return await promise;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export type BookListParams = {
  q?: string;
  category?: string;
  author?: string;
  min_price?: number;
  max_price?: number;
  free_shipping?: boolean;
  on_sale?: boolean;
  in_stock?: boolean;
  featured?: boolean;
  bestseller?: boolean;
  sort?: BookSort;
  page?: number;
  page_size?: number;
};

export const getBooks = (params: BookListParams = {}) => request<Page<BookSummary>>("/books", params);

export const getBook = (slug: string) => orNull(request<BookDetail>(`/books/${encodeURIComponent(slug)}`));

export const getRelatedBooks = (slug: string, limit = 6) =>
  request<BookSummary[]>(`/books/${encodeURIComponent(slug)}/related`, { limit });

export const getReviews = (slug: string) => request<Review[]>(`/books/${encodeURIComponent(slug)}/reviews`);

export const getCategories = () => request<Category[]>("/categories");

export const getCategory = (slug: string) => orNull(request<Category>(`/categories/${encodeURIComponent(slug)}`));
