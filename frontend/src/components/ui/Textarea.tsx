"use client";

import { useId } from "react";
import { cn } from "@/lib/cn";
import { FieldMessage } from "./FieldMessage";
import { fieldStyles } from "./Input";

type TextareaProps = React.ComponentProps<"textarea"> & { label: string; hint?: string; error?: string };

export function Textarea({ label, hint, error, id, className, ...props }: TextareaProps) {
  const autoId = useId();
  const textareaId = id ?? autoId;
  const describedBy = error ? `${textareaId}-error` : hint ? `${textareaId}-hint` : undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={textareaId} className="text-sm font-semibold text-ink-soft">
        {label}
      </label>
      <textarea
        id={textareaId}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cn(fieldStyles, "min-h-32 resize-y", error ? "border-danger" : "border-field", className)}
        {...props}
      />
      <FieldMessage id={error ? `${textareaId}-error` : `${textareaId}-hint`} error={error} hint={hint} />
    </div>
  );
}
