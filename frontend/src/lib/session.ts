// Solo para el servidor. La sesión es un JWT del backend guardado en una cookie httpOnly de ESTE origen:
// el JavaScript del navegador no puede leerla, así que un XSS no puede robar la sesión.

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { cache } from "react";
import { backendFetch } from "@/lib/backend";
import { SESSION_COOKIE } from "@/lib/session-cookie";
import type { User } from "@/types/user";

const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7; // el mismo plazo que JWT_EXPIRE_MINUTES del backend

export function sessionCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production", // solo por HTTPS en producción
    path: "/",
    maxAge: SESSION_MAX_AGE_SECONDS,
  };
}

export async function getSessionToken(): Promise<string | undefined> {
  return (await cookies()).get(SESSION_COOKIE)?.value;
}

/** Usuario de la sesión o null. `cache` evita repetir la consulta dentro de una misma petición. */
export const getCurrentUser = cache(async (): Promise<User | null> => {
  const token = await getSessionToken();
  if (!token) return null;
  try {
    const response = await backendFetch("/auth/me", { token });
    return response.ok ? ((await response.json()) as User) : null;
  } catch {
    return null; // API caída: se trata como sin sesión en vez de romper la página
  }
});

/** Para páginas privadas: si no hay sesión válida, redirige al login y vuelve aquí después. */
export async function requireUser(returnTo: string): Promise<User> {
  const user = await getCurrentUser();
  if (!user) redirect(`/login?next=${encodeURIComponent(returnTo)}`);
  return user;
}
