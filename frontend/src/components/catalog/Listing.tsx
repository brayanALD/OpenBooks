import { SearchX } from "lucide-react";
import { ButtonLink } from "@/components/ui/Button";
import { getBooks, type BookListParams } from "@/lib/api-client";
import { flattenParams, parseListing, type RawSearchParams } from "@/lib/listing";
import { Skeleton } from "@/components/ui/Skeleton";
import { BookGrid, BookGridSkeleton } from "./BookGrid";
import { Filters } from "./Filters";
import { Pagination } from "./Pagination";

type ListingProps = {
  /** Ruta de la página (los filtros y la paginación navegan a ella). */
  basePath: string;
  searchParams: RawSearchParams;
  /** Parte fija de la consulta que no editan los filtros: la categoría o el texto buscado. */
  fixed: Pick<BookListParams, "category" | "q">;
};

export function ListingSkeleton() {
  return (
    <div className="grid gap-6 lg:grid-cols-[16rem_1fr]" role="status" aria-label="Cargando libros">
      <Skeleton className="hidden h-96 lg:block" />
      <BookGridSkeleton />
    </div>
  );
}

/** Filtros + resultados + paginación. Lo comparten la página de categoría y la de búsqueda. */
export async function Listing({ basePath, searchParams, fixed }: ListingProps) {
  const { values, api, page, activeFilters } = parseListing(searchParams);
  const result = await getBooks({ ...api, ...fixed });

  return (
    <div className="grid gap-6 lg:grid-cols-[16rem_1fr] lg:items-start">
      <aside className="lg:sticky lg:top-4">
        <Filters
          action={basePath}
          values={values}
          activeCount={activeFilters}
          hidden={fixed.q ? { q: fixed.q } : undefined}
        />
      </aside>

      <section aria-live="polite">
        <h2 className="sr-only">Resultados</h2>
        <p className="mb-4 text-brand-800">
          {result.total === 0
            ? "Sin resultados"
            : `${result.total} ${result.total === 1 ? "libro" : "libros"}`}
          {result.pages > 1 && ` · página ${result.page} de ${result.pages}`}
        </p>

        {result.items.length > 0 ? (
          <>
            <BookGrid books={result.items} layout="sidebar" priorityCount={4} />
            <Pagination page={result.page} pages={result.pages} basePath={basePath} query={flattenParams(searchParams)} />
          </>
        ) : (
          <div className="flex flex-col items-center gap-4 rounded-2xl bg-card px-6 py-14 text-center shadow-card">
            <SearchX className="size-10 text-brand-400" aria-hidden />
            <p className="max-w-sm text-lg text-brand-800">
              {page > 1
                ? "Esta página no existe."
                : "No encontramos libros con esos criterios. Prueba con otros filtros o palabras."}
            </p>
            <ButtonLink href={basePath} variant="outline" size="sm">
              Quitar filtros
            </ButtonLink>
          </div>
        )}
      </section>
    </div>
  );
}
