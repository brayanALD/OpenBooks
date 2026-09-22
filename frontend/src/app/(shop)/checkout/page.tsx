import type { Metadata } from "next";
import { CheckoutForm } from "@/components/checkout/CheckoutForm";
import { requireUser } from "@/lib/session";

export const metadata: Metadata = { title: "Finalizar compra", robots: { index: false, follow: false } };

export default async function CheckoutPage() {
  // El proxy solo comprobó que hay cookie; aquí se valida de verdad y se obtienen los datos para precargar el envío.
  const user = await requireUser("/checkout");

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-4xl font-bold text-brand-600">Finalizar compra</h1>
      <CheckoutForm user={user} />
    </div>
  );
}
