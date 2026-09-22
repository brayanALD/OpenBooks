import { cn } from "@/lib/cn";

/** Bloque de carga. Se dimensiona desde fuera con clases (`h-4 w-32`, `aspect-[2/3]`…). */
export function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      aria-hidden
      className={cn("animate-pulse rounded-lg bg-brand-200/70", className)}
      {...props}
    />
  );
}
