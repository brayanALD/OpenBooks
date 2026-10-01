"use client";

import { useEffect } from "react";
import { CircleAlert, CircleCheck, Info, X } from "lucide-react";
import { cn } from "@/lib/cn";
import { useUIStore, type ToastItem, type ToastTone } from "@/store/ui.store";

const DURATION_MS = 4000;

const TONES: Record<ToastTone, { icon: typeof Info; style: string }> = {
  success: { icon: CircleCheck, style: "border-success-edge bg-success-soft text-success" },
  error: { icon: CircleAlert, style: "border-danger-edge bg-danger-soft text-danger" },
  info: { icon: Info, style: "border-info-edge bg-info-soft text-info" },
};

function Toast({ item }: { item: ToastItem }) {
  const dismiss = useUIStore((state) => state.dismiss);
  const { icon: Icon, style } = TONES[item.tone];

  useEffect(() => {
    const timer = setTimeout(() => dismiss(item.id), DURATION_MS);
    return () => clearTimeout(timer);
  }, [item.id, dismiss]);

  return (
    <div
      className={cn(
        "pointer-events-auto flex animate-toast-in items-center gap-3 rounded-2xl border py-3 pl-4 pr-3 shadow-card-hover",
        style,
      )}
    >
      <Icon className="size-5 shrink-0" aria-hidden />
      <p className="text-sm font-medium">{item.message}</p>
      <button
        type="button"
        onClick={() => dismiss(item.id)}
        aria-label="Cerrar aviso"
        className="-my-1 rounded-full p-2 transition-colors hover:bg-black/10"
      >
        <X className="size-4" aria-hidden />
      </button>
    </div>
  );
}

export function Toaster() {
  const toasts = useUIStore((state) => state.toasts);

  return (
    <div
      role="status"
      aria-live="polite"
      className="pointer-events-none fixed inset-x-4 bottom-4 z-50 flex flex-col items-center gap-2 sm:inset-x-auto sm:right-4 sm:items-end"
    >
      {toasts.map((item) => (
        <Toast key={item.id} item={item} />
      ))}
    </div>
  );
}
