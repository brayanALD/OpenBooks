"use client";

import { useId } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/cn";
import { fieldStyles } from "./Input";

type SelectProps = React.ComponentProps<"select"> & {
  label: string;
  error?: string;
};

export function Select({ label, error, id, className, children, ...props }: SelectProps) {
  const autoId = useId();
  const selectId = id ?? autoId;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={selectId} className="text-sm font-semibold text-brand-800">
        {label}
      </label>
      <div className="relative">
        <select
          id={selectId}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${selectId}-error` : undefined}
          className={cn(
            fieldStyles,
            "appearance-none pr-10",
            error ? "border-accent" : "border-brand-200",
            className,
          )}
          {...props}
        >
          {children}
        </select>
        <ChevronDown
          className="pointer-events-none absolute right-3 top-1/2 size-5 -translate-y-1/2 text-brand-600"
          aria-hidden
        />
      </div>
      {error && (
        <p id={`${selectId}-error`} className="text-sm text-accent">
          {error}
        </p>
      )}
    </div>
  );
}
