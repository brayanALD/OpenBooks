import { ThemeToggle } from "@/components/layout/ThemeToggle";
import type { Metadata } from "next";
import Link from "next/link";
import { Store } from "lucide-react";
import { AdminNav } from "@/components/admin/AdminNav";
import { Logo } from "@/components/layout/Logo";
import { requireAdmin } from "@/lib/admin";

export const metadata: Metadata = {
  title: { default: "Administración", template: "%s | Administración" },
  robots: { index: false, follow: false },
};

// La sesión depende de la cookie de cada petición.
export const dynamic = "force-dynamic";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  // Comprobación del layout. Los layouts no se vuelven a ejecutar al navegar entre páginas hijas, así que
  // cada página vuelve a llamar a `requireAdmin`: esta no es la única defensa.
  const user = await requireAdmin("/admin");

  return (
    <div className="flex min-h-screen flex-col">
      <header className="bg-brand-400 text-brand-900">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-3">
            <Logo />
            <span className="rounded-full bg-brand-900 px-3 py-0.5 text-xs font-bold uppercase tracking-wide text-brand-50">
              Administración
            </span>
          </div>
          <div className="flex items-center gap-4 text-sm font-semibold">
            <span className="hidden sm:inline">{user.first_name} {user.last_name}</span>
            <ThemeToggle />
            <Link href="/" className="inline-flex items-center gap-1.5 rounded-full px-3 py-2 hover:bg-brand-900/10">
              <Store className="size-4" aria-hidden />
              Ver la tienda
            </Link>
          </div>
        </div>
      </header>

      <div className="mx-auto grid w-full max-w-7xl flex-1 grid-cols-[minmax(0,1fr)] gap-6 px-4 py-6 md:grid-cols-[13rem_minmax(0,1fr)]">
        <aside aria-label="Administración" className="min-w-0 md:sticky md:top-4 md:self-start">
          <AdminNav />
        </aside>
        <main id="contenido" className="min-w-0">
          {children}
        </main>
      </div>
    </div>
  );
}
