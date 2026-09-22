"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";
import { requestJson } from "@/lib/auth-client";
import { toast } from "@/store/ui.store";

/** Oculta o vuelve a mostrar un libro en la tienda (no se borra nunca). */
export function ToggleActiveButton({ id, title, active }: { id: string; title: string; active: boolean }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function toggle() {
    setBusy(true);
    const result = await requestJson("PATCH", `/api/admin/books/${id}`, { active: !active });
    setBusy(false);
    if (!result.ok) {
      toast.error(result.message);
      return;
    }
    toast.success(active ? `«${title}» ya no se ve en la tienda.` : `«${title}» vuelve a estar visible.`);
    router.refresh();
  }

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={busy}
      aria-label={active ? `Ocultar ${title}` : `Mostrar ${title}`}
      title={active ? "Ocultar de la tienda" : "Mostrar en la tienda"}
      className="rounded-full p-2 text-brand-600 transition-colors hover:bg-brand-100 hover:text-accent disabled:opacity-40"
    >
      {active ? <EyeOff className="size-5" aria-hidden /> : <Eye className="size-5" aria-hidden />}
    </button>
  );
}
