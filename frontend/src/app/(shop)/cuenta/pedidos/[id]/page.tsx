import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CircleAlert, PartyPopper } from "lucide-react";
import { OrderStatusBadge } from "@/components/checkout/OrderStatusBadge";
import { ButtonLink } from "@/components/ui/Button";
import { formatCOP, formatDateTime } from "@/lib/format";
import { getMyOrder } from "@/lib/orders";
import { requireUser } from "@/lib/session";

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
      <nav aria-label="Ruta de navegación" className="text-sm text-brand-800">
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
        <div role="status" className="flex items-start gap-3 rounded-2xl bg-emerald-100 p-5 text-emerald-900">
          <PartyPopper className="mt-0.5 size-6 shrink-0" aria-hidden />
          <div>
            <p className="font-display text-2xl font-bold">¡Gracias por tu compra!</p>
            <p>Recibimos tu pago y estamos preparando tu pedido.</p>
          </div>
        </div>
      )}

      {order.status === "failed" && (
        <div role="alert" className="flex flex-col items-start gap-3 rounded-2xl bg-accent p-5 text-white">
          <p className="flex items-start gap-2 font-semibold">
            <CircleAlert className="mt-0.5 size-5 shrink-0" aria-hidden />
            El pago no se completó: {payment.failure_reason ?? "no se pudo procesar."} No se te cobró nada.
          </p>
          <ButtonLink href="/checkout" variant="light" size="sm">
            Volver a intentarlo
          </ButtonLink>
        </div>
      )}

      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-4xl font-bold text-brand-600">Pedido {order.number}</h1>
          <p className="text-brand-800">{formatDateTime(order.created_at)}</p>
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
                <span className="text-sm text-brand-800">{item.author_name}</span>
                <span className="text-sm text-brand-800">
                  {item.quantity} × {formatCOP(item.unit_price_cop)}
                </span>
              </span>
              <span className="font-bold text-accent">{formatCOP(item.line_total_cop)}</span>
            </li>
          ))}
        </ul>
        <dl className="flex flex-col gap-2 border-t border-brand-200 py-4">
          <div className="flex justify-between text-brand-800">
            <dt>Subtotal</dt>
            <dd>{formatCOP(order.subtotal_cop)}</dd>
          </div>
          <div className="flex justify-between text-brand-800">
            <dt>Envío</dt>
            <dd>{order.shipping_cop === 0 ? "Gratis" : formatCOP(order.shipping_cop)}</dd>
          </div>
          <div className="flex justify-between text-xl font-bold">
            <dt>Total</dt>
            <dd className="text-accent">{formatCOP(order.total_cop)}</dd>
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
          {shipping.notes && <p className="text-brand-800">{shipping.notes}</p>}
          {shipping.phone && <p className="text-brand-800">Cel. {shipping.phone}</p>}
        </section>

        <section aria-labelledby="pago" className="rounded-2xl bg-card p-5 shadow-card">
          <h2 id="pago" className="mb-2 font-display text-xl font-bold">
            Pago
          </h2>
          <p>{payment.method ?? "—"}</p>
          <p className="text-brand-800">
            {payment.status === "approved" ? "Aprobado" : payment.status === "declined" ? "Rechazado" : "En proceso"}
          </p>
          {payment.reference && <p className="break-all text-xs text-brand-600">Ref. {payment.reference}</p>}
        </section>
      </div>
    </div>
  );
}
