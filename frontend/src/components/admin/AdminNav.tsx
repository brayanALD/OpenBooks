"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, LayoutDashboard, Package } from "lucide-react";
import { cn } from "@/lib/cn";

const ITEMS = [
  { href: "/admin", label: "Resumen", Icon: LayoutDashboard, exact: true },
  { href: "/admin/libros", label: "Libros", Icon: BookOpen, exact: false },
  { href: "/admin/pedidos", label: "Pedidos", Icon: Package, exact: false },
] as const;

export function AdminNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Administración">
      <ul className="flex gap-1 overflow-x-auto md:flex-col">
        {ITEMS.map(({ href, label, Icon, exact }) => {
          const active = exact ? pathname === href : pathname.startsWith(href);
          return (
            <li key={href}>
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-2.5 whitespace-nowrap rounded-xl px-4 py-2.5 font-semibold transition-colors",
                  active ? "bg-brand-600 text-white" : "text-brand-800 hover:bg-brand-100",
                )}
              >
                <Icon className="size-5" aria-hidden />
                {label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
