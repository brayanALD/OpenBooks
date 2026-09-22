"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ShoppingCart } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { useHydrated } from "@/lib/use-hydrated";
import { MAX_QUANTITY_PER_BOOK, useCartStore } from "@/store/cart.store";
import { useUIStore } from "@/store/ui.store";

type PurchaseBoxProps = {
  bookId: string;
  stock: number;
  /** Se llama tras añadir o comprar (la vista rápida cierra su modal). */
  onAdded?: () => void;
};

/** Selector de cantidad y botones de compra. Respeta el stock y lo que ya hay en el carrito. */
export function PurchaseBox({ bookId, stock, onAdded }: PurchaseBoxProps) {
  const router = useRouter();
  const hydrated = useHydrated();
  const inCart = useCartStore((state) => state.items.find((i) => i.bookId === bookId)?.quantity ?? 0);
  const add = useCartStore((state) => state.add);
  const openCart = useUIStore((state) => state.openCart);
  const [chosen, setChosen] = useState(1);

  if (stock <= 0) {
    return (
      <div className="rounded-2xl bg-brand-100 p-4 text-brand-800">
        <p className="font-semibold">Agotado por ahora</p>
        <p className="text-sm">Vuelve pronto: este libro no tiene unidades disponibles.</p>
      </div>
    );
  }

  const limit = Math.min(stock, MAX_QUANTITY_PER_BOOK);
  // Hasta hidratar se ignora el carrito: coincide con el HTML del servidor.
  const room = Math.max(0, limit - (hydrated ? inCart : 0));
  const quantity = Math.min(chosen, Math.max(room, 1));

  const addToCart = () => {
    add(bookId, quantity, limit);
    setChosen(1);
  };

  return (
    <div className="flex flex-col gap-4">
      {stock <= 5 && <p className="text-sm font-semibold text-accent">¡Quedan solo {stock} unidades!</p>}

      {room === 0 ? (
        <div className="flex flex-col items-start gap-3 rounded-2xl bg-brand-100 p-4 text-brand-800">
          <p className="text-sm font-semibold">
            Ya tienes en el carrito todas las unidades que puedes pedir ({limit}).
          </p>
          <Button variant="outline" size="sm" onClick={openCart}>
            Ver carrito
          </Button>
        </div>
      ) : (
        <>
          <div className="max-w-40">
            <Select label="Cantidad" value={quantity} onChange={(e) => setChosen(Number(e.target.value))}>
              {Array.from({ length: room }, (_, i) => (
                <option key={i + 1} value={i + 1}>
                  {i + 1}
                </option>
              ))}
            </Select>
          </div>
          {hydrated && inCart > 0 && (
            <p className="text-sm text-brand-800">Ya tienes {inCart} en el carrito.</p>
          )}
          <div className="flex flex-wrap gap-3">
            <Button
              size="lg"
              onClick={() => {
                addToCart();
                onAdded?.();
                openCart();
              }}
            >
              <ShoppingCart className="size-5" aria-hidden />
              Añadir al carrito
            </Button>
            <Button
              size="lg"
              variant="secondary"
              onClick={() => {
                addToCart();
                onAdded?.();
                router.push("/carrito");
              }}
            >
              Comprar ahora
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
