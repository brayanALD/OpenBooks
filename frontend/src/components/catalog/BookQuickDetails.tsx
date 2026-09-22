"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { LoaderCircle } from "lucide-react";
import { PriceTag } from "@/components/book/PriceTag";
import { PurchaseBox } from "@/components/book/PurchaseBox";
import { ShippingBadge } from "@/components/book/ShippingBadge";
import { StarRating } from "@/components/book/StarRating";
import type { BookDetail, BookSummary } from "@/types/catalog";
import { FavoriteButton } from "./FavoriteButton";

type State = { status: "loading" | "error" } | { status: "ready"; detail: BookDetail };

/**
 * Contenido de un libro para un modal «vista rápida»: portada, datos, descripción (cargada al montar)
 * y acciones. Lo usan `QuickView` (icono del ojo en las tarjetas) y `Bookshelf` (portada del librero).
 */
export function BookQuickDetails({ book, onAdded }: { book: BookSummary; onAdded?: () => void }) {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/books/${book.slug}`)
      .then((response) => {
        if (!response.ok) throw new Error(String(response.status));
        return response.json() as Promise<BookDetail>;
      })
      .then((detail) => {
        if (!cancelled) setState({ status: "ready", detail });
      })
      .catch(() => {
        if (!cancelled) setState({ status: "error" });
      });
    return () => {
      cancelled = true; // el modal se cerró (o cambió de libro) antes de que respondiera el fetch
    };
  }, [book.slug]);

  const detail = state.status === "ready" ? state.detail : null;
  const facts = detail
    ? [
        detail.publisher && `Editorial: ${detail.publisher}`,
        detail.pages && `${detail.pages} páginas`,
        detail.language && `Idioma: ${detail.language}`,
        detail.isbn && `ISBN: ${detail.isbn}`,
      ].filter(Boolean)
    : [];

  return (
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

        <PurchaseBox bookId={book.id} stock={book.stock} onAdded={onAdded} />

        <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
          <FavoriteButton bookId={book.id} title={book.title} variant="text" />
          <Link href={`/libro/${book.slug}`} className="text-sm font-semibold text-accent underline underline-offset-4">
            Ver ficha completa
          </Link>
        </div>
      </div>
    </div>
  );
}
