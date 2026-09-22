"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { BadgeCheck, Trash2 } from "lucide-react";
import { StarRating } from "@/components/book/StarRating";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { requestJson } from "@/lib/auth-client";
import { formatDate } from "@/lib/format";
import { toast } from "@/store/ui.store";
import type { Review } from "@/types/catalog";

/** Retirar reseñas (también las de muestra). No se editan: solo se quitan las que no deben estar. */
export function ReviewModeration({ reviews }: { reviews: Review[] }) {
  const router = useRouter();
  const [target, setTarget] = useState<Review | null>(null);
  const [busy, setBusy] = useState(false);

  async function remove() {
    if (!target) return;
    setBusy(true);
    const result = await requestJson("DELETE", `/api/admin/reviews/${target.id}`);
    setBusy(false);
    if (!result.ok) return toast.error(result.message);
    toast.success("Reseña eliminada.");
    setTarget(null);
    router.refresh();
  }

  return (
    <section aria-labelledby="moderacion" className="rounded-2xl bg-card p-6 shadow-card">
      <h2 id="moderacion" className="mb-1 font-display text-2xl font-bold text-brand-600">
        Reseñas ({reviews.length})
      </h2>
      <p className="mb-4 text-sm text-brand-800">Puedes eliminar cualquier reseña, real o de muestra. No se pueden editar.</p>

      {reviews.length === 0 ? (
        <p className="text-brand-800">Este libro no tiene reseñas.</p>
      ) : (
        <ul className="divide-y divide-brand-100">
          {reviews.map((review) => (
            <li key={review.id} className="flex items-start justify-between gap-4 py-3">
              <div className="min-w-0">
                <p className="flex flex-wrap items-center gap-2 font-semibold">
                  {review.author_name}
                  {review.verified ? (
                    <Badge tone="success">
                      <BadgeCheck className="size-3.5" aria-hidden /> Verificada
                    </Badge>
                  ) : (
                    <Badge>De muestra</Badge>
                  )}
                  <span className="text-sm font-normal text-brand-600">{formatDate(review.created_at)}</span>
                </p>
                <StarRating rating={review.rating} size="sm" className="my-1" />
                <p className="whitespace-pre-line break-words text-brand-900">{review.comment}</p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setTarget(review)} aria-label={`Eliminar la reseña de ${review.author_name}`}>
                <Trash2 className="size-4" aria-hidden />
                Eliminar
              </Button>
            </li>
          ))}
        </ul>
      )}

      <Modal open={target !== null} onClose={() => setTarget(null)} title="¿Eliminar esta reseña?">
        <p className="text-brand-800">
          Se quitará la reseña de {target?.author_name} y cambiará la nota del libro. No se puede deshacer.
          {target?.verified && " Como es de un comprador verificado, podrá escribir otra."}
        </p>
        <div className="mt-6 flex flex-wrap justify-end gap-3">
          <Button variant="ghost" onClick={() => setTarget(null)} disabled={busy}>
            No, volver
          </Button>
          <Button onClick={remove} loading={busy}>
            Sí, eliminar
          </Button>
        </div>
      </Modal>
    </section>
  );
}
