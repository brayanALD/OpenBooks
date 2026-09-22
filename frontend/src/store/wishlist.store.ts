import { create } from "zustand";

type WishlistState = {
  /** Ids de los libros favoritos del usuario con sesión (vacío sin sesión). */
  ids: string[];
  /** false hasta que llega la primera respuesta del servidor. */
  loaded: boolean;
  replace: (ids: string[]) => void;
  clear: () => void;
};

/** Solo vive en memoria: la lista de verdad está en la cuenta (servidor), no en el navegador. */
export const useWishlistStore = create<WishlistState>((set) => ({
  ids: [],
  loaded: false,
  replace: (ids) => set({ ids, loaded: true }),
  clear: () => set({ ids: [], loaded: false }),
}));
