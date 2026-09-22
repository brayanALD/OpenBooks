"use client";

import { useEffect, useState } from "react";
import { validateCart } from "@/lib/cart-api";
import { useCartStore } from "@/store/cart.store";
import { toast } from "@/store/ui.store";
import type { CartValidation } from "@/types/cart";

/** Alinea el carrito guardado con lo que dice el servidor: quita lo que ya no existe y ajusta por stock. */
function reconcile(data: CartValidation) {
  const { removeMany, setQuantity } = useCartStore.getState();

  if (data.unavailable_ids.length > 0) {
    removeMany(data.unavailable_ids);
    toast.info("Quitamos del carrito un libro que ya no está disponible.");
  }
  for (const line of data.lines) {
    // Los agotados (quantity 0) se quedan a la vista con su aviso; solo se recortan los que tienen algo de stock.
    if (line.quantity > 0 && line.quantity < line.requested_quantity) {
      setQuantity(line.book.id, line.quantity);
      toast.info(`Ajustamos «${line.book.title}» a ${line.quantity} por disponibilidad.`);
    }
  }
}

type Result = { key: string; data: CartValidation | null; failed: boolean };

/**
 * Datos frescos del carrito (precios, stock, totales) desde el servidor.
 * Se recalcula al cambiar los artículos, con una pequeña espera para no lanzar una petición por cada clic.
 */
export function useCartDetails(enabled: boolean) {
  const items = useCartStore((state) => state.items);
  const key = JSON.stringify(items);
  const [result, setResult] = useState<Result | null>(null);
  const [attempt, setAttempt] = useState(0);
  const empty = items.length === 0;

  useEffect(() => {
    if (!enabled || empty) return;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const data = await validateCart(items, controller.signal);
        reconcile(data); // si cambia el carrito, este efecto vuelve a ejecutarse con la versión corregida
        setResult({ key, data, failed: false });
      } catch {
        if (controller.signal.aborted) return;
        setResult((previous) => ({ key, data: previous?.data ?? null, failed: true }));
      }
    }, 150);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [enabled, empty, items, key, attempt]);

  const current = result?.key === key ? result : null;
  return {
    items,
    empty,
    // Mientras llega la respuesta nueva se conservan los datos anteriores, para que la interfaz no parpadee.
    data: empty ? null : (current?.data ?? result?.data ?? null),
    loading: enabled && !empty && current === null,
    failed: current?.failed ?? false,
    retry: () => setAttempt((n) => n + 1),
  };
}
