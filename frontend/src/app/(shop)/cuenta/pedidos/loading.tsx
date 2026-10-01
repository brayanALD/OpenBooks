import { LoadingRegion, Skeleton } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <LoadingRegion label="Cargando tus pedidos…" className="mx-auto flex max-w-3xl flex-col gap-6">
      <Skeleton className="h-5 w-40" />
      <Skeleton className="h-10 w-56" />
      <div className="flex flex-col gap-3">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-[5.5rem] w-full rounded-2xl" />
        ))}
      </div>
    </LoadingRegion>
  );
}
