import type { Metadata } from "next";
import Link from "next/link";
import { Library } from "lucide-react";
import { Bookshelf } from "@/components/account/Bookshelf";
import { ButtonLink } from "@/components/ui/Button";
import { getMyLibrary } from "@/lib/library";
import { requireUser } from "@/lib/session";

export const metadata: Metadata = { title: "Mi librero", robots: { index: false, follow: false } };

export default async function LibraryPage() {
  await requireUser("/cuenta/librero");
  const { items, unavailable } = await getMyLibrary();
  const total = items.length + unavailable.length;

  return (
    <div className="flex flex-col gap-6">
      <nav aria-label="Ruta de navegación" className="text-sm text-brand-800">
        <Link href="/cuenta" className="hover:underline">
          Mi cuenta
        </Link>{" "}
        › <span className="font-semibold">Mi librero</span>
      </nav>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="text-4xl font-bold text-brand-600">Mi librero</h1>
        {total > 0 && (
          <p className="text-brand-800">
            {total} {total === 1 ? "libro" : "libros"}
          </p>
        )}
      </div>

      {total === 0 ? (
        <div className="mx-auto flex max-w-xl flex-col items-center gap-4 rounded-2xl bg-card p-10 text-center shadow-card">
          <Library className="size-12 text-brand-400" aria-hidden />
          <p className="font-display text-2xl font-bold">Todavía no has comprado ningún libro</p>
          <p className="text-brand-800">Los libros que compres aparecerán aquí, todos en un mismo lugar.</p>
          <ButtonLink href="/buscar">Ver el catálogo</ButtonLink>
        </div>
      ) : (
        <>
          <h2 className="sr-only">Libros comprados</h2>
          <Bookshelf items={items} unavailable={unavailable} />
        </>
      )}
    </div>
  );
}
