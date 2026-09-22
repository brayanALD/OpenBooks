"use client";

import { useSyncExternalStore } from "react";
import { Moon, Sun } from "lucide-react";
import { headerActionStyles } from "./styles";

export const THEME_KEY = "openbooks-theme";

type Theme = "light" | "dark";

const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

// El atributo lo pone el script de layout.tsx antes de pintar; aquí solo se lee.
const read = (): Theme => (document.documentElement.dataset.theme === "dark" ? "dark" : "light");
const readServer = (): Theme => "light";

/** Cambia entre modo claro y oscuro. Guarda la elección; sin elección se sigue la preferencia del sistema. */
export function ThemeToggle() {
  const theme = useSyncExternalStore(subscribe, read, readServer);

  function toggle() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      /* modo privado o almacenamiento bloqueado: el cambio vale solo para esta visita */
    }
    listeners.forEach((listener) => listener());
  }

  const dark = theme === "dark";
  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={dark}
      aria-label="Modo oscuro"
      title={dark ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      className={headerActionStyles}
    >
      {dark ? <Sun className="size-6" aria-hidden /> : <Moon className="size-6" aria-hidden />}
    </button>
  );
}
