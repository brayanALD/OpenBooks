"use client";

import { createContext, useContext } from "react";
import type { User } from "@/types/user";

const SessionContext = createContext<User | null>(null);

/** Entrega al cliente el usuario que el servidor ya conoce (la cookie es httpOnly: el cliente no puede leerla). */
export function SessionProvider({ user, children }: { user: User | null; children: React.ReactNode }) {
  return <SessionContext.Provider value={user}>{children}</SessionContext.Provider>;
}

export function useSession(): User | null {
  return useContext(SessionContext);
}
