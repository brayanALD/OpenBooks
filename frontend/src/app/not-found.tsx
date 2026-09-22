import type { Metadata } from "next";
import { BookX } from "lucide-react";
import { Logo } from "@/components/layout/Logo";
import { ButtonLink } from "@/components/ui/Button";

export const metadata: Metadata = { title: "Página no encontrada", robots: { index: false, follow: false } };

/**
 * 404 global, para lo que queda fuera de la tienda (p. ej. /admin/* para quien no es administrador: responde
 * como si no existiera). Las rutas de la tienda tienen la suya, con cabecera y pie, en `(shop)/not-found.tsx`.
 */
export default function GlobalNotFound() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-6 px-4 text-center">
      <Logo />
      <BookX className="size-12 text-brand-400" aria-hidden />
      <h1 className="text-3xl font-bold">No encontramos esa página</h1>
      <p className="text-brand-800">Puede que el enlace tenga un error o que la página ya no exista.</p>
      <ButtonLink href="/">Ir al inicio</ButtonLink>
    </main>
  );
}
