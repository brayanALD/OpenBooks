import { BookGridSkeleton } from "@/components/catalog/BookGrid";
import { LoadingRegion, Skeleton } from "@/components/ui/Skeleton";

/** Inicio: misma estructura que la página (portada, recomendados y dos estanterías). */
export default function Loading() {
  return (
    <LoadingRegion label="Cargando la tienda…" className="flex flex-col gap-14">
      <Skeleton className="h-72 w-full rounded-3xl sm:h-80" />
      <section className="flex flex-col gap-6">
        <Skeleton className="h-9 w-72" />
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-44 rounded-2xl" />
          <Skeleton className="hidden h-44 rounded-2xl lg:block" />
        </div>
      </section>
      <section className="flex flex-col gap-6">
        <Skeleton className="h-9 w-48" />
        <BookGridSkeleton count={5} layout="full" />
      </section>
    </LoadingRegion>
  );
}
