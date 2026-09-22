import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/cn";

type PaginationProps = {
  page: number;
  pages: number;
  basePath: string;
  /** Resto de parámetros de la URL (filtros, búsqueda…), sin `page`. */
  query: Record<string, string>;
};

/** Páginas a mostrar: primera, última y una ventana de ±1 alrededor de la actual; `null` = "…". */
function windowed(page: number, pages: number): (number | null)[] {
  const wanted = new Set([1, pages, page - 1, page, page + 1]);
  const numbers = [...wanted].filter((n) => n >= 1 && n <= pages).sort((a, b) => a - b);
  const out: (number | null)[] = [];
  numbers.forEach((n, i) => {
    if (i > 0 && n - numbers[i - 1] > 1) out.push(null);
    out.push(n);
  });
  return out;
}

export function Pagination({ page, pages, basePath, query }: PaginationProps) {
  if (pages <= 1) return null;

  const href = (target: number) => {
    const params = new URLSearchParams(query);
    if (target > 1) params.set("page", String(target));
    const qs = params.toString();
    return qs ? `${basePath}?${qs}` : basePath;
  };

  const item = "grid size-10 place-items-center rounded-full text-sm font-semibold transition-colors";

  return (
    <nav aria-label="Paginación" className="mt-8 flex items-center justify-center gap-1">
      {page > 1 ? (
        <Link href={href(page - 1)} rel="prev" aria-label="Página anterior" className={cn(item, "hover:bg-brand-100")}>
          <ChevronLeft className="size-5" aria-hidden />
        </Link>
      ) : (
        <span className={cn(item, "opacity-30")} aria-hidden>
          <ChevronLeft className="size-5" />
        </span>
      )}

      {windowed(page, pages).map((n, i) =>
        n === null ? (
          <span key={`gap-${i}`} className={cn(item, "text-brand-600")} aria-hidden>
            …
          </span>
        ) : n === page ? (
          <span key={n} aria-current="page" className={cn(item, "bg-brand-600 text-white")}>
            {n}
          </span>
        ) : (
          <Link key={n} href={href(n)} aria-label={`Página ${n}`} className={cn(item, "hover:bg-brand-100")}>
            {n}
          </Link>
        ),
      )}

      {page < pages ? (
        <Link href={href(page + 1)} rel="next" aria-label="Página siguiente" className={cn(item, "hover:bg-brand-100")}>
          <ChevronRight className="size-5" aria-hidden />
        </Link>
      ) : (
        <span className={cn(item, "opacity-30")} aria-hidden>
          <ChevronRight className="size-5" />
        </span>
      )}
    </nav>
  );
}
