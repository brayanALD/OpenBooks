// Espejo de backend/app/schemas/catalog.py. Si cambia allí, cambia aquí.

export type Author = { id: string; name: string; slug: string };

export type CategoryRef = { id: string; name: string; slug: string };

export type Category = CategoryRef & { description: string; book_count: number };

export type BookSummary = {
  id: string;
  slug: string;
  title: string;
  author: Author;
  categories: CategoryRef[];
  price_cop: number; // precio de lista
  discount_pct: number;
  final_price_cop: number; // por unidad, con descuento
  shipping_cost_cop: number;
  free_shipping: boolean;
  stock: number;
  in_stock: boolean;
  cover: string;
  cover_width: number;
  cover_height: number;
  cover_blur: string | null;
  featured: boolean;
  bestseller: boolean;
  rating_avg: number | null;
  rating_count: number;
};

export type BookDetail = BookSummary & {
  publisher: string | null;
  pages: number | null;
  language: string | null;
  description: string;
  incomplete: boolean;
};

export type Review = {
  id: string;
  author_name: string;
  rating: number;
  comment: string;
  is_demo: boolean;
  verified: boolean; // de una cuenta que compró el libro
  created_at: string;
  updated_at: string | null;
};

/** Situación de la persona con sesión frente a un libro (GET /books/{slug}/reviews/mine). */
export type MyReview = { can_review: boolean; has_purchased: boolean; review: Review | null };

export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type BookSort = "relevance" | "price_asc" | "price_desc" | "rating" | "title" | "newest";
