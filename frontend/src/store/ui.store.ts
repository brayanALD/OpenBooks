import { create } from "zustand";

export type ToastTone = "success" | "error" | "info";

export type ToastItem = {
  id: number;
  message: string;
  tone: ToastTone;
};

type UIState = {
  toasts: ToastItem[];
  push: (message: string, tone?: ToastTone) => void;
  dismiss: (id: number) => void;
  cartOpen: boolean;
  openCart: () => void;
  closeCart: () => void;
};

let nextId = 1;

export const useUIStore = create<UIState>((set) => ({
  toasts: [],
  push: (message, tone = "info") =>
    set((state) => ({ toasts: [...state.toasts, { id: nextId++, message, tone }] })),
  dismiss: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
  cartOpen: false,
  openCart: () => set({ cartOpen: true }),
  closeCart: () => set({ cartOpen: false }),
}));

/** Atajo para lanzar avisos desde cualquier sitio (también fuera de componentes). */
export const toast = {
  success: (message: string) => useUIStore.getState().push(message, "success"),
  error: (message: string) => useUIStore.getState().push(message, "error"),
  info: (message: string) => useUIStore.getState().push(message, "info"),
};
