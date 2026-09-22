import { BookX } from "lucide-react";
import { ButtonLink } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-4 py-16 text-center">
      <BookX className="size-12 text-brand-400" aria-hidden />
      <h1 className="text-3xl font-bold">No encontramos esa página</h1>
      <p className="text-brand-800">Puede que el libro ya no esté disponible o que el enlace tenga un error.</p>
      <div className="flex flex-wrap justify-center gap-3">
        <ButtonLink href="/">Ir al inicio</ButtonLink>
        <ButtonLink href="/buscar" variant="outline">
          Ver el catálogo
        </ButtonLink>
      </div>
    </div>
  );
}
