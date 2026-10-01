import { CircleAlert } from "lucide-react";
import { cn } from "@/lib/cn";

/**
 * Mensaje bajo un campo: error (icono + texto, no solo color) o ayuda.
 * El campo lo enlaza con `aria-describedby` apuntando a `id`.
 */
export function FieldMessage({ id, error, hint }: { id: string; error?: string; hint?: string }) {
  if (!error && !hint) return null;
  return (
    <p id={id} className={cn("flex items-start gap-1.5 text-sm", error ? "font-medium text-danger" : "text-brand-600")}>
      {error && <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />}
      <span>{error ?? hint}</span>
    </p>
  );
}
