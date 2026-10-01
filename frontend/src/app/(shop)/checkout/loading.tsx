import { CheckoutSkeleton } from "@/components/checkout/CheckoutSkeleton";
import { LoadingRegion, Skeleton } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <LoadingRegion label="Cargando el pago…" className="flex flex-col gap-6">
      <Skeleton className="h-10 w-56" />
      <CheckoutSkeleton />
    </LoadingRegion>
  );
}
