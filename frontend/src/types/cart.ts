import type { BookSummary } from "@/types/catalog";

// Espejo de backend/app/schemas/cart.py.

export type CartIssue = "out_of_stock" | "limited_stock" | "quantity_capped";

export type CartLine = {
  book: BookSummary;
  requested_quantity: number;
  quantity: number; // la que acepta el servidor (0 si está agotado)
  max_quantity: number; // mínimo entre stock y máximo por pedido
  unit_price_cop: number;
  line_total_cop: number;
  issue: CartIssue | null;
};

export type CartValidation = {
  lines: CartLine[];
  unavailable_ids: string[];
  item_count: number;
  subtotal_cop: number;
  shipping_cop: number;
  total_cop: number;
  has_issues: boolean;
};
