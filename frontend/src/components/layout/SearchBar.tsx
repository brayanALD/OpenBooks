import { Search } from "lucide-react";
import { cn } from "@/lib/cn";

/** Formulario GET nativo hacia /buscar: funciona sin JavaScript. */
export function SearchBar({ className, defaultValue }: { className?: string; defaultValue?: string }) {
  return (
    <form action="/buscar" method="get" role="search" className={cn("flex items-center gap-2", className)}>
      <label htmlFor="header-search" className="sr-only">
        Buscar libros
      </label>
      <input
        id="header-search"
        type="search"
        name="q"
        defaultValue={defaultValue}
        placeholder="Buscar libros, autores…"
        autoComplete="off"
        className="min-w-0 flex-1 rounded-full border border-brand-900/15 bg-card px-5 py-2.5 text-base text-brand-900 placeholder:text-brand-600/80"
      />
      <button
        type="submit"
        className="inline-flex shrink-0 items-center gap-2 rounded-full bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition duration-150 hover:bg-brand-800 active:scale-[0.97] sm:px-5"
      >
        <Search className="size-4" aria-hidden />
        <span className="hidden sm:inline">Buscar</span>
        <span className="sr-only sm:hidden">Buscar</span>
      </button>
    </form>
  );
}
