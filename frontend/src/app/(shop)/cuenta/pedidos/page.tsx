import type { Metadata } from "next";
import Link from "next/link";
import { ChevronRight, PackageOpen } from "lucide-react";
import { OrderStatusBadge } from "@/components/checkout/OrderStatusBadge";
import { ButtonLink } from "@/components/ui/Button";
import { formatCOP, formatDateTime } from "@/lib/format";
import { getMyOrders } from "@/lib/orders";
import { requireUser } from "@/lib/session";
import { EmptyState } from "@/components/ui/EmptyState";

export const metadata: Metadata = { title: "Mis pedidos", robots: { index: false, follow: false } };

export default async function OrdersPage() {
  await requireUser("/cuenta/pedidos");
  const orders = await getMyOrders();

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <nav aria-label="Ruta de navegación" className="text-sm text-ink-soft">
        <Link href="/cuenta" className="hover:underline">
          Mi cuenta
        </Link>{" "}
        › <span className="font-semibold">Mis pedidos</span>
      </nav>
      <h1 className="text-4xl font-bold text-ink-muted">Mis pedidos</h1>

      {orders.length === 0 ? (
        <EmptyState icon={PackageOpen} title="Todavía no tienes pedidos" description="Cuando compres, aquí verás el estado de cada pedido.">
          <ButtonLink href="/buscar">Ver el catálogo</ButtonLink>
        </EmptyState>
      ) : (
        <ul className="flex flex-col gap-3">
          {orders.map((order) => (
            <li key={order.id}>
              <Link
                href={`/cuenta/pedidos/${order.id}`}
                className="flex items-center justify-between gap-4 rounded-2xl bg-card p-5 shadow-card transition duration-200 hover:-translate-y-0.5 hover:shadow-card-hover"
              >
                <span className="flex min-w-0 flex-col gap-1">
                  <span className="flex flex-wrap items-center gap-2">
                    <span className="font-display text-xl font-bold">{order.number}</span>
                    <OrderStatusBadge status={order.status} />
                  </span>
                  <span className="text-sm text-ink-soft">{formatDateTime(order.created_at)}</span>
                  <span className="truncate text-sm text-ink-soft">
                    {order.items.reduce((sum, i) => sum + i.quantity, 0)} artículos · {order.items[0]?.title}
                    {order.items.length > 1 && ` y ${order.items.length - 1} más`}
                  </span>
                </span>
                <span className="flex shrink-0 items-center gap-2">
                  <span className="font-bold text-action">{formatCOP(order.total_cop)}</span>
                  <ChevronRight className="size-5 text-ink-muted" aria-hidden />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
