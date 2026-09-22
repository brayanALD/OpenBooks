// Solo para el servidor: pedidos del usuario con sesión.

import { backendFetch } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";
import type { Order } from "@/types/order";

export async function getMyOrders(): Promise<Order[]> {
  const token = await getSessionToken();
  if (!token) return [];
  const response = await backendFetch("/orders", { token });
  if (!response.ok) throw new Error(`No se pudieron cargar los pedidos (${response.status})`);
  return (await response.json()) as Order[];
}

/** null si no existe o no es del usuario (el backend responde 404 en ambos casos). */
export async function getMyOrder(id: string): Promise<Order | null> {
  const token = await getSessionToken();
  if (!token) return null;
  const response = await backendFetch(`/orders/${encodeURIComponent(id)}`, { token });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`No se pudo cargar el pedido (${response.status})`);
  return (await response.json()) as Order;
}
