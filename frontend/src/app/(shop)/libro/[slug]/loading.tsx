import { LoadingRegion, Skeleton } from "@/components/ui/Skeleton";

/** Ficha de libro: portada a la izquierda; título, precio y compra a la derecha. */
export default function Loading() {
  return (
    <LoadingRegion label="Cargando el libro…" className="flex flex-col gap-10">
      <Skeleton className="h-5 w-64" />
      <div className="grid gap-8 md:grid-cols-[minmax(0,20rem)_1fr] md:gap-12">
        <Skeleton className="mx-auto aspect-[2/3] w-full max-w-[13rem] rounded-2xl sm:max-w-xs md:max-w-none" />
        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-3">
            <Skeleton className="h-12 w-4/5" />
            <Skeleton className="h-6 w-1/3" />
            <Skeleton className="h-5 w-48" />
          </div>
          <Skeleton className="h-56 w-full rounded-2xl" />
          <Skeleton className="h-24 w-full" />
        </div>
      </div>
      <div className="flex max-w-3xl flex-col gap-3">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-11/12" />
        <Skeleton className="h-4 w-2/3" />
      </div>
    </LoadingRegion>
  );
}
