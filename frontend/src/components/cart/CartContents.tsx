"use client";

import { useRouter } from "next/navigation";
import { CircleAlert, ShoppingBag } from "lucide-react";
import { useSession } from "@/components/auth/SessionProvider";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { useCartDetails } from "@/lib/use-cart-details";
import { useHydrated } from "@/lib/use-hydrated";
import { useCartStore } from "@/store/cart.store";
import { toast } from "@/store/ui.store";
import { CartItemRow } from "./CartItemRow";
import { OrderSummary } from "./OrderSummary";

type CartContentsProps = {
  /** drawer: panel lateral con pie fijo · page: dos columnas en /carrito */
  layout: "drawer" | "page";
  /** Para cerrar el panel cuando el usuario navega desde él. */
  onNavigate?: () => void;
};

function CartSkeleton() {
  return (
    <div className="flex flex-col gap-4 py-4" role="status" aria-label="Cargando el carrito">
      {[0, 1].map((i) => (
        <div key={i} className="flex gap-4">
          <Skeleton className="h-24 w-16 shrink-0" />
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-9 w-32" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function CartContents({ layout, onNavigate }: CartContentsProps) {
  const router = useRouter();
  const user = useSession();
  const hydrated = useHydrated();
  const { items, empty, data, loading, failed, retry } = useCartDetails(hydrated);
  const setQuantity = useCartStore((state) => state.setQuantity);
  const remove = useCartStore((state) => state.remove);
  const clear = useCartStore((state) => state.clear);

  if (!hydrated) return <CartSkeleton />;

  if (empty) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 px-6 py-16 text-center">
        <ShoppingBag className="size-12 text-brand-400" aria-hidden />
        <p className="font-display text-2xl font-bold">Tu carrito está vacío</p>
        <p className="text-brand-800">Explora el catálogo y añade los libros que quieras leer.</p>
        <ButtonLink href="/buscar" onClick={onNavigate}>
          Ver el catálogo
        </ButtonLink>
      </div>
    );
  }

  if (!data) {
    return failed ? (
      <div className="flex flex-col items-center gap-4 px-6 py-12 text-center">
        <CircleAlert className="size-10 text-accent" aria-hidden />
        <p className="text-brand-800">No pudimos cargar tu carrito. Comprueba tu conexión e inténtalo de nuevo.</p>
        <Button variant="outline" size="sm" onClick={retry}>
          Reintentar
        </Button>
      </div>
    ) : (
      <CartSkeleton />
    );
  }

  const quantityOf = (bookId: string) => items.find((i) => i.bookId === bookId)?.quantity ?? 0;
  // Se oculta al instante lo que el usuario acaba de quitar, sin esperar a la respuesta del servidor.
  const lines = data.lines.filter((line) => quantityOf(line.book.id) > 0);
  const canCheckout = data.item_count > 0;

  const list = (
    <ul className="divide-y divide-brand-200">
      {lines.map((line) => (
        <CartItemRow
          key={line.book.id}
          line={line}
          quantity={quantityOf(line.book.id)}
          onQuantityChange={(quantity) => setQuantity(line.book.id, quantity)}
          onRemove={() => remove(line.book.id)}
          onNavigate={onNavigate}
        />
      ))}
    </ul>
  );

  const finalize = () => {
    onNavigate?.();
    // Para pagar hay que tener cuenta: el carrito se conserva y se continúa en /checkout tras iniciar sesión.
    router.push(user ? "/checkout" : "/login?next=/checkout&reason=checkout");
  };

  const checkout = (
    <Button size="lg" className="w-full" disabled={!canCheckout} onClick={finalize}>
      Finalizar compra
    </Button>
  );

  if (layout === "drawer") {
    return (
      <div className="flex min-h-0 flex-1 flex-col">
        <div className="flex-1 overflow-y-auto px-5">{list}</div>
        <div className="flex flex-col gap-4 border-t border-brand-200 bg-card p-5">
          <OrderSummary cart={data} stale={loading} />
          {checkout}
          <ButtonLink href="/carrito" variant="outline" size="md" className="w-full" onClick={onNavigate}>
            Ver carrito completo
          </ButtonLink>
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_22rem] lg:items-start">
      <section aria-label="Artículos del carrito" className="rounded-2xl bg-card px-5 shadow-card sm:px-6">
        {list}
      </section>
      <aside className="flex flex-col gap-4 rounded-2xl bg-card p-6 shadow-card lg:sticky lg:top-4">
        <h2 className="text-2xl font-bold">Resumen</h2>
        <OrderSummary cart={data} stale={loading} />
        {checkout}
        <ButtonLink href="/buscar" variant="outline" className="w-full">
          Seguir comprando
        </ButtonLink>
        <button
          type="button"
          onClick={() => {
            clear();
            toast.info("Carrito vaciado.");
          }}
          className="text-sm font-semibold text-brand-600 underline underline-offset-4 hover:text-accent"
        >
          Vaciar carrito
        </button>
      </aside>
    </div>
  );
}
