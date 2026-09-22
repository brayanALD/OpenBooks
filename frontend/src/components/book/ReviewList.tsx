import { BadgeCheck, Info } from "lucide-react";
import { formatDate } from "@/lib/format";
import type { Review } from "@/types/catalog";
import { StarRating } from "./StarRating";

export function ReviewList({ reviews }: { reviews: Review[] }) {
  if (reviews.length === 0) {
    return <p className="text-brand-800">Este libro todavía no tiene reseñas.</p>;
  }

  return (
    <div className="flex flex-col gap-4">
      {reviews.some((r) => r.is_demo) && (
        <p className="flex items-start gap-2 rounded-xl bg-brand-100 p-3 text-sm text-brand-800">
          <Info className="mt-0.5 size-4 shrink-0" aria-hidden />
          Las reseñas sin la insignia «Compra verificada» son de muestra para desarrollo: no son de compradores reales.
        </p>
      )}
      <ul className="flex flex-col gap-4">
        {reviews.map((review) => (
          <li key={review.id} className="rounded-2xl bg-card p-5 shadow-card">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="flex flex-wrap items-center gap-2 font-semibold">
                {review.author_name}
                {review.verified && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-900">
                    <BadgeCheck className="size-3.5" aria-hidden /> Compra verificada
                  </span>
                )}
              </p>
              <time dateTime={review.created_at} className="text-sm text-brand-600">
                {formatDate(review.created_at)}
                {review.updated_at && " · editada"}
              </time>
            </div>
            <StarRating rating={review.rating} size="sm" className="mt-1" />
            {/* Texto plano: React lo escapa. Los saltos de línea de quien escribe se respetan. */}
            <p className="mt-3 whitespace-pre-line text-brand-900">{review.comment}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
