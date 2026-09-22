import { cn } from "@/lib/cn";
import { formatCOP } from "@/lib/format";
import type { CartValidation } from "@/types/cart";

/** Resumen con los totales que calculó el servidor. `stale` atenúa la cifra mientras se recalcula. */
export function OrderSummary({ cart, stale }: { cart: CartValidation; stale: boolean }) {
  return (
    <dl className={cn("flex flex-col gap-2 transition-opacity", stale && "opacity-50")} aria-busy={stale}>
      <div className="flex justify-between text-brand-800">
        <dt>
          Subtotal ({cart.item_count} {cart.item_count === 1 ? "artículo" : "artículos"})
        </dt>
        <dd>{formatCOP(cart.subtotal_cop)}</dd>
      </div>
      <div className="flex justify-between text-brand-800">
        <dt>Envío</dt>
        <dd className={cart.shipping_cop === 0 ? "font-semibold text-emerald-800" : undefined}>
          {cart.shipping_cop === 0 ? "Gratis" : formatCOP(cart.shipping_cop)}
        </dd>
      </div>
      <div className="mt-1 flex justify-between border-t border-brand-200 pt-3 text-xl font-bold">
        <dt>Total</dt>
        <dd className="text-accent">{formatCOP(cart.total_cop)}</dd>
      </div>
    </dl>
  );
}
