import type { Metadata } from "next";
import Link from "next/link";
import { Heart } from "lucide-react";
import { BookGrid } from "@/components/catalog/BookGrid";
import { ButtonLink } from "@/components/ui/Button";
import { requireUser } from "@/lib/session";
import { getMyFavorites } from "@/lib/wishlist";
import { EmptyState } from "@/components/ui/EmptyState";

export const metadata: Metadata = { title: "Mis favoritos", robots: { index: false, follow: false } };

export default async function FavoritesPage() {
  await requireUser("/cuenta/favoritos");
  const books = await getMyFavorites();

  return (
    <div className="flex flex-col gap-6">
      <nav aria-label="Ruta de navegación" className="text-sm text-ink-soft">
        <Link href="/cuenta" className="hover:underline">
          Mi cuenta
        </Link>{" "}
        › <span className="font-semibold">Mis favoritos</span>
      </nav>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="text-4xl font-bold text-ink-muted">Mis favoritos</h1>
        {books.length > 0 && (
          <p className="text-ink-soft">
            {books.length} {books.length === 1 ? "libro" : "libros"}
          </p>
        )}
      </div>

      {books.length === 0 ? (
        <EmptyState icon={Heart} title="Todavía no tienes favoritos" description="Toca el corazón de un libro para guardarlo aquí y encontrarlo después.">
          <ButtonLink href="/buscar">Ver el catálogo</ButtonLink>
        </EmptyState>
      ) : (
        <>
          <h2 className="sr-only">Libros guardados</h2>
          <BookGrid books={books} />
        </>
      )}
    </div>
  );
}
