"use client";

import { ServerCrash } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";

export default function ShopError({ reset }: { error: Error; reset: () => void }) {
  return (
    <EmptyState
      tone="error"
      as="h1"
      icon={ServerCrash}
      title="No pudimos cargar la página"
      description="Algo falló al pedir los datos al servidor. Comprueba que la API esté en marcha e inténtalo de nuevo."
    >
      <Button onClick={reset}>Reintentar</Button>
    </EmptyState>
  );
}
