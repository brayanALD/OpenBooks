import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { OrderStatusBadge } from "@/components/checkout/OrderStatusBadge";
import { ButtonLink } from "@/components/ui/Button";
import { formatCOP, formatDateTime } from "@/lib/format";
import { getMyOrder } from "@/lib/orders";
import { requireUser } from "@/lib/session";
import { Alert } from "@/components/ui/Alert";

type Props = {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ nuevo?: string }>;
};

export const metadata: Metadata = { title: "Detalle del pedido", robots: { index: false, follow: false } };

export default async function OrderDetailPage({ params, searchParams }: Props) {
  const { id } = await params;
  await requireUser(`/cuenta/pedidos/${id}`);
  const order = await getMyOrder(id);
  if (!order) notFound(); // también cuando el pedido existe pero es de otra persona

  const justPlaced = (await searchParams).nuevo === "1";
  const { shipping, payment } = order;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <nav aria-label="Ruta de navegación" className="text-sm text-ink-soft">
        <Link href="/cuenta" className="hover:underline">
          Mi cuenta
        </Link>{" "}
        ›{" "}
        <Link href="/cuenta/pedidos" className="hover:underline">
          Mis pedidos
        </Link>{" "}
        › <span className="font-semibold">{order.number}</span>
      </nav>

      {justPlaced && order.status === "paid" && (
        <Alert tone="success" live title="¡Gracias por tu compra!" className="text-base">
          Recibimos tu pago y estamos preparando tu pedido.
        </Alert>
      )}

      {order.status === "failed" && (
        <Alert tone="danger" live title="El pago no se completó">
          <p>{payment.failure_reason ?? "No se pudo procesar."} No se te cobró nada.</p>
          <ButtonLink href="/checkout" size="sm" className="mt-3">
            Volver a intentarlo
          </ButtonLink>
        </Alert>
      )}

      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-4xl font-bold text-ink-muted">Pedido {order.number}</h1>
          <p className="text-ink-soft">{formatDateTime(order.created_at)}</p>
        </div>
        <OrderStatusBadge status={order.status} />
      </header>

      <section aria-labelledby="articulos" className="rounded-2xl bg-card px-5 shadow-card sm:px-6">
        <h2 id="articulos" className="sr-only">
          Artículos
        </h2>
        <ul className="divide-y divide-brand-200">
          {order.items.map((item) => (
            <li key={item.book_id} className="flex gap-4 py-4">
              <span className="relative block h-20 w-14 shrink-0 overflow-hidden rounded-lg bg-brand-100">
                <Image src={item.cover} alt="" fill sizes="56px" className="object-contain p-1" />
              </span>
              <span className="flex min-w-0 flex-1 flex-col">
                <span className="font-display font-bold leading-snug">{item.title}</span>
                <span className="text-sm text-ink-soft">{item.author_name}</span>
                <span className="text-sm text-ink-soft">
                  {item.quantity} × {formatCOP(item.unit_price_cop)}
                </span>
              </span>
              <span className="font-bold text-action">{formatCOP(item.line_total_cop)}</span>
            </li>
          ))}
        </ul>
        <dl className="flex flex-col gap-2 border-t border-brand-200 py-4">
          <div className="flex justify-between text-ink-soft">
            <dt>Subtotal</dt>
            <dd>{formatCOP(order.subtotal_cop)}</dd>
          </div>
          <div className="flex justify-between text-ink-soft">
            <dt>Envío</dt>
            <dd>{order.shipping_cop === 0 ? "Gratis" : formatCOP(order.shipping_cop)}</dd>
          </div>
          <div className="flex justify-between text-xl font-bold">
            <dt>Total</dt>
            <dd className="text-action">{formatCOP(order.total_cop)}</dd>
          </div>
        </dl>
      </section>

      <div className="grid gap-4 sm:grid-cols-2">
        <section aria-labelledby="envio" className="rounded-2xl bg-card p-5 shadow-card">
          <h2 id="envio" className="mb-2 font-display text-xl font-bold">
            Envío a
          </h2>
          <p className="font-semibold">{shipping.recipient_name}</p>
          <p>{shipping.line}</p>
          <p>{shipping.city}</p>
          {shipping.notes && <p className="text-ink-soft">{shipping.notes}</p>}
          {shipping.phone && <p className="text-ink-soft">Cel. {shipping.phone}</p>}
        </section>

        <section aria-labelledby="pago" className="rounded-2xl bg-card p-5 shadow-card">
          <h2 id="pago" className="mb-2 font-display text-xl font-bold">
            Pago
          </h2>
          <p>{payment.method ?? "—"}</p>
          <p className="text-ink-soft">
            {payment.status === "approved" ? "Aprobado" : payment.status === "declined" ? "Rechazado" : "En proceso"}
          </p>
          {payment.reference && <p className="break-all text-xs text-ink-muted">Ref. {payment.reference}</p>}
        </section>
      </div>
    </div>
  );
}
