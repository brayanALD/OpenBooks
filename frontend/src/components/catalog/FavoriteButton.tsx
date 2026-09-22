"use client";

import { useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Heart } from "lucide-react";
import { useSession } from "@/components/auth/SessionProvider";
import { requestJson } from "@/lib/auth-client";
import { cn } from "@/lib/cn";
import { useHydrated } from "@/lib/use-hydrated";
import { toast } from "@/store/ui.store";
import { useWishlistStore } from "@/store/wishlist.store";

type FavoriteButtonProps = {
  bookId: string;
  title: string;
  /** icon: corazón flotante sobre la portada · text: botón con texto (ficha del libro) */
  variant?: "icon" | "text";
  className?: string;
};

/** Añade o quita un libro de los favoritos. Sin sesión lleva al login y vuelve a esta página. */
export function FavoriteButton({ bookId, title, variant = "icon", className }: FavoriteButtonProps) {
  const router = useRouter();
  const pathname = usePathname();
  const user = useSession();
  const hydrated = useHydrated();
  const active = useWishlistStore((state) => state.ids.includes(bookId));
  const [busy, setBusy] = useState(false);
  const on = hydrated && active;

  async function toggle() {
    if (!user) {
      router.push(`/login?next=${encodeURIComponent(pathname)}&reason=favoritos`);
      return;
    }
    if (busy) return;
    setBusy(true);
    const adding = !on;
    const before = useWishlistStore.getState().ids;
    const without = before.filter((id) => id !== bookId);
    useWishlistStore.getState().replace(adding ? [bookId, ...without] : without); // optimista

    const result = await requestJson<{ book_ids: string[] }>(adding ? "PUT" : "DELETE", `/api/wishlist/${bookId}`);
    setBusy(false);
    if (!result.ok) {
      useWishlistStore.getState().replace(before);
      toast.error(result.message);
      return;
    }
    useWishlistStore.getState().replace(result.data.book_ids);
    toast.success(adding ? "Añadido a tus favoritos." : "Quitado de tus favoritos.");
    // En la lista de favoritos el libro quitado debe desaparecer.
    if (!adding && pathname === "/cuenta/favoritos") router.refresh();
  }

  if (variant === "text") {
    return (
      <button
        type="button"
        onClick={toggle}
        aria-pressed={on}
        disabled={busy}
        className={cn(
          "inline-flex items-center gap-2 rounded-full border-2 border-brand-600 px-5 py-2 text-[13px] font-semibold uppercase tracking-wide text-brand-600 transition hover:bg-brand-600 hover:text-white disabled:opacity-60",
          className,
        )}
      >
        <Heart className={cn("size-5", on && "fill-accent text-accent")} aria-hidden />
        {on ? "En tus favoritos" : "Añadir a favoritos"}
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={on}
      aria-label={on ? `Quitar ${title} de favoritos` : `Añadir ${title} a favoritos`}
      title={on ? "Quitar de favoritos" : "Añadir a favoritos"}
      disabled={busy}
      // `relative z-10` lo deja por encima del enlace que cubre toda la tarjeta.
      className={cn(
        "relative z-10 flex size-10 items-center justify-center rounded-full bg-card/90 text-brand-600 shadow transition hover:scale-110 hover:bg-card disabled:opacity-60",
        className,
      )}
    >
      <Heart className={cn("size-5", on && "fill-accent text-accent")} aria-hidden />
    </button>
  );
}
