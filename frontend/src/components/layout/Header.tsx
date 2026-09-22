import Link from "next/link";
import { Heart, Settings, User } from "lucide-react";
import { CartButton } from "@/components/cart/CartButton";
import { getCurrentUser } from "@/lib/session";
import { Logo } from "./Logo";
import { SearchBar } from "./SearchBar";
import { headerActionStyles as actionStyles } from "./styles";
import { ThemeToggle } from "./ThemeToggle";

export async function Header() {
  const user = await getCurrentUser();

  return (
    // Texto oscuro sobre el marrón claro original: el blanco no llega a contraste AA (3,7:1).
    <header className="bg-brand-400 text-brand-900">
      {/* Tres columnas solo desde lg: a 768 px logo + buscador + acciones no caben en una fila. */}
      <div className="mx-auto grid max-w-6xl grid-cols-[1fr_auto] items-center gap-x-4 gap-y-3 px-4 py-3 lg:grid-cols-[auto_1fr_auto] lg:gap-x-8 lg:py-4">
        <Logo className="col-start-1 row-start-1" />

        <SearchBar className="col-span-2 row-start-2 lg:col-span-1 lg:col-start-2 lg:row-start-1 lg:mx-auto lg:w-full lg:max-w-xl" />

        <nav aria-label="Cuenta y carrito" className="col-start-2 row-start-1 flex items-center gap-1 lg:col-start-3">
          <ThemeToggle />
          <CartButton />
          {user && (
            <Link href="/cuenta/favoritos" className={actionStyles} aria-label="Mis favoritos">
              <Heart className="size-6" aria-hidden />
              <span className="hidden lg:inline">Favoritos</span>
            </Link>
          )}
          {user?.role === "admin" && (
            <Link href="/admin" className={actionStyles} aria-label="Panel de administración">
              <Settings className="size-6" aria-hidden />
              <span className="hidden lg:inline">Panel</span>
            </Link>
          )}
          {user ? (
            <Link href="/cuenta" className={actionStyles} aria-label={`Mi cuenta, ${user.first_name}`}>
              <User className="size-6" aria-hidden />
              <span className="hidden max-w-28 truncate sm:inline" aria-hidden>
                {user.first_name}
              </span>
            </Link>
          ) : (
            <Link href="/login" className={actionStyles}>
              <User className="size-6" aria-hidden />
              <span className="hidden sm:inline">Ingresar</span>
              <span className="sr-only sm:hidden">Ingresar</span>
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
