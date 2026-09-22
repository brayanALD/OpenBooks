import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

/** Igual que `MAX_QUANTITY_PER_BOOK` del backend, que es quien decide de verdad. */
export const MAX_QUANTITY_PER_BOOK = 10;

/**
 * El carrito guarda solo qué libros y cuántos. Precios, stock y totales los calcula siempre el servidor
 * (`POST /cart/validate`): un precio guardado en el navegador podría estar desactualizado o manipulado.
 */
export type CartItem = { bookId: string; quantity: number };

type CartState = {
  items: CartItem[];
  /** Suma `quantity` sin pasar de `limit`. Devuelve la cantidad resultante en el carrito. */
  add: (bookId: string, quantity: number, limit?: number) => number;
  setQuantity: (bookId: string, quantity: number) => void;
  remove: (bookId: string) => void;
  removeMany: (bookIds: string[]) => void;
  clear: () => void;
  /** Sustituye todo el carrito (lo usa la sincronización con la cuenta). Aplica las mismas limpiezas que al cargar. */
  replace: (items: CartItem[]) => void;
};

const clamp = (quantity: number, limit = MAX_QUANTITY_PER_BOOK) =>
  Math.max(0, Math.min(Math.floor(quantity), limit, MAX_QUANTITY_PER_BOOK));

/** Lo guardado en localStorage puede estar corrupto o venir de otra versión: se filtra lo que no sirva. */
function sanitize(raw: unknown): CartItem[] {
  if (!Array.isArray(raw)) return [];
  const seen = new Set<string>();
  const items: CartItem[] = [];
  for (const entry of raw) {
    const bookId = typeof entry?.bookId === "string" ? entry.bookId : "";
    const quantity = Number(entry?.quantity);
    if (!bookId || seen.has(bookId) || !Number.isInteger(quantity) || quantity < 1) continue;
    seen.add(bookId);
    items.push({ bookId, quantity: Math.min(quantity, MAX_QUANTITY_PER_BOOK) });
  }
  return items;
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],

      add: (bookId, quantity, limit = MAX_QUANTITY_PER_BOOK) => {
        const current = get().items.find((i) => i.bookId === bookId)?.quantity ?? 0;
        const next = clamp(current + quantity, limit);
        if (next <= 0) return current;
        set((state) => ({
          items: state.items.some((i) => i.bookId === bookId)
            ? state.items.map((i) => (i.bookId === bookId ? { ...i, quantity: next } : i))
            : [...state.items, { bookId, quantity: next }],
        }));
        return next;
      },

      setQuantity: (bookId, quantity) => {
        const next = clamp(quantity);
        set((state) => ({
          items:
            next === 0
              ? state.items.filter((i) => i.bookId !== bookId)
              : state.items.map((i) => (i.bookId === bookId ? { ...i, quantity: next } : i)),
        }));
      },

      remove: (bookId) => set((state) => ({ items: state.items.filter((i) => i.bookId !== bookId) })),

      removeMany: (bookIds) =>
        set((state) => ({ items: state.items.filter((i) => !bookIds.includes(i.bookId)) })),

      clear: () => set({ items: [] }),

      replace: (items) => set({ items: sanitize(items) }),
    }),
    {
      name: "openbooks-cart-v1",
      version: 1,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ items: state.items }),
      merge: (persisted, current) => ({
        ...current,
        items: sanitize((persisted as { items?: unknown } | undefined)?.items),
      }),
    },
  ),
);

export const cartCount = (items: CartItem[]) => items.reduce((sum, i) => sum + i.quantity, 0);
