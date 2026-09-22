"use client";

import Image from "next/image";
import Link from "next/link";
import { Trash2 } from "lucide-react";
import { formatCOP } from "@/lib/format";
import type { CartIssue, CartLine } from "@/types/cart";
import { QuantityStepper } from "./QuantityStepper";

const ISSUE_TEXT: Record<CartIssue, (max: number) => string> = {
  out_of_stock: () => "Agotado: no se incluye en el pedido.",
  limited_stock: (max) => `Solo quedan ${max} ${max === 1 ? "unidad" : "unidades"}.`,
  quantity_capped: (max) => `Máximo ${max} por pedido.`,
};

type CartItemRowProps = {
  line: CartLine;
  /** Cantidad del carrito (la fuente de verdad es el store, no la respuesta del servidor). */
  quantity: number;
  onQuantityChange: (quantity: number) => void;
  onRemove: () => void;
  onNavigate?: () => void;
};

export function CartItemRow({ line, quantity, onQuantityChange, onRemove, onNavigate }: CartItemRowProps) {
  const { book } = line;
  const soldOut = line.max_quantity === 0;
  // Total inmediato al pulsar +/−; el del servidor llega enseguida y manda en el resumen.
  const lineTotal = quantity <= line.max_quantity ? line.unit_price_cop * quantity : line.line_total_cop;

  return (
    <li className="flex gap-4 py-4">
      <Link
        href={`/libro/${book.slug}`}
        onClick={onNavigate}
        className="relative block h-24 w-16 shrink-0 overflow-hidden rounded-lg bg-brand-100"
        tabIndex={-1}
        aria-hidden
      >
        <Image src={book.cover} alt="" fill sizes="64px" className="object-contain p-1" />
      </Link>

      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <Link
          href={`/libro/${book.slug}`}
          onClick={onNavigate}
          className="line-clamp-2 font-display font-bold leading-snug hover:underline"
        >
          {book.title}
        </Link>
        <p className="text-sm text-brand-800">{book.author.name}</p>
        <p className="text-sm text-brand-800">
          {formatCOP(line.unit_price_cop)} c/u
          {book.discount_pct > 0 && <span className="ml-1 font-semibold text-accent">(-{book.discount_pct} %)</span>}
        </p>
        {line.issue && (
          <p className="text-sm font-semibold text-accent" role="status">
            {ISSUE_TEXT[line.issue](line.max_quantity)}
          </p>
        )}
        <div className="mt-1 flex items-center justify-between gap-2">
          <QuantityStepper
            value={quantity}
            max={line.max_quantity}
            onChange={onQuantityChange}
            label={`Cantidad de ${book.title}`}
            disabled={soldOut}
          />
          <span className={soldOut ? "text-sm text-brand-600 line-through" : "font-bold text-accent"}>
            {formatCOP(soldOut ? 0 : lineTotal)}
          </span>
        </div>
      </div>

      <button
        type="button"
        onClick={onRemove}
        aria-label={`Quitar ${book.title} del carrito`}
        className="-mr-2 -mt-1 h-fit rounded-full p-2 text-brand-600 transition-colors hover:bg-brand-100 hover:text-accent"
      >
        <Trash2 className="size-5" aria-hidden />
      </button>
    </li>
  );
}
