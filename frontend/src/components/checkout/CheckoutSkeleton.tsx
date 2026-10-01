import { Skeleton } from "@/components/ui/Skeleton";

/**
 * Silueta del pago: envío + pago a la izquierda, resumen a la derecha. La usan `checkout/loading.tsx` (servidor)
 * y el formulario mientras hidrata el carrito, para que no haya saltos entre un estado y otro.
 */
export function CheckoutSkeleton() {
  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_24rem] lg:items-start">
      <div className="flex flex-col gap-8">
        <Skeleton className="h-[26rem] w-full rounded-2xl" />
        <Skeleton className="h-[30rem] w-full rounded-2xl" />
      </div>
      <Skeleton className="h-80 w-full rounded-2xl" />
    </div>
  );
}
