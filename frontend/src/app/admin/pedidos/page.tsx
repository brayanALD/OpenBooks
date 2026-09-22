import type { Metadata } from "next";
import Link from "next/link";
import { OrderStatusBadge } from "@/components/checkout/OrderStatusBadge";
import { Pagination } from "@/components/catalog/Pagination";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { getAdminOrders, requireAdmin } from "@/lib/admin";
import { formatCOP, formatDateTime } from "@/lib/format";
import { flattenParams, type RawSearchParams } from "@/lib/listing";
import { ORDER_STATUS_LABEL } from "@/types/order";

export const metadata: Metadata = { title: "Pedidos" };

const first = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v);
const STATUSES = Object.keys(ORDER_STATUS_LABEL);

export default async function AdminOrdersPage({ searchParams }: { searchParams: Promise<RawSearchParams> }) {
  await requireAdmin("/admin/pedidos");
  const sp = await searchParams;
  const q = first(sp.q)?.trim().slice(0, 100) || undefined;
  const requested = first(sp.estado);
  const status = requested && STATUSES.includes(requested) ? requested : undefined; // una URL inventada se ignora
  const page = Math.max(1, Number.parseInt(first(sp.page) ?? "1", 10) || 1);

  const data = await getAdminOrders({ q, status, page });

  // El contenedor de la tabla lleva `relative`: los textos `sr-only` son position:absolute y, sin un ancestro posicionado,
  // escapan del recorte del scroll horizontal y ensanchan toda la página en móvil.
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-4xl font-bold text-brand-600">Pedidos</h1>

      <form method="get" className="flex flex-wrap items-end gap-3 rounded-2xl bg-card p-4 shadow-card" role="search" aria-label="Buscar pedidos">
        <div className="min-w-56 flex-1">
          <Input label="Buscar" name="q" defaultValue={q} placeholder="Número, cliente o correo" />
        </div>
        <div className="w-48">
          <Select label="Estado" name="estado" defaultValue={status ?? ""}>
            <option value="">Todos</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {ORDER_STATUS_LABEL[s as keyof typeof ORDER_STATUS_LABEL]}
              </option>
            ))}
          </Select>
        </div>
        <Button type="submit">Filtrar</Button>
      </form>

      <p className="text-brand-800" aria-live="polite">
        {data.total} {data.total === 1 ? "pedido" : "pedidos"}
      </p>

      {data.items.length === 0 ? (
        <p className="rounded-2xl bg-card p-8 text-center text-brand-800 shadow-card">No hay pedidos con esos criterios.</p>
      ) : (
        <div className="relative overflow-x-auto rounded-2xl bg-card shadow-card">
          <table className="w-full min-w-[40rem] text-left">
            <caption className="sr-only">Pedidos</caption>
            <thead className="border-b border-brand-200 text-sm text-brand-800">
              <tr>
                <th scope="col" className="p-3 font-semibold">Pedido</th>
                <th scope="col" className="p-3 font-semibold">Cliente</th>
                <th scope="col" className="p-3 font-semibold">Estado</th>
                <th scope="col" className="p-3 text-right font-semibold">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-100">
              {data.items.map((order) => (
                <tr key={order.id}>
                  <td className="p-3">
                    <Link href={`/admin/pedidos/${order.id}`} className="font-display text-lg font-bold hover:underline">
                      {order.number}
                    </Link>
                    <span className="block text-sm text-brand-800">{formatDateTime(order.created_at)}</span>
                  </td>
                  <td className="p-3">
                    {order.customer ? (
                      <>
                        {order.customer.name}
                        <span className="block text-sm text-brand-800">{order.customer.email}</span>
                      </>
                    ) : (
                      <span className="text-brand-800">Cuenta eliminada</span>
                    )}
                  </td>
                  <td className="p-3">
                    <OrderStatusBadge status={order.status} />
                  </td>
                  <td className="p-3 text-right font-bold tabular-nums text-accent">{formatCOP(order.total_cop)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Pagination page={data.page} pages={data.pages} basePath="/admin/pedidos" query={flattenParams(sp)} />
    </div>
  );
}
