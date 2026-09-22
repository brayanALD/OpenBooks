"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { PackageCheck, Truck, XCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { requestJson } from "@/lib/auth-client";
import { toast } from "@/store/ui.store";
import { NEXT_STATUSES } from "@/types/admin";

type Target = "shipped" | "delivered" | "cancelled";

const MESSAGES: Record<Target, string> = {
  shipped: "Pedido marcado como enviado.",
  delivered: "Pedido marcado como entregado.",
  cancelled: "Pedido cancelado y stock devuelto al inventario.",
};

type Props = { orderId: string; number: string; status: string; units: number };

export function OrderStatusActions({ orderId, number, status, units }: Props) {
  const router = useRouter();
  const [busy, setBusy] = useState<Target | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const allowed = NEXT_STATUSES[status] ?? [];

  async function change(target: Target) {
    setBusy(target);
    setError(null);
    const result = await requestJson("POST", `/api/admin/orders/${orderId}/status`, { status: target });
    setBusy(null);
    if (!result.ok) {
      setConfirming(false);
      setError(result.message);
      router.refresh(); // el estado pudo cambiar desde otro sitio: se muestra el real
      return;
    }
    setConfirming(false);
    toast.success(MESSAGES[target]);
    router.refresh();
  }

  if (allowed.length === 0) {
    return (
      <p className="text-sm text-brand-800">
        {status === "delivered"
          ? "Pedido entregado: no admite más cambios."
          : status === "cancelled"
            ? "Pedido cancelado: no admite más cambios."
            : "Este pedido no admite cambios de estado."}
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {error && (
        <p role="alert" className="rounded-xl bg-accent px-4 py-3 text-sm font-semibold text-white">
          {error}
        </p>
      )}
      <div className="flex flex-wrap gap-3">
        {allowed.includes("shipped") && (
          <Button onClick={() => change("shipped")} loading={busy === "shipped"} disabled={busy !== null}>
            <Truck className="size-4" aria-hidden />
            Marcar como enviado
          </Button>
        )}
        {allowed.includes("delivered") && (
          <Button onClick={() => change("delivered")} loading={busy === "delivered"} disabled={busy !== null}>
            <PackageCheck className="size-4" aria-hidden />
            Marcar como entregado
          </Button>
        )}
        {allowed.includes("cancelled") && (
          <Button variant="outline" onClick={() => setConfirming(true)} disabled={busy !== null}>
            <XCircle className="size-4" aria-hidden />
            Cancelar pedido
          </Button>
        )}
      </div>

      <Modal open={confirming} onClose={() => setConfirming(false)} title={`¿Cancelar el pedido ${number}?`}>
        <p className="text-brand-800">
          Se devolverán {units} {units === 1 ? "unidad" : "unidades"} al inventario. Después no se podrá enviar ni volver a
          activar. El pago es simulado, así que no se calcula ningún reembolso.
        </p>
        <div className="mt-6 flex flex-wrap justify-end gap-3">
          <Button variant="ghost" onClick={() => setConfirming(false)} disabled={busy !== null}>
            No, volver
          </Button>
          <Button onClick={() => change("cancelled")} loading={busy === "cancelled"}>
            Sí, cancelar pedido
          </Button>
        </div>
      </Modal>
    </div>
  );
}
