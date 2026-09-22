import Link from "next/link";
import { cn } from "@/lib/cn";
import { SITE } from "@/lib/site";

/** Marca vectorial: libro inclinado, en la línea del logo original (legacy/imagenes/LogoBueno.png). */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 40" fill="none" aria-hidden className={cn("size-10", className)}>
      <g transform="rotate(-14 20 20)">
        <path
          d="M9 6.5A2.5 2.5 0 0 1 11.5 4H31v27H11.5A2.5 2.5 0 0 0 9 33.5V6.5Z"
          fill="currentColor"
        />
        <path
          d="M9 33.5A2.5 2.5 0 0 1 11.5 31H31v5H11.5A2.5 2.5 0 0 1 9 33.5Z"
          fill="currentColor"
          fillOpacity=".55"
        />
        <rect x="14" y="10" width="11" height="2.2" rx="1.1" fill="#faf5ee" />
        <rect x="14" y="15" width="7" height="2.2" rx="1.1" fill="#faf5ee" />
      </g>
    </svg>
  );
}

export function Logo({ className }: { className?: string }) {
  return (
    <Link
      href="/"
      aria-label={`${SITE.name}, ir al inicio`}
      // Color de marca fijo (el mismo en claro y oscuro): no usa `text-brand-900`, que el modo oscuro
      // reasigna a un tono claro para el resto del texto.
      className={cn("inline-flex items-center gap-2.5 text-[#2e1708]", className)}
    >
      <LogoMark />
      <span className="whitespace-nowrap font-display text-2xl font-bold leading-none tracking-tight">
        Open <span className="font-semibold">Books</span>
      </span>
    </Link>
  );
}
