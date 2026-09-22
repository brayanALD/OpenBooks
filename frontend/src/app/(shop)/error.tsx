"use client";

import { ServerCrash } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function ShopError({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-4 py-16 text-center">
      <ServerCrash className="size-12 text-brand-400" aria-hidden />
      <h1 className="text-3xl font-bold">No pudimos cargar el catálogo</h1>
      <p className="text-brand-800">
        Algo falló al pedir los datos al servidor. Comprueba que la API esté en marcha e inténtalo de nuevo.
      </p>
      <Button onClick={reset}>Reintentar</Button>
    </div>
  );
}
