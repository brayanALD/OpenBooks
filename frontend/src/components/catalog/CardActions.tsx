"use client";

import { useRouter } from "next/navigation";
import { Banknote, ShoppingCart } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useHydrated } from "@/lib/use-hydrated";
import { MAX_QUANTITY_PER_BOOK, useCartStore } from "@/store/cart.store";
import { useUIStore } from "@/store/ui.store";

type CardActionsProps = { bookId: string; title: string; stock: number; className?: string };

/** Botones con solo icono (carrito y rayo) de las tarjetas: siempre una unidad, respetando stock y lo que ya hay en el carrito. */
export function CardActions({ bookId, title, stock, className }: CardActionsProps) {
  const router = useRouter();
  const hydrated = useHydrated();
  const inCart = useCartStore((state) => state.items.find((i) => i.bookId === bookId)?.quantity ?? 0);
  const add = useCartStore((state) => state.add);
  const openCart = useUIStore((state) => state.openCart);

  if (stock <= 0) return null;

  const limit = Math.min(stock, MAX_QUANTITY_PER_BOOK);
  const full = hydrated && inCart >= limit;

  const label = full ? "Ya tienes el máximo en el carrito" : `Añadir ${title} al carrito`;

  return (
    // `relative z-10` deja los botones por encima del enlace que cubre toda la tarjeta.
    <div className={`relative z-10 flex gap-2 ${className ?? ""}`}>
      <Button
        size="sm"
        className="size-11 !p-0"
        disabled={full}
        aria-label={label}
        title={full ? "Ya tienes el máximo en el carrito" : "Añadir al carrito"}
        onClick={() => {
          add(bookId, 1, limit);
          openCart();
        }}
      >
        <ShoppingCart className="size-6" aria-hidden />
      </Button>
      <Button
        size="sm"
        variant="secondary"
        className="size-11 !p-0"
        aria-label={`Comprar ahora ${title}`}
        title="Comprar ahora"
        onClick={() => {
          if (!full) add(bookId, 1, limit);
          router.push("/carrito");
        }}
      >
        <Banknote className="size-6" aria-hidden />
      </Button>
    </div>
  );
}
