import { LoadingRegion, Skeleton } from "@/components/ui/Skeleton";

/** Genérico del panel: título + bloque de contenido. Las tablas y el resumen comparten esta silueta. */
export default function Loading() {
  return (
    <LoadingRegion label="Cargando…" className="flex flex-col gap-6">
      <Skeleton className="h-10 w-56" />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-24 rounded-2xl" />
        ))}
      </div>
      <Skeleton className="h-72 w-full rounded-2xl" />
    </LoadingRegion>
  );
}
