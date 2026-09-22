"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShoppingCart } from "lucide-react";
import { headerActionStyles } from "@/components/layout/styles";
import { useHydrated } from "@/lib/use-hydrated";
import { cartCount, useCartStore } from "@/store/cart.store";
import { useUIStore } from "@/store/ui.store";

/** Botón del header: abre el panel del carrito (en /carrito enlaza a la propia página). */
export function CartButton() {
  const hydrated = useHydrated();
  const count = useCartStore((state) => cartCount(state.items));
  const openCart = useUIStore((state) => state.openCart);
  const onCartPage = usePathname() === "/carrito";

  // El contador vive en localStorage: hasta hidratar se muestra 0 para coincidir con el HTML del servidor.
  const shown = hydrated ? count : 0;
  const label = shown > 0 ? `Carrito, ${shown} ${shown === 1 ? "artículo" : "artículos"}` : "Carrito";

  const content = (
    <>
      <ShoppingCart className="size-6" aria-hidden />
      <span className="hidden sm:inline" aria-hidden>
        Carrito
      </span>
      {shown > 0 && (
        <span
          aria-hidden
          className="absolute -right-0.5 -top-0.5 grid min-w-5 place-items-center rounded-full bg-accent px-1 text-xs font-bold leading-5 text-white"
        >
          {shown}
        </span>
      )}
    </>
  );

  return onCartPage ? (
    <Link href="/carrito" aria-label={label} aria-current="page" className={headerActionStyles}>
      {content}
    </Link>
  ) : (
    <button type="button" onClick={openCart} aria-label={label} aria-haspopup="dialog" className={headerActionStyles}>
      {content}
    </button>
  );
}
