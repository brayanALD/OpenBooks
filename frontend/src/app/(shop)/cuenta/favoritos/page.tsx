import type { Metadata } from "next";
import Link from "next/link";
import { Heart } from "lucide-react";
import { BookGrid } from "@/components/catalog/BookGrid";
import { ButtonLink } from "@/components/ui/Button";
import { requireUser } from "@/lib/session";
import { getMyFavorites } from "@/lib/wishlist";

export const metadata: Metadata = { title: "Mis favoritos", robots: { index: false, follow: false } };

export default async function FavoritesPage() {
  await requireUser("/cuenta/favoritos");
  const books = await getMyFavorites();

  return (
    <div className="flex flex-col gap-6">
      <nav aria-label="Ruta de navegación" className="text-sm text-brand-800">
        <Link href="/cuenta" className="hover:underline">
          Mi cuenta
        </Link>{" "}
        › <span className="font-semibold">Mis favoritos</span>
      </nav>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="text-4xl font-bold text-brand-600">Mis favoritos</h1>
        {books.length > 0 && (
          <p className="text-brand-800">
            {books.length} {books.length === 1 ? "libro" : "libros"}
          </p>
        )}
      </div>

      {books.length === 0 ? (
        <div className="mx-auto flex max-w-xl flex-col items-center gap-4 rounded-2xl bg-card p-10 text-center shadow-card">
          <Heart className="size-12 text-brand-400" aria-hidden />
          <p className="font-display text-2xl font-bold">Todavía no tienes favoritos</p>
          <p className="text-brand-800">Toca el corazón de un libro para guardarlo aquí y encontrarlo después.</p>
          <ButtonLink href="/buscar">Ver el catálogo</ButtonLink>
        </div>
      ) : (
        <>
          <h2 className="sr-only">Libros guardados</h2>
          <BookGrid books={books} />
        </>
      )}
    </div>
  );
}
