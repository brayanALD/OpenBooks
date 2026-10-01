import { useEffect, useRef } from "react";

/**
 * Sincroniza un <dialog> nativo con un estado `open`: lo abre como modal (foco atrapado, Escape y fondo inerte)
 * o lo cierra. Lo comparten el modal genérico y el cajón del carrito.
 */
export function useDialog(open: boolean) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return ref;
}
