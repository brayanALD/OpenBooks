"use client";

import { useEffect } from "react";
import { useWishlistStore } from "@/store/wishlist.store";
import { useSession } from "./SessionProvider";

/** Con sesión iniciada, trae los ids de favoritos para pintar los corazones; al cerrar sesión los olvida. */
export function WishlistSync() {
  const user = useSession();
  const userId = user?.id ?? null;

  useEffect(() => {
    if (!userId) {
      useWishlistStore.getState().clear();
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch("/api/wishlist/ids");
        if (!response.ok || cancelled) return;
        const data = (await response.json()) as { book_ids: string[] };
        if (!cancelled) useWishlistStore.getState().replace(data.book_ids);
      } catch {
        /* sin red: los corazones se quedan vacíos hasta la próxima carga */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  return null;
}
