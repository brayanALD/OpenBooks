import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/seo";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Páginas privadas o sin valor para buscadores.
      disallow: ["/admin", "/carrito", "/checkout", "/cuenta", "/login", "/registro", "/buscar"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
