"use client";

import { useId } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/cn";
import { useDialog } from "@/lib/use-dialog";

type ModalProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  /** Más ancho, para contenido con columnas (vista rápida). */
  wide?: boolean;
};

/**
 * Modal sobre <dialog> nativo: gestiona el foco, Escape y el fondo inerte sin librerías.
 * Se cierra con Escape, con la X o al hacer clic en el fondo.
 */
export function Modal({ open, onClose, title, children, wide = false }: ModalProps) {
  const ref = useDialog(open);
  const titleId = useId();

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onClose={onClose}
      onClick={(event) => {
        // El clic llega al <dialog> solo si fue sobre el fondo (el contenido tiene su propio padding).
        if (event.target === ref.current) onClose();
      }}
      className={cn(
        "m-auto max-h-[calc(100dvh-2rem)] overflow-y-auto rounded-3xl bg-brand-50 p-0 text-ink shadow-card-hover backdrop:bg-brand-900/50 backdrop:backdrop-blur-sm",
        wide ? "w-[min(46rem,calc(100vw-2rem))]" : "w-[min(32rem,calc(100vw-2rem))]",
      )}
    >
      <div className="p-6">
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 id={titleId} className="text-2xl font-bold">
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="-m-2 rounded-full p-2 text-ink-muted transition-colors hover:bg-brand-100"
          >
            <X className="size-5" aria-hidden />
          </button>
        </div>
        {children}
      </div>
    </dialog>
  );
}
