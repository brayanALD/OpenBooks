import { CartSync } from "@/components/auth/CartSync";
import { WishlistSync } from "@/components/auth/WishlistSync";
import { SessionProvider } from "@/components/auth/SessionProvider";
import { CartDrawer } from "@/components/cart/CartDrawer";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { NavCategorias } from "@/components/layout/NavCategorias";
import { PromoBanner } from "@/components/layout/PromoBanner";
import { getCategories } from "@/lib/api-client";
import { getCurrentUser } from "@/lib/session";
import { CATEGORIES } from "@/lib/site";

// El catálogo lo sirve la API en cada petición; sin esto Next intentaría prerenderizar contra un backend
// que puede no estar levantado durante `next build`. Además la sesión depende de la cookie de cada petición.
export const dynamic = "force-dynamic";

/** Las categorías vienen de la API; si esta no responde, la navegación sigue funcionando con la lista de respaldo. */
async function loadNavCategories() {
  try {
    return await getCategories();
  } catch {
    return [...CATEGORIES];
  }
}

export default async function ShopLayout({ children }: { children: React.ReactNode }) {
  const [categories, user] = await Promise.all([loadNavCategories(), getCurrentUser()]);

  return (
    <SessionProvider user={user}>
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-full focus:bg-brand-900 focus:px-4 focus:py-2 focus:text-white"
      >
        Saltar al contenido
      </a>
      <PromoBanner />
      <Header />
      <NavCategorias categories={categories} />
      <main id="contenido" className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        {children}
      </main>
      <Footer />
      <CartDrawer />
      <CartSync />
      <WishlistSync />
    </SessionProvider>
  );
}
