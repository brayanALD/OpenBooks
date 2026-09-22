import Image from "next/image";
import { formatCOP } from "@/lib/format";
import type { CartLine } from "@/types/cart";

/** Líneas del carrito en versión compacta, para el resumen del checkout. */
export function CartItemsSummary({ lines, quantityOf }: { lines: CartLine[]; quantityOf: (bookId: string) => number }) {
  return (
    <ul className="flex flex-col divide-y divide-brand-200">
      {lines.map((line) => {
        const quantity = Math.min(quantityOf(line.book.id), line.max_quantity);
        return (
          <li key={line.book.id} className="flex gap-3 py-3 first:pt-0">
            <span className="relative block h-16 w-11 shrink-0 overflow-hidden rounded-md bg-brand-100">
              <Image src={line.book.cover} alt="" fill sizes="44px" className="object-contain p-0.5" />
            </span>
            <span className="flex min-w-0 flex-1 flex-col">
              <span className="line-clamp-2 font-display text-sm font-bold leading-snug">{line.book.title}</span>
              <span className="text-sm text-brand-800">
                {quantity} × {formatCOP(line.unit_price_cop)}
              </span>
              {line.issue && <span className="text-xs font-semibold text-accent">No disponible en esta cantidad</span>}
            </span>
            <span className="text-sm font-bold text-accent">{formatCOP(line.line_total_cop)}</span>
          </li>
        );
      })}
    </ul>
  );
}
