import { BookGridSkeleton } from "@/components/catalog/BookGrid";
import { LoadingRegion, Skeleton } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <LoadingRegion label="Cargando tus favoritos…" className="flex flex-col gap-6">
      <Skeleton className="h-5 w-40" />
      <Skeleton className="h-10 w-56" />
      <BookGridSkeleton count={5} layout="full" />
    </LoadingRegion>
  );
}
