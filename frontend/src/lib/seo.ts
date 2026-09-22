import type { BookDetail } from "@/types/catalog";

export const SITE_URL = process.env.SITE_URL ?? "http://localhost:3000";

/** Datos estructurados para que buscadores muestren precio, disponibilidad y valoración. */
export function bookJsonLd(book: BookDetail) {
  return {
    "@context": "https://schema.org",
    "@type": ["Product", "Book"],
    name: book.title,
    image: `${SITE_URL}${book.cover}`,
    description: book.description || undefined,
    url: `${SITE_URL}/libro/${book.slug}`,
    author: { "@type": "Person", name: book.author.name },
    inLanguage: book.language ?? undefined,
    numberOfPages: book.pages ?? undefined,
    publisher: book.publisher ? { "@type": "Organization", name: book.publisher } : undefined,
    offers: {
      "@type": "Offer",
      priceCurrency: "COP",
      price: book.final_price_cop,
      availability: book.in_stock ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
      url: `${SITE_URL}/libro/${book.slug}`,
    },
    // Sin aggregateRating a propósito: hoy las reseñas son de muestra y no deben presentarse como reales.
  };
}

/** Serializa JSON-LD para incrustarlo en <script>: evita que un "</script>" en los datos cierre la etiqueta. */
export function serializeJsonLd(data: unknown): string {
  return JSON.stringify(data).replace(/</g, "\\u003c");
}
