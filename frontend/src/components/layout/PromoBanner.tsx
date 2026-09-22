import { Truck } from "lucide-react";
import { PROMO_TEXT } from "@/lib/site";

/** Sustituye al <marquee> original: mismo mensaje, sin texto en movimiento (accesibilidad). */
export function PromoBanner() {
  return (
    <section aria-label="Promoción" className="bg-accent px-4 py-2 text-center text-sm font-semibold uppercase tracking-wide text-white">
      <p className="inline-flex items-center justify-center gap-2">
        <Truck className="size-4 shrink-0" aria-hidden />
        {PROMO_TEXT}
      </p>
    </section>
  );
}
