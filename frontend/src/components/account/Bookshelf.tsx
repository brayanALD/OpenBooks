"use client";

import { useState } from "react";
import Image from "next/image";
import { BookQuickDetails } from "@/components/catalog/BookQuickDetails";
import { Modal } from "@/components/ui/Modal";
import type { BookSummary } from "@/types/catalog";
import type { LibraryUnavailableBook } from "@/types/library";

type Selected = { kind: "available"; book: BookSummary } | { kind: "unavailable"; book: LibraryUnavailableBook } | null;

/**
 * El librero: solo portadas, como una estantería. Nada de título, precio ni botones a la vista —
 * un clic en la portada abre un modal con la información (mismo contenido que la vista rápida del
 * catálogo para los libros que siguen en la tienda; un aviso simple para los que el admin ocultó).
 */
export function Bookshelf({ items, unavailable }: { items: BookSummary[]; unavailable: LibraryUnavailableBook[] }) {
  const [selected, setSelected] = useState<Selected>(null);

  return (
    <>
      <div className="grid grid-cols-[repeat(auto-fill,minmax(6rem,6rem))] justify-center gap-x-5 gap-y-10 sm:justify-start">
        {items.map((book) => (
          <button
            key={book.id}
            type="button"
            onClick={() => setSelected({ kind: "available", book })}
            aria-label={`Ver información de ${book.title}`}
            className="group flex w-24 flex-col items-center transition hover:-translate-y-1"
          >
            <span className="relative aspect-[2/3] w-full overflow-hidden rounded-md bg-brand-100 shadow-card group-hover:shadow-card-hover">
              <Image
                src={book.cover}
                alt=""
                fill
                sizes="96px"
                className="object-cover"
                placeholder={book.cover_blur ? "blur" : "empty"}
                blurDataURL={book.cover_blur ?? undefined}
              />
            </span>
            <span className="h-2 w-[85%] rounded-b-sm bg-brand-400" aria-hidden />
          </button>
        ))}

        {unavailable.map((book) => (
          <button
            key={book.book_id}
            type="button"
            onClick={() => setSelected({ kind: "unavailable", book })}
            aria-label={`Ver información de ${book.title}`}
            className="group flex w-24 flex-col items-center transition hover:-translate-y-1"
          >
            <span className="relative aspect-[2/3] w-full overflow-hidden rounded-md bg-brand-100 opacity-60 shadow-card grayscale group-hover:opacity-80 group-hover:shadow-card-hover">
              <Image src={book.cover} alt="" fill sizes="96px" className="object-cover" unoptimized={book.cover.startsWith("/media/")} />
            </span>
            <span className="h-2 w-[85%] rounded-b-sm bg-brand-400 opacity-60" aria-hidden />
          </button>
        ))}
      </div>

      <Modal open={selected !== null} onClose={() => setSelected(null)} title={selected?.book.title ?? ""} wide={selected?.kind === "available"}>
        {selected?.kind === "available" && <BookQuickDetails book={selected.book} onAdded={() => setSelected(null)} />}
        {selected?.kind === "unavailable" && (
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="relative aspect-[2/3] w-32 overflow-hidden rounded-xl bg-brand-100">
              <Image
                src={selected.book.cover}
                alt={`Portada de ${selected.book.title}`}
                fill
                sizes="128px"
                className="object-contain p-2"
                unoptimized={selected.book.cover.startsWith("/media/")}
              />
            </div>
            <p className="text-brand-800">por {selected.book.author_name}</p>
            <p className="rounded-xl bg-brand-100 px-4 py-3 text-sm text-brand-800">
              Ya no está disponible en la tienda: el vendedor lo retiró del catálogo, pero sigue siendo tuyo.
            </p>
          </div>
        )}
      </Modal>
    </>
  );
}
