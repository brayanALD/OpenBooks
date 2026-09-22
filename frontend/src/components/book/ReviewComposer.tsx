"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { BadgeCheck, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Textarea } from "@/components/ui/Textarea";
import { requestJson } from "@/lib/auth-client";
import { formatDate } from "@/lib/format";
import { toast } from "@/store/ui.store";
import type { MyReview, Review } from "@/types/catalog";
import { StarInput } from "./StarInput";
import { StarRating } from "./StarRating";

const MIN = 10;
const MAX = 2000;

type Props = {
  slug: string;
  /** null = sin sesión */
  mine: MyReview | null;
};

function ReviewForm({ slug, existing, onDone }: { slug: string; existing: Review | null; onDone: () => void }) {
  const router = useRouter();
  const [rating, setRating] = useState(existing?.rating ?? 0);
  const [comment, setComment] = useState(existing?.comment ?? "");
  const [errors, setErrors] = useState<{ rating?: string; comment?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);

    const found: typeof errors = {};
    if (rating < 1) found.rating = "Elige de 1 a 5 estrellas.";
    const length = comment.trim().length;
    if (length < MIN) found.comment = `Cuéntanos un poco más: mínimo ${MIN} caracteres.`;
    else if (length > MAX) found.comment = `Máximo ${MAX} caracteres.`;
    setErrors(found);
    if (Object.keys(found).length > 0) {
      (event.currentTarget.elements.namedItem(found.rating ? "rating-group" : "comment") as HTMLElement | null)?.focus?.();
      if (found.rating) event.currentTarget.querySelector<HTMLInputElement>("input[type=radio]")?.focus();
      return;
    }

    setSaving(true);
    const body = { rating, comment: comment.trim() };
    const result = existing
      ? await requestJson<Review>("PUT", `/api/books/${slug}/reviews/mine`, body)
      : await requestJson<Review>("POST", `/api/books/${slug}/reviews`, body);
    setSaving(false);

    if (!result.ok) {
      setFormError(result.message);
      if (result.status === 409 || result.status === 403) router.refresh(); // la situación cambió: se muestra la real
      return;
    }
    toast.success(existing ? "Reseña actualizada." : "¡Gracias por tu reseña!");
    onDone();
    router.refresh();
  }

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-4">
      {formError && (
        <p role="alert" className="rounded-xl bg-accent px-4 py-3 text-sm font-semibold text-white">
          {formError}
        </p>
      )}
      <StarInput value={rating} onChange={(v) => { setRating(v); setErrors((e) => ({ ...e, rating: undefined })); }} error={errors.rating} />
      <Textarea
        label="Tu reseña"
        name="comment"
        value={comment}
        maxLength={MAX + 200}
        hint={`${comment.trim().length}/${MAX} caracteres (mínimo ${MIN}).`}
        error={errors.comment}
        onChange={(e) => { setComment(e.target.value); setErrors((c) => ({ ...c, comment: undefined })); }}
      />
      <div className="flex flex-wrap gap-3">
        <Button type="submit" loading={saving}>
          {existing ? "Guardar cambios" : "Publicar reseña"}
        </Button>
        {existing && (
          <Button type="button" variant="ghost" onClick={onDone} disabled={saving}>
            Cancelar
          </Button>
        )}
      </div>
    </form>
  );
}

/** Zona de reseña del libro: cambia según la persona (sin sesión, sin compra, puede reseñar, ya reseñó). */
export function ReviewComposer({ slug, mine }: Props) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);

  const box = "flex flex-col gap-3 rounded-2xl bg-card p-5 shadow-card";

  if (mine === null) {
    return (
      <div className={box}>
        <h3 className="text-xl font-bold">¿Lo has leído?</h3>
        <p className="text-brand-800">Las reseñas las escriben quienes compraron el libro.</p>
        <p>
          <Link href={`/login?next=${encodeURIComponent(`/libro/${slug}`)}`} className="font-semibold text-accent underline underline-offset-4">
            Inicia sesión
          </Link>{" "}
          para dejar la tuya.
        </p>
      </div>
    );
  }

  if (mine.review) {
    async function remove() {
      setBusy(true);
      const result = await requestJson("DELETE", `/api/books/${slug}/reviews/mine`);
      setBusy(false);
      setConfirming(false);
      if (!result.ok) return toast.error(result.message);
      toast.info("Reseña eliminada.");
      router.refresh();
    }

    return (
      <div className={box}>
        <h3 className="text-xl font-bold">Tu reseña</h3>
        {editing ? (
          <ReviewForm slug={slug} existing={mine.review} onDone={() => setEditing(false)} />
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-3">
              <StarRating rating={mine.review.rating} size="sm" />
              <span className="inline-flex items-center gap-1 text-sm font-semibold text-emerald-800">
                <BadgeCheck className="size-4" aria-hidden /> Compra verificada
              </span>
              <span className="text-sm text-brand-600">
                {formatDate(mine.review.created_at)}
                {mine.review.updated_at && " · editada"}
              </span>
            </div>
            <p className="whitespace-pre-line">{mine.review.comment}</p>
            <div className="flex flex-wrap gap-3">
              <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
                <Pencil className="size-4" aria-hidden /> Editar
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setConfirming(true)}>
                <Trash2 className="size-4" aria-hidden /> Eliminar
              </Button>
            </div>
            <Modal open={confirming} onClose={() => setConfirming(false)} title="¿Eliminar tu reseña?">
              <p className="text-brand-800">Dejará de verse y cambiará la nota del libro. Podrás escribir otra después.</p>
              <div className="mt-6 flex flex-wrap justify-end gap-3">
                <Button variant="ghost" onClick={() => setConfirming(false)} disabled={busy}>
                  No, volver
                </Button>
                <Button onClick={remove} loading={busy}>
                  Sí, eliminar
                </Button>
              </div>
            </Modal>
          </>
        )}
      </div>
    );
  }

  if (!mine.has_purchased) {
    return (
      <div className={box}>
        <h3 className="text-xl font-bold">¿Lo has leído?</h3>
        <p className="text-brand-800">Solo pueden reseñar quienes compraron este libro. Cuando lo compres, podrás dejar aquí tu opinión.</p>
      </div>
    );
  }

  return (
    <div className={box}>
      <h3 className="text-xl font-bold">Deja tu reseña</h3>
      <p className="flex items-center gap-1 text-sm font-semibold text-emerald-800">
        <BadgeCheck className="size-4" aria-hidden /> Compraste este libro: tu reseña llevará la insignia «Compra verificada».
      </p>
      <ReviewForm slug={slug} existing={null} onDone={() => undefined} />
    </div>
  );
}
