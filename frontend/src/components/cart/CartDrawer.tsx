"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { X } from "lucide-react";
import { useUIStore } from "@/store/ui.store";
import { CartContents } from "./CartContents";

/** Panel lateral sobre <dialog> nativo: foco, Escape y fondo inerte sin librerías. */
export function CartDrawer() {
  const open = useUIStore((state) => state.cartOpen);
  const closeCart = useUIStore((state) => state.closeCart);
  const ref = useRef<HTMLDialogElement>(null);
  const pathname = usePathname();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  // Navegar (p. ej. a la ficha de un libro) cierra el panel.
  useEffect(() => {
    closeCart();
  }, [pathname, closeCart]);

  return (
    <dialog
      ref={ref}
      aria-labelledby="cart-drawer-title"
      onClose={closeCart}
      onClick={(event) => {
        if (event.target === ref.current) closeCart();
      }}
      className="fixed inset-y-0 left-auto right-0 m-0 h-dvh max-h-none w-[min(26rem,100vw)] max-w-none bg-brand-50 p-0 text-brand-900 shadow-card-hover backdrop:bg-brand-900/50 backdrop:backdrop-blur-sm open:animate-drawer-in"
    >
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between border-b border-brand-200 px-5 py-4">
          <h2 id="cart-drawer-title" className="text-2xl font-bold">
            Tu carrito
          </h2>
          <button
            type="button"
            onClick={closeCart}
            aria-label="Cerrar el carrito"
            className="-mr-2 rounded-full p-2 text-brand-600 transition-colors hover:bg-brand-100"
          >
            <X className="size-5" aria-hidden />
          </button>
        </div>
        {/* Solo se monta abierto: así el carrito se pide al servidor al abrirlo, no en cada página. */}
        {open && <CartContents layout="drawer" onNavigate={closeCart} />}
      </div>
    </dialog>
  );
}
