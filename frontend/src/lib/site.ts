export const SITE = {
  name: "Open Books",
  description:
    "Librería virtual con clásicos, fantasía, biografías e historia. Libros en descuento y envío gratis en títulos seleccionados.",
  locale: "es-CO",
} as const;

/**
 * Categorías de la navegación, en el mismo orden que `GET /api/v1/categories`.
 * Provisional: en la Fase 3 se leerán de la API en lugar de estar escritas aquí.
 * El sitio original llamaba "bibliografia.html" a lo que en realidad son biografías;
 * "Novela" y "Desarrollo personal" son nuevas (9 libros no cabían en las 4 originales).
 */
export const CATEGORIES = [
  { slug: "clasicos", name: "Clásicos" },
  { slug: "fantasia", name: "Fantasía" },
  { slug: "novela", name: "Novela" },
  { slug: "biografias", name: "Biografías" },
  { slug: "historia", name: "Historia" },
  { slug: "desarrollo-personal", name: "Desarrollo personal" },
  { slug: "ciencia-ficcion", name: "Ciencia ficción" },
  { slug: "misterio", name: "Misterio" },
  { slug: "poesia", name: "Poesía" },
  { slug: "terror", name: "Terror" },
  { slug: "romance", name: "Romance" },
  { slug: "ciencia", name: "Ciencia" },
  { slug: "infantil", name: "Infantil" },
  { slug: "cocina", name: "Cocina" },
  { slug: "tecnologia", name: "Tecnología" },
] as const;

export const PROMO_TEXT = "Libros en descuento y con envío gratuito";
