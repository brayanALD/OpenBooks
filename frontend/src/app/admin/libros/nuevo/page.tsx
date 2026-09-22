import type { Metadata } from "next";
import Link from "next/link";
import { BookForm } from "@/components/admin/BookForm";
import { getAdminBooks, requireAdmin } from "@/lib/admin";
import { getCategories } from "@/lib/api-client";

export const metadata: Metadata = { title: "Nuevo libro" };

export default async function NewBookPage() {
  await requireAdmin("/admin/libros/nuevo");
  const [categories, { authors }] = await Promise.all([getCategories(), getAdminBooks({ page: 1 })]);

  return (
    <div className="flex flex-col gap-6">
      <nav aria-label="Ruta de navegación" className="text-sm text-brand-800">
        <Link href="/admin/libros" className="hover:underline">
          Libros
        </Link>{" "}
        › <span className="font-semibold">Nuevo</span>
      </nav>
      <h1 className="text-4xl font-bold text-brand-600">Nuevo libro</h1>
      <BookForm categories={categories} authors={authors} />
    </div>
  );
}
