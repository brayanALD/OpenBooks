import type { Metadata } from "next";
import Link from "next/link";
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
          <h1 className="text-4xl font-bold text-brand-600">Hola, {user.first_name}</h1>
          <p className="mt-1 text-brand-800">Esta es tu cuenta de Open Books.</p>
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

      <section aria-labelledby="datos" className="rounded-2xl bg-card p-6 shadow-card">
        <h2 id="datos" className="mb-4 text-2xl font-bold">
          Tus datos
        </h2>
        <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2">
          {rows
            .filter(([, value]) => value)
            .map(([label, value]) => (
              <div key={label} className="contents">
                <dt className="font-semibold text-brand-800">{label}</dt>
                <dd className="break-words">{value}</dd>
              </div>
            ))}
        </dl>
      </section>

      <section aria-labelledby="pedidos" className="rounded-2xl bg-card p-6 shadow-card">
        <div className="mb-4 flex items-baseline justify-between gap-4">
          <h2 id="pedidos" className="text-2xl font-bold">
            Mis pedidos
          </h2>
          {orders.length > 0 && (
            <Link href="/cuenta/pedidos" className="text-sm font-semibold text-accent underline underline-offset-4">
              Ver todos ({orders.length})
            </Link>
          )}
        </div>
        {recent.length === 0 ? (
          <p className="text-brand-800">Aquí aparecerá el historial de tus compras.</p>
        ) : (
          <ul className="divide-y divide-brand-200">
            {recent.map((order) => (
              <li key={order.id}>
                <Link href={`/cuenta/pedidos/${order.id}`} className="flex items-center justify-between gap-3 py-3 hover:opacity-80">
                  <span className="flex flex-col gap-0.5">
                    <span className="flex items-center gap-2 font-semibold">
                      {order.number} <OrderStatusBadge status={order.status} />
                    </span>
                    <span className="text-sm text-brand-800">{formatDateTime(order.created_at)}</span>
                  </span>
                  <span className="font-bold text-accent">{formatCOP(order.total_cop)}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="favoritos" className="rounded-2xl bg-card p-6 shadow-card">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="favoritos" className="text-2xl font-bold">
            Mis favoritos
          </h2>
          <Link href="/cuenta/favoritos" className="text-sm font-semibold text-accent underline underline-offset-4">
            Ver mi lista
          </Link>
        </div>
        <p className="mt-2 text-brand-800">Los libros que guardaste con el corazón para verlos más tarde.</p>
      </section>

      <section aria-labelledby="librero" className="rounded-2xl bg-card p-6 shadow-card">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="librero" className="text-2xl font-bold">
            Mi librero
          </h2>
          <Link href="/cuenta/librero" className="text-sm font-semibold text-accent underline underline-offset-4">
            Ver mi librero
          </Link>
        </div>
        <p className="mt-2 text-brand-800">Los libros que has comprado, todos en un mismo lugar.</p>
      </section>
    </div>
  );
}
