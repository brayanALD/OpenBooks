import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Listing, ListingSkeleton } from "@/components/catalog/Listing";
import { getCategory } from "@/lib/api-client";
import type { RawSearchParams } from "@/lib/listing";

type Props = {
  params: Promise<{ slug: string }>;
  searchParams: Promise<RawSearchParams>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const category = await getCategory(slug);
  if (!category) return { title: "Categoría no encontrada" };
  return {
    title: category.name,
    description: `${category.description} ${category.book_count} libros de ${category.name.toLowerCase()} en Open Books.`,
    alternates: { canonical: `/categoria/${slug}` },
  };
}

export default async function CategoryPage({ params, searchParams }: Props) {
  const { slug } = await params;
  const category = await getCategory(slug);
  if (!category) notFound();

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-4xl font-bold text-brand-600">{category.name}</h1>
        {category.description && <p className="mt-2 max-w-2xl text-brand-800">{category.description}</p>}
      </header>
      {/* El Suspense va aquí y no en un loading.tsx: la categoría ya se comprobó arriba, así que un slug
          inválido responde 404 de verdad; con loading.tsx la respuesta ya habría salido como 200. */}
      <Suspense fallback={<ListingSkeleton />}>
        <Listing basePath={`/categoria/${slug}`} searchParams={await searchParams} fixed={{ category: slug }} />
      </Suspense>
    </div>
  );
}
