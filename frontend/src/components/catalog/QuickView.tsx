"use client";

import { useState } from "react";
import { Eye } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import type { BookSummary } from "@/types/catalog";
import { BookQuickDetails } from "./BookQuickDetails";

/** Botón «vista rápida» de las tarjetas: abre un modal con la descripción y la compra, sin salir de la lista. */
export function QuickView({ book }: { book: BookSummary }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label={`Vista rápida de ${book.title}`}
        title="Vista rápida"
        // `relative z-10` lo deja por encima del enlace que cubre toda la tarjeta.
        className="relative z-10 flex size-11 items-center justify-center rounded-full border-2 border-brand-600 text-brand-600 transition hover:bg-brand-600 hover:text-white"
      >
        <Eye className="size-6" aria-hidden />
      </button>

      <Modal open={open} onClose={() => setOpen(false)} title={book.title} wide>
        {/* Montado solo mientras está abierto: así no se piden 12-48 fichas de golpe al cargar una grilla. */}
        {open && <BookQuickDetails book={book} onAdded={() => setOpen(false)} />}
      </Modal>
    </>
  );
}
