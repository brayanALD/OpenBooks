import { Star } from "lucide-react";
import { cn } from "@/lib/cn";
import { formatRating } from "@/lib/format";

type StarRatingProps = {
  rating: number | null;
  count?: number;
  size?: "sm" | "md";
  className?: string;
};

function Stars({ className }: { className: string }) {
  return (
    <span className={cn("flex", className)}>
      {Array.from({ length: 5 }, (_, i) => (
        <Star key={i} className="h-full w-1/5 shrink-0 fill-current" aria-hidden />
      ))}
    </span>
  );
}

/** Estrellas con relleno proporcional (4,5 = cuatro y media), sustituye a las imágenes de estrellas del original. */
export function StarRating({ rating, count, size = "md", className }: StarRatingProps) {
  const dimension = size === "sm" ? "h-4 w-[5rem]" : "h-5 w-[6.25rem]";

  if (rating === null) {
    return <span className={cn("text-sm text-brand-600", className)}>Sin reseñas</span>;
  }

  const label = `${formatRating(rating)} de 5 estrellas${count !== undefined ? `, ${count} reseñas` : ""}`;
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <span role="img" aria-label={label} className={cn("relative inline-block", dimension)}>
        <Stars className="h-full text-brand-200" />
        <span className="absolute inset-y-0 left-0 overflow-hidden" style={{ width: `${(rating / 5) * 100}%` }}>
          <Stars className={cn("h-full text-amber-500", size === "sm" ? "w-[5rem]" : "w-[6.25rem]")} />
        </span>
      </span>
      <span className="text-sm font-medium text-brand-800" aria-hidden>
        {formatRating(rating)}
        {count !== undefined && <span className="text-brand-600"> ({count})</span>}
      </span>
    </span>
  );
}
