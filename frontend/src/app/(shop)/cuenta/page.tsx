import type { Metadata } from "next";
import Link from "next/link";
import { ChevronDown, Heart, Library } from "lucide-react";
import { LogoutButton } from "@/components/auth/LogoutButton";
import { ButtonLink } from "@/components/ui/Button";
import { OrderStatusBadge } from "@/components/checkout/OrderStatusBadge";
import { formatCOP, formatDateTime } from "@/lib/format";
import { getMyOrders } from "@/lib/orders";
import { requireUser } from "@/lib/session";

export const metadata: Metadata = { title: "Mi cuenta", robots: { index: false, follow: false } };

export default async function AccountPage() {
  // El proxy solo comprobó que hay cookie; aquí se valida de verdad la sesión con el backend.
  const user = await requireUser("/cuenta");
  const orders = await getMyOrders();
  const recent = orders.slice(0, 3);

  const rows: [string, string | null][] = [
    ["Nombre", `${user.first_name} ${user.last_name}`],
    ["Correo", user.email],
    ["Celular", user.phone],
    ["Dirección", user.address.line],
    ["Ciudad", user.address.city],
    ["Indicaciones", user.address.notes],
  ];

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold text-ink-muted">Hola, {user.first_name}</h1>
          <p className="mt-1 text-ink-soft">Esta es tu cuenta de Open Books.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          {user.role === "admin" && (
            <ButtonLink href="/admin" variant="secondary">
              Panel de administración
            </ButtonLink>
          )}
          <LogoutButton />
        </div>
      </header>

      <section aria-labelledby="pedidos" className="rounded-2xl bg-card p-6 shadow-card">
        <div className="mb-4 flex items-baseline justify-between gap-4">
          <h2 id="pedidos" className="text-2xl font-bold">
            Mis pedidos
          </h2>
          {orders.length > 0 && (
            <Link href="/cuenta/pedidos" className="text-sm font-semibold text-action underline underline-offset-4">
              Ver todos ({orders.length})
            </Link>
          )}
        </div>
        {recent.length === 0 ? (
          <p className="text-ink-soft">Aquí aparecerá el historial de tus compras.</p>
        ) : (
          <ul className="divide-y divide-brand-200">
            {recent.map((order) => (
              <li key={order.id}>
                <Link href={`/cuenta/pedidos/${order.id}`} className="flex items-center justify-between gap-3 py-3 hover:opacity-80">
                  <span className="flex flex-col gap-0.5">
                    <span className="flex items-center gap-2 font-semibold">
                      {order.number} <OrderStatusBadge status={order.status} />
                    </span>
                    <span className="text-sm text-ink-soft">{formatDateTime(order.created_at)}</span>
                  </span>
                  <span className="font-bold text-action">{formatCOP(order.total_cop)}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <nav aria-label="Accesos de la cuenta" className="grid gap-4 sm:grid-cols-2">
        <Link
          href="/cuenta/favoritos"
          className="flex items-center gap-3 rounded-2xl bg-card p-5 font-display text-xl font-bold shadow-card transition duration-200 hover:-translate-y-0.5 hover:shadow-card-hover"
        >
          <Heart className="size-6 text-action" aria-hidden />
          Mis favoritos
        </Link>
        <Link
          href="/cuenta/librero"
          className="flex items-center gap-3 rounded-2xl bg-card p-5 font-display text-xl font-bold shadow-card transition duration-200 hover:-translate-y-0.5 hover:shadow-card-hover"
        >
          <Library className="size-6 text-action" aria-hidden />
          Mi librero
        </Link>
      </nav>

      <section aria-labelledby="datos" className="rounded-2xl bg-card p-6 shadow-card">
        <details className="group">
          <summary className="flex cursor-pointer select-none items-center justify-between gap-3">
            <h2 id="datos" className="text-2xl font-bold">
              Tus datos
            </h2>
            <span className="flex items-center gap-1 text-sm font-semibold text-ink-muted">
              <span className="group-open:hidden">Ver</span>
              <span className="hidden group-open:inline">Ocultar</span>
              <ChevronDown className="size-4 transition-transform group-open:rotate-180" aria-hidden />
            </span>
          </summary>
          <div className="mt-4">
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2">
            {rows
              .filter(([, value]) => value)
              .map(([label, value]) => (
                <div key={label} className="contents">
                  <dt className="font-semibold text-ink-soft">{label}</dt>
                  <dd className="break-words">{value}</dd>
                </div>
              ))}
          </dl>
          </div>
        </details>
      </section>
    </div>
  );
}
