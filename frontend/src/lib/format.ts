/** 306708 -> "$306.708" (como en el sitio original). */
export function formatCOP(amount: number): string {
  return `$${amount.toLocaleString("es-CO")}`;
}

/** 4.5 -> "4,5" */
export function formatRating(rating: number): string {
  return rating.toLocaleString("es-CO", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("es-CO", { dateStyle: "long", timeStyle: "short" });
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-CO", { year: "numeric", month: "long", day: "numeric" });
}
