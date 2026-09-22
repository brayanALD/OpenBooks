import type { Metadata } from "next";
import { CartContents } from "@/components/cart/CartContents";

export const metadata: Metadata = {
  title: "Carrito",
  robots: { index: false, follow: false },
};

export default function CartPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-4xl font-bold text-brand-600">Tu carrito</h1>
      <CartContents layout="page" />
    </div>
  );
}
