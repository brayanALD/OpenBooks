"use client";

import { useEffect, useRef } from "react";
import { useCartStore, type CartItem } from "@/store/cart.store";
import { toast } from "@/store/ui.store";
import { useSession } from "./SessionProvider";

type ServerCart = { items: { book_id: string; quantity: number }[]; removed?: string[] };

const toItems = (cart: ServerCart): CartItem[] => cart.items.map((i) => ({ bookId: i.book_id, quantity: i.quantity }));
const keyOf = (items: CartItem[]) => JSON.stringify(items);

/**
 * Con sesión iniciada, el carrito vive en la cuenta: se carga al entrar y cada cambio se guarda (con una
 * pequeña espera para no enviar una petición por cada clic). Sin sesión no hace nada: el carrito de invitado
 * es solo del navegador.
 */
export function CartSync() {
  const user = useSession();
  const authenticated = user !== null;
  const items = useCartStore((state) => state.items);
  const ready = useRef(false);
  const lastSynced = useRef<string | null>(null);

  // 1) Al haber sesión: traer el carrito guardado (manda el servidor).
  useEffect(() => {
    if (!authenticated) return;
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch("/api/cart");
        if (!response.ok || cancelled) return;
        const cart = (await response.json()) as ServerCart;
        const stored = toItems(cart);
        if (cancelled) return;
        // El servidor quita de la cuenta los libros ocultos o borrados y avisa UNA vez (guarda la limpieza).
        if (cart.removed && cart.removed.length > 0) {
          toast.info("Quitamos del carrito un libro que ya no está disponible.");
        }
        lastSynced.current = keyOf(stored);
        useCartStore.getState().replace(stored);
        ready.current = true;
      } catch {
        /* sin red: se reintentará en la próxima carga */
      }
    })();
    return () => {
      cancelled = true;
      ready.current = false;
    };
  }, [authenticated]);

  // 3) Al cerrar o recargar la página se envía lo pendiente. Sin esto, un cambio hecho menos de 300 ms antes de
  //    recargar se perdía: al cargar manda el servidor, que todavía tenía el carrito anterior.
  //    `keepalive` hace que el navegador complete la petición aunque la página ya se esté descargando.
  const latest = useRef(items);
  useEffect(() => {
    latest.current = items;
  }, [items]);

  useEffect(() => {
    if (!authenticated) return;
    const flush = () => {
      const pending = latest.current;
      if (!ready.current || keyOf(pending) === lastSynced.current) return;
      lastSynced.current = keyOf(pending);
      void fetch("/api/cart", {
        method: "PUT",
        keepalive: true,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ items: pending.map((i) => ({ book_id: i.bookId, quantity: i.quantity })) }),
      }).catch(() => {});
    };
    const onVisibility = () => document.visibilityState === "hidden" && flush();
    window.addEventListener("pagehide", flush);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.removeEventListener("pagehide", flush);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [authenticated]);

  // 2) Cada cambio local se guarda en la cuenta.
  useEffect(() => {
    const key = keyOf(items);
    if (!authenticated || !ready.current || key === lastSynced.current) return;

    const timer = setTimeout(async () => {
      try {
        const response = await fetch("/api/cart", {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ items: items.map((i) => ({ book_id: i.bookId, quantity: i.quantity })) }),
        });
        if (!response.ok) return;
        const saved = toItems((await response.json()) as ServerCart);
        lastSynced.current = keyOf(saved);
        // El servidor puede haber descartado libros que ya no existen: se refleja aquí.
        if (keyOf(saved) !== key) useCartStore.getState().replace(saved);
      } catch {
        /* se reintentará con el próximo cambio */
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [authenticated, items]);

  return null;
}
