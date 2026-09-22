"use client";

import { Minus, Plus } from "lucide-react";
import { cn } from "@/lib/cn";

type QuantityStepperProps = {
  value: number;
  max: number;
  onChange: (value: number) => void;
  /** Para lectores de pantalla: «Cantidad de <título>». */
  label: string;
  disabled?: boolean;
};

const button =
  "grid size-9 place-items-center rounded-full text-brand-800 transition-colors hover:bg-brand-100 disabled:pointer-events-none disabled:opacity-30";

export function QuantityStepper({ value, max, onChange, label, disabled }: QuantityStepperProps) {
  return (
    <div role="group" aria-label={label} className={cn("inline-flex items-center rounded-full border border-brand-200 bg-card", disabled && "opacity-60")}>
      <button type="button" className={button} disabled={disabled || value <= 1} onClick={() => onChange(value - 1)} aria-label="Una unidad menos">
        <Minus className="size-4" aria-hidden />
      </button>
      <output aria-live="polite" className="min-w-8 text-center text-sm font-semibold tabular-nums">
        {value}
      </output>
      <button type="button" className={button} disabled={disabled || value >= max} onClick={() => onChange(value + 1)} aria-label="Una unidad más">
        <Plus className="size-4" aria-hidden />
      </button>
    </div>
  );
}
