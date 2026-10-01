import { LoadingRegion, Skeleton } from "@/components/ui/Skeleton";

/** Misma silueta que la cuenta: pedidos recientes, dos accesos y «Tus datos» plegado. */
export default function Loading() {
  return (
    <LoadingRegion label="Cargando tu cuenta…" className="mx-auto flex max-w-2xl flex-col gap-8">
      <div className="flex flex-col gap-2">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-5 w-56" />
      </div>
      <Skeleton className="h-60 w-full rounded-2xl" />
      <div className="grid gap-4 sm:grid-cols-2">
        <Skeleton className="h-[4.5rem] rounded-2xl" />
        <Skeleton className="h-[4.5rem] rounded-2xl" />
      </div>
      <Skeleton className="h-[4.5rem] w-full rounded-2xl" />
    </LoadingRegion>
  );
}
