import clsx, { type ClassValue } from "clsx";

/** Une clases condicionales. Los componentes evitan conflictos de utilidades por diseño. */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}
