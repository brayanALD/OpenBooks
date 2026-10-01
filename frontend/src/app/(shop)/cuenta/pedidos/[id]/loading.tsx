import { LoadingRegion, Skeleton } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <LoadingRegion label="Cargando el pedido…" className="mx-auto flex max-w-3xl flex-col gap-6">
      <Skeleton className="h-5 w-56" />
      <div className="flex items-center justify-between gap-3">
        <Skeleton className="h-10 w-52" />
        <Skeleton className="h-6 w-24 rounded-full" />
      </div>
      <Skeleton className="h-64 w-full rounded-2xl" />
      <Skeleton className="h-40 w-full rounded-2xl" />
    </LoadingRegion>
  );
}
