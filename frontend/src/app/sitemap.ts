import type { MetadataRoute } from "next";
import { getBooks, getCategories } from "@/lib/api-client";
import { SITE_URL } from "@/lib/seo";

// Se genera en cada petición: depende del catálogo vivo, y así `next build` no necesita el backend.
export const dynamic = "force-dynamic";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const categories = await getCategories();

  const books = [];
  for (let page = 1; ; page++) {
    const result = await getBooks({ page, page_size: 48 });
    books.push(...result.items);
    if (page >= result.pages) break;
  }

  return [
    { url: SITE_URL, changeFrequency: "daily", priority: 1 },
    ...categories.map((c) => ({
      url: `${SITE_URL}/categoria/${c.slug}`,
      changeFrequency: "weekly" as const,
      priority: 0.8,
    })),
    ...books.map((b) => ({
      url: `${SITE_URL}/libro/${b.slug}`,
      changeFrequency: "weekly" as const,
      priority: 0.6,
    })),
  ];
}
