// Espejo de backend/app/schemas/admin.py.

import type { Order } from "@/types/order";

export type AdminBook = {
  id: string;
  slug: string;
  title: string;
  author_name: string;
  category_ids: string[];
  publisher: string | null;
  pages: number | null;
  language: string | null;
  description: string;
  price_cop: number;
  discount_pct: number;
  final_price_cop: number;
  shipping_cost_cop: number;
  stock: number;
  cover: string;
  cover_width: number;
  cover_height: number;
  featured: boolean;
  bestseller: boolean;
  active: boolean;
  incomplete: boolean;
  created_at: string;
};

export type AdminPage<T> = { items: T[]; total: number; page: number; page_size: number; pages: number };

export type AdminBookPage = AdminPage<AdminBook> & { authors: string[] };

export type AdminOrder = Order & { customer: { name: string; email: string } | null };

export type AdminSummary = {
  books: { total: number; active: number; hidden: number; out_of_stock: number; low_stock: number };
  orders: { by_status: Record<string, number>; revenue_cop: number };
};

export type CoverUpload = { cover: string; cover_width: number; cover_height: number; cover_blur: string };

/** Estados a los que un administrador puede llevar un pedido (espejo de TRANSITIONS del backend). */
export const NEXT_STATUSES: Record<string, ("shipped" | "delivered" | "cancelled")[]> = {
  paid: ["shipped", "cancelled"],
  shipped: ["delivered"],
};
