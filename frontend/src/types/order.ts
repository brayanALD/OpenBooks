// Espejo de backend/app/schemas/orders.py (OrderOut).

export type OrderStatus = "pending" | "paid" | "failed" | "shipped" | "delivered" | "cancelled";

export type OrderItem = {
  book_id: string;
  title: string;
  author_name: string;
  cover: string;
  unit_price_cop: number;
  quantity: number;
  line_total_cop: number;
};

export type Order = {
  id: string;
  number: string; // OB-000001
  status: OrderStatus;
  items: OrderItem[];
  subtotal_cop: number;
  shipping_cop: number;
  total_cop: number;
  shipping: { recipient_name: string; phone: string | null; line: string; city: string; notes: string | null };
  payment: {
    status: "pending" | "approved" | "declined";
    method: string | null; // "Visa •••• 4242": nunca el número completo
    reference: string | null;
    failure_reason: string | null;
  };
  created_at: string;
};

export const ORDER_STATUS_LABEL: Record<OrderStatus, string> = {
  pending: "Procesando",
  paid: "Pagado",
  failed: "Pago fallido",
  shipped: "Enviado",
  delivered: "Entregado",
  cancelled: "Cancelado",
};
