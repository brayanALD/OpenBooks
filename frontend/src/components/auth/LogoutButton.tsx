"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useCartStore } from "@/store/cart.store";
import { toast } from "@/store/ui.store";

export function LogoutButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function logout() {
    setLoading(true);
    // Primero se borra la cookie: así, si la sincronización del carrito intenta guardar el carrito vacío,
    // el servidor lo rechaza (401) y el carrito de la cuenta se conserva intacto.
    await fetch("/api/auth/logout", { method: "POST" });
    // En un equipo compartido no debe quedar el carrito de esta persona en el navegador.
    useCartStore.getState().clear();
    router.push("/");
    router.refresh();
    toast.info("Sesión cerrada.");
  }

  return (
    <Button variant="outline" loading={loading} onClick={logout}>
      <LogOut className="size-4" aria-hidden />
      Cerrar sesión
    </Button>
  );
}
