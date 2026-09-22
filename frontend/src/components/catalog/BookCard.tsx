import Image from "next/image";
import Link from "next/link";
import { PriceTag } from "@/components/book/PriceTag";
import { ShippingBadge } from "@/components/book/ShippingBadge";
import { StarRating } from "@/components/book/StarRating";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/cn";
import { CardActions } from "./CardActions";
import { FavoriteButton } from "./FavoriteButton";
import { QuickView } from "./QuickView";
import type { BookSummary } from "@/types/catalog";

type BookCardProps = {
  book: BookSummary;
  /** vertical: rejillas · horizontal: listas destacadas · mini: solo portada y título (relacionados) */
  variant?: "vertical" | "horizontal" | "mini";
  /** true para las portadas visibles al cargar (mejora el LCP). */
  priority?: boolean;
};

function Cover({ book, sizes, priority, favorite = false }: { book: BookSummary; sizes: string; priority: boolean; favorite?: boolean }) {
  return (
    // Proporción fija 2:3 y `object-contain`: las portadas originales tienen formas distintas y no se recortan.
    <div className="relative aspect-[2/3] w-full overflow-hidden rounded-xl bg-brand-100">
      <Image
        src={book.cover}
        alt={`Portada de ${book.title}`}
        fill
        sizes={sizes}
        priority={priority}
        placeholder={book.cover_blur ? "blur" : "empty"}
        blurDataURL={book.cover_blur ?? undefined}
        className="object-contain p-2 transition-transform duration-300 group-hover:scale-[1.03]"
      />
      {book.discount_pct > 0 && (
        <Badge tone="accent" className="absolute left-2 top-2 shadow">
          -{book.discount_pct} %
        </Badge>
      )}
      {!book.in_stock && (
        <Badge className="absolute bottom-2 left-2 bg-brand-900 text-white shadow">Agotado</Badge>
      )}
      {favorite && <FavoriteButton bookId={book.id} title={book.title} className="absolute right-2 top-2" />}
    </div>
  );
}

/** Todo el tarjetón es clicable a través del enlace del título (`after:absolute after:inset-0`). */
function TitleLink({ book, className }: { book: BookSummary; className?: string }) {
  return (
    <Link
      href={`/libro/${book.slug}`}
      className={cn("font-display font-bold leading-snug after:absolute after:inset-0 after:content-['']", className)}
    >
      {book.title}
    </Link>
  );
}

export function BookCard({ book, variant = "vertical", priority = false }: BookCardProps) {
  if (variant === "mini") {
    return (
      <article className="group relative flex flex-col gap-2">
        <Cover book={book} sizes="(min-width: 640px) 160px, 40vw" priority={priority} />
        <h3 className="text-sm">
          <TitleLink book={book} className="line-clamp-2" />
        </h3>
      </article>
    );
  }

  if (variant === "horizontal") {
    return (
      <article className="group relative flex h-full gap-4 rounded-2xl bg-card p-4 shadow-card transition duration-200 hover:shadow-card-hover sm:gap-6 sm:p-5">
        <div className="w-28 shrink-0 sm:w-40">
          <Cover book={book} sizes="(min-width: 640px) 160px, 112px" priority={priority} favorite />
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <h3 className="text-xl sm:text-2xl">
            <TitleLink book={book} />
          </h3>
          <p className="text-brand-800">{book.author.name}</p>
          <StarRating rating={book.rating_avg} count={book.rating_count} size="sm" />
          <PriceTag {...book} size="md" className="mt-auto" />
          <div>
            <ShippingBadge free={book.free_shipping} cost={book.shipping_cost_cop} />
          </div>
          <div className="mt-2 flex gap-2">
          <CardActions bookId={book.id} title={book.title} stock={book.stock} />
          <QuickView book={book} />
        </div>
        </div>
      </article>
    );
  }

  return (
    <article className="group relative flex h-full flex-col gap-3 rounded-2xl bg-card p-3 shadow-card transition duration-200 hover:-translate-y-1 hover:shadow-card-hover">
      <Cover book={book} sizes="(min-width: 1280px) 220px, (min-width: 640px) 30vw, 46vw" priority={priority} favorite />
      <div className="flex flex-1 flex-col gap-1.5 px-1 pb-1">
        <h3 className="text-base">
          <TitleLink book={book} className="line-clamp-2" />
        </h3>
        <p className="line-clamp-1 text-sm text-brand-800">{book.author.name}</p>
        <StarRating rating={book.rating_avg} size="sm" />
        <PriceTag {...book} className="mt-auto pt-1" />
        <div>
          <ShippingBadge free={book.free_shipping} cost={book.shipping_cost_cop} />
        </div>
        <div className="mt-2 flex gap-2">
          <CardActions bookId={book.id} title={book.title} stock={book.stock} />
          <QuickView book={book} />
        </div>
      </div>
    </article>
  );
}
