import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ExternalLink } from "lucide-react";
import { BookForm } from "@/components/admin/BookForm";
import { ReviewModeration } from "@/components/admin/ReviewModeration";
import { getAdminBook, getAdminBookReviews, getAdminBooks, requireAdmin } from "@/lib/admin";
import { getCategories } from "@/lib/api-client";

export const metadata: Metadata = { title: "Editar libro" };

export default async function EditBookPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await requireAdmin(`/admin/libros/${id}`);
  const [book, categories, { authors }, reviews] = await Promise.all([
    getAdminBook(id),
    getCategories(),
    getAdminBooks({ page: 1 }),
    getAdminBookReviews(id),
  ]);
  if (!book) notFound();

  return (
    <div className="flex flex-col gap-6">
      <nav aria-label="Ruta de navegación" className="text-sm text-brand-800">
        <Link href="/admin/libros" className="hover:underline">
          Libros
        </Link>{" "}
        › <span className="font-semibold">{book.title}</span>
      </nav>
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-4xl font-bold text-brand-600">Editar libro</h1>
        {book.active && (
          <Link href={`/libro/${book.slug}`} target="_blank" className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-600 underline underline-offset-4 hover:text-accent">
            Ver en la tienda
            <ExternalLink className="size-4" aria-hidden />
          </Link>
        )}
      </header>
      <BookForm book={book} categories={categories} authors={authors} />
      <ReviewModeration reviews={reviews ?? []} />
    </div>
  );
}
