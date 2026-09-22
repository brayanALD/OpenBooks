import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { OrderStatusActions } from "@/components/admin/OrderStatusActions";
import { OrderStatusBadge } from "@/components/checkout/OrderStatusBadge";
import { getAdminOrder, requireAdmin } from "@/lib/admin";
import { formatCOP, formatDateTime } from "@/lib/format";

export const metadata: Metadata = { title: "Detalle del pedido" };

export default async function AdminOrderPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await requireAdmin(`/admin/pedidos/${id}`);
  const order = await getAdminOrder(id);
  if (!order) notFound();

  const units = order.items.reduce((sum, item) => sum + item.quantity, 0);
  const { shipping, payment, customer } = order;

  return (
    <div className="flex max-w-4xl flex-col gap-6">
      <nav aria-label="Ruta de navegación" className="text-sm text-brand-800">
        <Link href="/admin/pedidos" className="hover:underline">
          Pedidos
        </Link>{" "}
        › <span className="font-semibold">{order.number}</span>
      </nav>

      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-4xl font-bold text-brand-600">Pedido {order.number}</h1>
          <p className="text-brand-800">{formatDateTime(order.created_at)}</p>
        </div>
        <OrderStatusBadge status={order.status} />
      </header>

      <section aria-labelledby="acciones" className="rounded-2xl bg-card p-5 shadow-card">
        <h2 id="acciones" className="mb-3 text-xl font-bold">
          Estado del pedido
        </h2>
        <OrderStatusActions orderId={order.id} number={order.number} status={order.status} units={units} />
      </section>

      <section aria-labelledby="articulos" className="rounded-2xl bg-card px-5 shadow-card">
        <h2 id="articulos" className="sr-only">
          Artículos
        </h2>
        <ul className="divide-y divide-brand-200">
          {order.items.map((item) => (
            <li key={item.book_id} className="flex gap-4 py-4">
              <span className="relative block h-16 w-11 shrink-0 overflow-hidden rounded bg-brand-100">
                <Image src={item.cover} alt="" fill sizes="44px" className="object-contain" />
              </span>
              <span className="min-w-0 flex-1">
                <Link href={`/admin/libros/${item.book_id}`} className="font-display font-bold hover:underline">
                  {item.title}
                </Link>
                <span className="block text-sm text-brand-800">
                  {item.author_name} · {item.quantity} × {formatCOP(item.unit_price_cop)}
                </span>
              </span>
              <span className="font-bold tabular-nums text-accent">{formatCOP(item.line_total_cop)}</span>
            </li>
          ))}
        </ul>
        <dl className="flex flex-col gap-1.5 border-t border-brand-200 py-4">
          <div className="flex justify-between text-brand-800">
            <dt>Subtotal</dt>
            <dd className="tabular-nums">{formatCOP(order.subtotal_cop)}</dd>
          </div>
          <div className="flex justify-between text-brand-800">
            <dt>Envío</dt>
            <dd className="tabular-nums">{order.shipping_cop === 0 ? "Gratis" : formatCOP(order.shipping_cop)}</dd>
          </div>
          <div className="flex justify-between text-xl font-bold">
            <dt>Total</dt>
            <dd className="tabular-nums text-accent">{formatCOP(order.total_cop)}</dd>
          </div>
        </dl>
      </section>

      <div className="grid gap-4 sm:grid-cols-3">
        <section aria-labelledby="cliente" className="rounded-2xl bg-card p-5 shadow-card">
          <h2 id="cliente" className="mb-2 font-display text-xl font-bold">
            Cliente
          </h2>
          {customer ? (
            <>
              <p className="font-semibold">{customer.name}</p>
              <p className="break-all text-brand-800">{customer.email}</p>
            </>
          ) : (
            <p className="text-brand-800">Cuenta eliminada</p>
          )}
        </section>
        <section aria-labelledby="envio" className="rounded-2xl bg-card p-5 shadow-card">
          <h2 id="envio" className="mb-2 font-display text-xl font-bold">
            Enviar a
          </h2>
          <p className="font-semibold">{shipping.recipient_name}</p>
          <p>{shipping.line}</p>
          <p>{shipping.city}</p>
          {shipping.notes && <p className="text-brand-800">{shipping.notes}</p>}
          {shipping.phone && <p className="text-brand-800">Cel. {shipping.phone}</p>}
        </section>
        <section aria-labelledby="pago" className="rounded-2xl bg-card p-5 shadow-card">
          <h2 id="pago" className="mb-2 font-display text-xl font-bold">
            Pago
          </h2>
          <p>{payment.method ?? "—"}</p>
          <p className="text-brand-800">{payment.status === "approved" ? "Aprobado" : payment.status === "declined" ? "Rechazado" : "En proceso"}</p>
          {payment.failure_reason && <p className="text-sm text-accent">{payment.failure_reason}</p>}
          {payment.reference && <p className="break-all text-xs text-brand-600">Ref. {payment.reference}</p>}
        </section>
      </div>
    </div>
  );
}
