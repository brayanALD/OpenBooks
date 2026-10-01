import { LoadingRegion, Skeleton } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <LoadingRegion label="Cargando tu librero…" className="flex flex-col gap-6">
      <Skeleton className="h-5 w-40" />
      <Skeleton className="h-10 w-48" />
      <div className="grid grid-cols-3 gap-4 sm:grid-cols-5 lg:grid-cols-6">
        {Array.from({ length: 12 }, (_, i) => (
          <Skeleton key={i} className="aspect-[2/3] w-full" />
        ))}
      </div>
    </LoadingRegion>
  );
}
