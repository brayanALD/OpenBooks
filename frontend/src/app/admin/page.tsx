import type { Metadata } from "next";
import Link from "next/link";
import { AlertTriangle, BookX, Coins, EyeOff, Library, Package } from "lucide-react";
import { getAdminSummary, requireAdmin } from "@/lib/admin";
import { formatCOP } from "@/lib/format";
import { ORDER_STATUS_LABEL, type OrderStatus } from "@/types/order";

export const metadata: Metadata = { title: "Resumen" };

function Stat({ label, value, href, Icon, tone = "normal" }: { label: string; value: string | number; href?: string; Icon: typeof Library; tone?: "normal" | "warn" }) {
  const body = (
    <div className={`flex items-center gap-4 rounded-2xl p-5 shadow-card ${tone === "warn" && Number(value) > 0 ? "bg-accent text-white" : "bg-card"}`}>
      <Icon className="size-8 shrink-0 opacity-80" aria-hidden />
      <div>
        <p className="text-3xl font-bold leading-none">{value}</p>
        <p className="mt-1 text-sm opacity-90">{label}</p>
      </div>
    </div>
  );
  return href ? (
    <Link href={href} className="block transition hover:-translate-y-0.5">
      {body}
    </Link>
  ) : (
    body
  );
}

export default async function AdminDashboard() {
  await requireAdmin("/admin");
  const { books, orders } = await getAdminSummary();

  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-4xl font-bold text-brand-600">Resumen</h1>

      <section aria-labelledby="inventario" className="flex flex-col gap-3">
        <h2 id="inventario" className="text-2xl font-bold">
          Inventario
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Stat label="Libros activos" value={books.active} href="/admin/libros?estado=activos" Icon={Library} />
          <Stat label="Ocultos" value={books.hidden} href="/admin/libros?estado=ocultos" Icon={EyeOff} />
          <Stat label="Agotados" value={books.out_of_stock} href="/admin/libros?estado=poco-stock" Icon={BookX} tone="warn" />
          <Stat label="Con pocas unidades (1–5)" value={books.low_stock} href="/admin/libros?estado=poco-stock" Icon={AlertTriangle} tone="warn" />
        </div>
      </section>

      <section aria-labelledby="ventas" className="flex flex-col gap-3">
        <h2 id="ventas" className="text-2xl font-bold">
          Ventas
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Stat label="Ingresos (pagados, enviados y entregados)" value={formatCOP(orders.revenue_cop)} Icon={Coins} />
          <Stat label="Pedidos pendientes de enviar" value={orders.by_status.paid ?? 0} href="/admin/pedidos?estado=paid" Icon={Package} tone="warn" />
        </div>
        {Object.keys(orders.by_status).length > 0 && (
          <ul className="flex flex-wrap gap-2 text-sm">
            {Object.entries(orders.by_status).map(([status, count]) => (
              <li key={status}>
                <Link href={`/admin/pedidos?estado=${status}`} className="rounded-full bg-card px-3 py-1 font-semibold shadow-card hover:bg-brand-100">
                  {ORDER_STATUS_LABEL[status as OrderStatus] ?? status}: {count}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
