"use client";

import { useId } from "react";
import { cn } from "@/lib/cn";
import { fieldStyles } from "./Input";

type TextareaProps = React.ComponentProps<"textarea"> & { label: string; hint?: string; error?: string };

export function Textarea({ label, hint, error, id, className, ...props }: TextareaProps) {
  const autoId = useId();
  const textareaId = id ?? autoId;
  const describedBy = error ? `${textareaId}-error` : hint ? `${textareaId}-hint` : undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={textareaId} className="text-sm font-semibold text-brand-800">
        {label}
      </label>
      <textarea
        id={textareaId}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cn(fieldStyles, "min-h-32 resize-y", error ? "border-accent" : "border-brand-200", className)}
        {...props}
      />
      {error ? (
        <p id={`${textareaId}-error`} className="text-sm text-accent">
          {error}
        </p>
      ) : hint ? (
        <p id={`${textareaId}-hint`} className="text-sm text-brand-600">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
