import type { BookListParams } from "@/lib/api-client";
import type { BookSort } from "@/types/catalog";

export type RawSearchParams = Record<string, string | string[] | undefined>;

export const SORT_OPTIONS: { value: BookSort; label: string }[] = [
  { value: "relevance", label: "Relevancia" },
  { value: "price_asc", label: "Precio: menor a mayor" },
  { value: "price_desc", label: "Precio: mayor a menor" },
  { value: "rating", label: "Mejor valorados" },
  { value: "title", label: "Título (A–Z)" },
  { value: "newest", label: "Más recientes" },
];

export type ListingValues = {
  sort: BookSort;
  min_price?: number;
  max_price?: number;
  free_shipping: boolean;
  on_sale: boolean;
  in_stock: boolean;
};

const first = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value);

function nonNegativeInt(value: string | undefined): number | undefined {
  if (!value) return undefined;
  const n = Number(value);
  return Number.isInteger(n) && n >= 0 ? n : undefined;
}

/**
 * Traduce la URL a parámetros de la API. Todo valor inválido se ignora en vez de romper la página:
 * la URL la puede escribir cualquiera.
 */
export function parseListing(sp: RawSearchParams): {
  values: ListingValues;
  api: BookListParams;
  page: number;
  activeFilters: number;
} {
  const sortRaw = first(sp.sort);
  const sort = SORT_OPTIONS.some((o) => o.value === sortRaw) ? (sortRaw as BookSort) : "relevance";

  let min = nonNegativeInt(first(sp.min_price));
  let max = nonNegativeInt(first(sp.max_price));
  if (min !== undefined && max !== undefined && min > max) [min, max] = [max, min];

  const values: ListingValues = {
    sort,
    min_price: min,
    max_price: max,
    free_shipping: first(sp.free_shipping) === "true",
    on_sale: first(sp.on_sale) === "true",
    in_stock: first(sp.in_stock) === "true",
  };
  const page = Math.max(1, nonNegativeInt(first(sp.page)) ?? 1);

  return {
    values,
    page,
    api: {
      sort,
      page,
      page_size: 12,
      min_price: min,
      max_price: max,
      free_shipping: values.free_shipping || undefined,
      on_sale: values.on_sale || undefined,
      in_stock: values.in_stock || undefined,
    },
    activeFilters:
      Number(min !== undefined) +
      Number(max !== undefined) +
      Number(values.free_shipping) +
      Number(values.on_sale) +
      Number(values.in_stock),
  };
}

/** Parámetros de la URL como texto plano, sin `page`, para reconstruir enlaces de paginación. */
export function flattenParams(sp: RawSearchParams): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(sp)) {
    const v = first(value);
    if (key !== "page" && v) out[key] = v;
  }
  return out;
}
