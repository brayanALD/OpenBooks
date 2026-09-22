"use client";

import { useSyncExternalStore } from "react";

const subscribe = () => () => {};

/**
 * `false` en el servidor y durante la hidratación, `true` después. Sirve para no pintar datos que solo
 * existen en el navegador (el carrito de localStorage) hasta que coincida con el HTML del servidor.
 */
export function useHydrated(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
}
