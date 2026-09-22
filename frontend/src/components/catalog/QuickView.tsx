"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Eye, LoaderCircle } from "lucide-react";
import { PriceTag } from "@/components/book/PriceTag";
import { PurchaseBox } from "@/components/book/PurchaseBox";
import { ShippingBadge } from "@/components/book/ShippingBadge";
import { StarRating } from "@/components/book/StarRating";
import { Modal } from "@/components/ui/Modal";
import type { BookDetail, BookSummary } from "@/types/catalog";
import { FavoriteButton } from "./FavoriteButton";

type State = { status: "idle" | "loading" | "error" } | { status: "ready"; detail: BookDetail };

/** Botón «vista rápida» de las tarjetas: abre un modal con la descripción y la compra, sin salir de la lista. */
export function QuickView({ book }: { book: BookSummary }) {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<State>({ status: "idle" });

  async function show() {
    setOpen(true);
    if (state.status === "ready" || state.status === "loading") return;
    setState({ status: "loading" });
    try {
      const response = await fetch(`/api/books/${book.slug}`);
      if (!response.ok) throw new Error(String(response.status));
      setState({ status: "ready", detail: (await response.json()) as BookDetail });
    } catch {
      setState({ status: "error" });
    }
  }

  const detail = state.status === "ready" ? state.detail : null;
  const facts = detail
    ? [detail.publisher && `Editorial: ${detail.publisher}`, detail.pages && `${detail.pages} páginas`, detail.language && `Idioma: ${detail.language}`].filter(Boolean)
    : [];

  return (
    <>
      <button
        type="button"
        onClick={show}
        aria-label={`Vista rápida de ${book.title}`}
        title="Vista rápida"
        // `relative z-10` lo deja por encima del enlace que cubre toda la tarjeta.
        className="relative z-10 flex size-11 items-center justify-center rounded-full border-2 border-brand-600 text-brand-600 transition hover:bg-brand-600 hover:text-white"
      >
        <Eye className="size-6" aria-hidden />
      </button>

      <Modal open={open} onClose={() => setOpen(false)} title={book.title} wide>
        <div className="grid gap-5 sm:grid-cols-[10rem_1fr]">
          <div className="relative mx-auto aspect-[2/3] w-32 overflow-hidden rounded-xl bg-brand-100 sm:w-full">
            <Image src={book.cover} alt={`Portada de ${book.title}`} fill sizes="160px" className="object-contain p-2" />
          </div>

          <div className="flex min-w-0 flex-col gap-3">
            <p className="text-brand-800">{book.author.name}</p>
            <StarRating rating={book.rating_avg} count={book.rating_count} size="sm" />
            <PriceTag {...book} />
            <div>
              <ShippingBadge free={book.free_shipping} cost={book.shipping_cost_cop} />
            </div>

            {state.status === "loading" && (
              <p className="flex items-center gap-2 text-sm text-brand-800" role="status">
                <LoaderCircle className="size-4 animate-spin" aria-hidden /> Cargando la descripción…
              </p>
            )}
            {state.status === "error" && (
              <p className="text-sm text-accent" role="alert">
                No pudimos cargar la descripción. Puedes verla en la ficha completa.
              </p>
            )}
            {detail && (
              <>
                {detail.description && (
                  // Con foco de teclado: si el texto es largo y se desplaza, hay que poder recorrerlo sin ratón.
                  <div
                    role="region"
                    aria-label="Descripción"
                    tabIndex={0}
                    className="max-h-36 overflow-y-auto whitespace-pre-line pr-1 text-sm leading-relaxed"
                  >
                    {detail.description}
                  </div>
                )}
                {facts.length > 0 && <p className="text-sm text-brand-800">{facts.join(" · ")}</p>}
              </>
            )}

            <PurchaseBox bookId={book.id} stock={book.stock} onAdded={() => setOpen(false)} />

            <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
              <FavoriteButton bookId={book.id} title={book.title} variant="text" />
              <Link href={`/libro/${book.slug}`} className="text-sm font-semibold text-accent underline underline-offset-4">
                Ver ficha completa
              </Link>
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
}
