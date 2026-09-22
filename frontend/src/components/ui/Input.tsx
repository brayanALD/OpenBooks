"use client";

import { useId } from "react";
import { cn } from "@/lib/cn";

export const fieldStyles =
  "w-full rounded-xl border bg-card px-4 py-2.5 text-base text-brand-900 placeholder:text-brand-600/80" +
  "transition-colors focus-visible:outline-accent disabled:cursor-not-allowed disabled:bg-surface";

type InputProps = React.ComponentProps<"input"> & {
  label: string;
  hint?: string;
  error?: string;
};

export function Input({ label, hint, error, id, className, ...props }: InputProps) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const describedBy = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-sm font-semibold text-brand-800">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cn(fieldStyles, error ? "border-accent" : "border-brand-200", className)}
        {...props}
      />
      {error ? (
        <p id={`${inputId}-error`} className="text-sm text-accent">
          {error}
        </p>
      ) : hint ? (
        <p id={`${inputId}-hint`} className="text-sm text-brand-600">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
