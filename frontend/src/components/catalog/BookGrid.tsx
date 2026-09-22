import { Skeleton } from "@/components/ui/Skeleton";
import { cn } from "@/lib/cn";
import type { BookSummary } from "@/types/catalog";
import { BookCard } from "./BookCard";

const COLUMNS = {
  // Con panel de filtros lateral hay menos ancho útil.
  sidebar: "grid-cols-2 sm:grid-cols-3 xl:grid-cols-4",
  full: "grid-cols-2 sm:grid-cols-3 lg:grid-cols-5",
} as const;

type BookGridProps = {
  books: BookSummary[];
  layout?: keyof typeof COLUMNS;
  /** Cuántas portadas iniciales se cargan con prioridad. */
  priorityCount?: number;
  className?: string;
};

export function BookGrid({ books, layout = "full", priorityCount = 0, className }: BookGridProps) {
  return (
    <ul className={cn("grid gap-4", COLUMNS[layout], className)}>
      {books.map((book, index) => (
        <li key={book.id}>
          <BookCard book={book} priority={index < priorityCount} />
        </li>
      ))}
    </ul>
  );
}

export function BookGridSkeleton({ count = 8, layout = "sidebar" }: { count?: number; layout?: keyof typeof COLUMNS }) {
  return (
    <ul className={cn("grid gap-4", COLUMNS[layout])} aria-hidden>
      {Array.from({ length: count }, (_, i) => (
        <li key={i} className="flex flex-col gap-3 rounded-2xl bg-card p-3 shadow-card">
          <Skeleton className="aspect-[2/3] w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-6 w-2/5" />
        </li>
      ))}
    </ul>
  );
}
