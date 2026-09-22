import type { Metadata } from "next";
import { Listing } from "@/components/catalog/Listing";
import type { RawSearchParams } from "@/lib/listing";

type Props = { searchParams: Promise<RawSearchParams> };

const queryOf = (sp: RawSearchParams) => {
  const raw = Array.isArray(sp.q) ? sp.q[0] : sp.q;
  return raw?.trim().slice(0, 100) || undefined;
};

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const q = queryOf(await searchParams);
  return {
    title: q ? `Resultados para «${q}»` : "Todos los libros",
    // Las búsquedas son infinitas: no interesa que Google las indexe.
    robots: { index: false, follow: true },
  };
}

export default async function SearchPage({ searchParams }: Props) {
  const sp = await searchParams;
  const q = queryOf(sp);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-4xl font-bold text-brand-600">{q ? `Resultados para «${q}»` : "Todos los libros"}</h1>
      <Listing basePath="/buscar" searchParams={sp} fixed={{ q }} />
    </div>
  );
}
