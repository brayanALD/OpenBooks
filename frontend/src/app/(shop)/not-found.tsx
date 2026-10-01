import { BookX } from "lucide-react";
import { ButtonLink } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";

export default function NotFound() {
  return (
    <EmptyState
      as="h1"
      icon={BookX}
      title="No encontramos esa página"
      description="Puede que el libro ya no esté disponible o que el enlace tenga un error."
    >
      <div className="flex flex-wrap justify-center gap-3">
        <ButtonLink href="/">Ir al inicio</ButtonLink>
        <ButtonLink href="/buscar" variant="outline">
          Ver el catálogo
        </ButtonLink>
      </div>
    </EmptyState>
  );
}
