import { cn } from "@/lib/cn";

/**
 * Bloque de carga. Se dimensiona desde fuera con las MISMAS medidas del contenido final
 * (`h-4 w-32`, `aspect-[2/3]`…) para que al llegar los datos no se mueva el diseño.
 * El pulso se desactiva con «reducir movimiento».
 */
export function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return <div aria-hidden className={cn("motion-safe:animate-pulse rounded-lg bg-brand-200/70", className)} {...props} />;
}

/**
 * Envuelve un conjunto de skeletons: un único aviso «Cargando…» para lectores de pantalla (los bloques van ocultos)
 * y `aria-busy`. Solo para cargas reales; un estado vacío o de error NO usa esto.
 */
export function LoadingRegion({ label, className, children }: { label: string; className?: string; children: React.ReactNode }) {
  return (
    <div role="status" aria-busy="true" className={className}>
      <span className="sr-only">{label}</span>
      {children}
    </div>
  );
}
