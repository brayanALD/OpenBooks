"use client";

import { useState } from "react";
import { SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";

/** En móvil los filtros se pliegan tras un botón; desde lg están siempre visibles en la barra lateral. */
export function FiltersPanel({ activeCount, children }: { activeCount: number; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <div>
      <Button
        variant="outline"
        size="sm"
        className="w-full lg:hidden"
        aria-expanded={open}
        aria-controls="filtros"
        onClick={() => setOpen((value) => !value)}
      >
        <SlidersHorizontal className="size-4" aria-hidden />
        Filtros{activeCount > 0 && ` (${activeCount})`}
      </Button>
      <div id="filtros" className={cn(open ? "mt-3 block" : "hidden", "lg:mt-0 lg:block")}>
        {children}
      </div>
    </div>
  );
}
