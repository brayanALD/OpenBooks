"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/cn";

type NavCategoriasProps = { categories: { slug: string; name: string }[] };

const ARROW =
  "absolute top-1/2 z-10 hidden size-8 -translate-y-1/2 items-center justify-center rounded-full bg-brand-800 text-white shadow transition-opacity hover:bg-brand-900 md:flex";

/** Barra de categorías en una sola fila que se desliza; en pantallas anchas se añaden flechas en los extremos. */
export function NavCategorias({ categories }: NavCategoriasProps) {
  const pathname = usePathname();
  const scroller = useRef<HTMLUListElement>(null);
  const [canScroll, setCanScroll] = useState({ left: false, right: false });

  const update = useCallback(() => {
    const el = scroller.current;
    if (!el) return;
    setCanScroll({ left: el.scrollLeft > 4, right: el.scrollLeft + el.clientWidth < el.scrollWidth - 4 });
  }, []);

  useEffect(() => {
    update();
    const el = scroller.current;
    if (!el) return;
    // Que la categoría activa quede a la vista al abrir su página.
    el.querySelector<HTMLElement>('[aria-current="page"]')?.scrollIntoView({ inline: "center", block: "nearest" });
    const observer = new ResizeObserver(update);
    observer.observe(el);
    return () => observer.disconnect();
  }, [pathname, update]);

  const scrollBy = (direction: -1 | 1) => {
    const el = scroller.current;
    if (el) el.scrollBy({ left: direction * el.clientWidth * 0.7, behavior: "smooth" });
  };

  return (
    <nav aria-label="Categorías" className="relative rounded-b-2xl bg-brand-600">
      <ul
        ref={scroller}
        onScroll={update}
        className="mx-auto flex max-w-6xl snap-x gap-0.5 overflow-x-auto px-2 py-2 [scrollbar-width:none] sm:gap-1 sm:px-4 [&::-webkit-scrollbar]:hidden"
      >
        {categories.map(({ slug, name }) => {
          const href = `/categoria/${slug}`;
          const active = pathname === href;
          return (
            <li key={slug} className="snap-start">
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "block whitespace-nowrap rounded-full px-3 py-1.5 text-base font-bold text-white transition-colors sm:px-4",
                  active ? "bg-white/20 underline decoration-2 underline-offset-4" : "hover:bg-white/10",
                )}
              >
                {name}
              </Link>
            </li>
          );
        })}
      </ul>
      <button
        type="button"
        aria-label="Ver categorías anteriores"
        onClick={() => scrollBy(-1)}
        tabIndex={-1}
        className={cn(ARROW, "left-2", !canScroll.left && "pointer-events-none opacity-0")}
      >
        <ChevronLeft className="size-5" aria-hidden />
      </button>
      <button
        type="button"
        aria-label="Ver más categorías"
        onClick={() => scrollBy(1)}
        tabIndex={-1}
        className={cn(ARROW, "right-2", !canScroll.right && "pointer-events-none opacity-0")}
      >
        <ChevronRight className="size-5" aria-hidden />
      </button>
    </nav>
  );
}
