"use client";

import { useId } from "react";
import { Star } from "lucide-react";
import { cn } from "@/lib/cn";

type StarInputProps = { value: number; onChange: (value: number) => void; error?: string };

/**
 * Valoración de 1 a 5. Son cinco botones de opción (radio) reales: con teclado se recorre con las flechas,
 * los lectores de pantalla anuncian «3 de 5 estrellas», y no depende de que el ratón pase por encima.
 */
export function StarInput({ value, onChange, error }: StarInputProps) {
  const name = useId();

  return (
    <fieldset aria-describedby={error ? `${name}-error` : undefined}>
      <legend className="mb-1 text-sm font-semibold text-brand-800">Tu valoración</legend>
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((n) => (
          <label
            key={n}
            className="relative cursor-pointer rounded-md p-0.5 transition-transform hover:scale-110 has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-accent"
          >
            <input
              type="radio"
              name={name}
              value={n}
              checked={value === n}
              onChange={() => onChange(n)}
              className="peer sr-only"
              aria-label={`${n} ${n === 1 ? "estrella" : "estrellas"}`}
            />
            <Star
              className={cn("size-8 transition-colors", n <= value ? "fill-amber-500 text-amber-500" : "fill-brand-100 text-brand-400")}
              aria-hidden
            />
          </label>
        ))}
        <span className="ml-2 text-sm font-medium text-brand-800" aria-live="polite">
          {value > 0 ? `${value} de 5` : "Elige de 1 a 5"}
        </span>
      </div>
      {error && (
        <p id={`${name}-error`} className="mt-1 text-sm text-accent">
          {error}
        </p>
      )}
    </fieldset>
  );
}
