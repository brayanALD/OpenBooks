"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { CircleAlert, Lock, ShoppingBag } from "lucide-react";
import { CartItemsSummary } from "@/components/checkout/CartItemsSummary";
import { OrderSummary } from "@/components/cart/OrderSummary";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
import { postJson } from "@/lib/auth-client";
import {
  digitsOnly,
  formatCardNumber,
  formatExpiry,
  parseExpiry,
  TEST_CARDS,
  validateCard,
  type CardValues,
} from "@/lib/card";
import { formatCOP } from "@/lib/format";
import { useCartDetails } from "@/lib/use-cart-details";
import { useHydrated } from "@/lib/use-hydrated";
import { normalizePhone } from "@/lib/validation";
import { useCartStore } from "@/store/cart.store";
import { toast } from "@/store/ui.store";
import type { Order } from "@/types/order";
import type { User } from "@/types/user";

type Shipping = { recipient_name: string; phone: string; line: string; city: string; notes: string };

/** Una clave por intento de pago: si la petición se repite, el servidor no cobra dos veces. */
function newAttemptKey(): string {
  const random = globalThis.crypto?.randomUUID?.();
  return random ?? `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}

function validateShipping(s: Shipping): Record<string, string> {
  const errors: Record<string, string> = {};
  if (s.recipient_name.trim().length < 2) errors.recipient_name = "Escribe el nombre de quien recibe.";
  if (s.line.trim().length < 5) errors.line = "Escribe la dirección completa.";
  if (s.city.trim().length < 2) errors.city = "Escribe la ciudad.";
  if (s.phone.trim() && !normalizePhone(s.phone)) errors.phone = "El celular debe tener 10 dígitos y empezar por 3.";
  return errors;
}

/** Nombres de campo del backend -> nombres del formulario. */
const SERVER_FIELDS: Record<string, string> = {
  "shipping.recipient_name": "recipient_name",
  "shipping.phone": "phone",
  "shipping.line": "line",
  "shipping.city": "city",
  "shipping.notes": "notes",
  "card.number": "number",
  "card.holder": "holder",
  "card.exp_month": "expiry",
  "card.exp_year": "expiry",
  "card.cvc": "cvc",
};

export function CheckoutForm({ user }: { user: User }) {
  const router = useRouter();
  const hydrated = useHydrated();
  const { items, empty, data, loading, failed, retry } = useCartDetails(hydrated);
  const clearCart = useCartStore((state) => state.clear);

  // Datos de envío de ESTE pedido: parten de la cuenta, pero se pueden cambiar sin modificarla.
  const [shipping, setShipping] = useState<Shipping>({
    recipient_name: `${user.first_name} ${user.last_name}`,
    phone: user.phone ?? "",
    line: user.address.line,
    city: user.address.city,
    notes: user.address.notes ?? "",
  });
  const [card, setCard] = useState<CardValues>({ number: "", holder: "", expiry: "", cvc: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [paying, setPaying] = useState(false);
  const [attemptKey, setAttemptKey] = useState(newAttemptKey);

  if (!hydrated) return <Skeleton className="h-96 w-full" />;

  if (empty) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center gap-4 rounded-2xl bg-card p-10 text-center shadow-card">
        <ShoppingBag className="size-12 text-brand-400" aria-hidden />
        <p className="font-display text-2xl font-bold">Tu carrito está vacío</p>
        <p className="text-brand-800">Añade algún libro para poder pagar.</p>
        <ButtonLink href="/buscar">Ver el catálogo</ButtonLink>
      </div>
    );
  }

  const lines = data?.lines.filter((line) => items.some((i) => i.bookId === line.book.id)) ?? [];
  const blocked = !data || loading || data.has_issues || data.item_count === 0;

  // El error de un campo se quita al ESCRIBIR en él, no al enfocarlo: la validación lleva el foco al primer
  // campo inválido y no debe borrarle el mensaje justo después de mostrarlo.
  const clearError = (key: string) => setErrors((current) => (current[key] ? { ...current, [key]: "" } : current));
  const editShipping = (key: keyof Shipping, value: string) => {
    setShipping((current) => ({ ...current, [key]: value }));
    clearError(key);
  };
  const editCard = (key: keyof CardValues, value: string) => {
    setCard((current) => ({ ...current, [key]: value }));
    clearError(key);
  };

  const field = (group: "shipping" | "card", key: string) => ({
    name: key,
    error: errors[key],
    value: group === "shipping" ? shipping[key as keyof Shipping] : card[key as keyof CardValues],
  });

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    if (!data || blocked) return;

    const found = { ...validateShipping(shipping), ...validateCard(card) } as Record<string, string>;
    setErrors(found);
    const first = Object.keys(found)[0];
    if (first) {
      (event.currentTarget.elements.namedItem(first) as HTMLElement | null)?.focus();
      return;
    }

    const expiry = parseExpiry(card.expiry)!;
    setPaying(true);
    const result = await postJson<Order>("/api/orders", {
      items: items.map((i) => ({ book_id: i.bookId, quantity: i.quantity })),
      shipping: {
        recipient_name: shipping.recipient_name.trim(),
        phone: shipping.phone.trim() ? normalizePhone(shipping.phone) : null,
        line: shipping.line.trim(),
        city: shipping.city.trim(),
        notes: shipping.notes.trim() || null,
      },
      card: {
        number: digitsOnly(card.number),
        holder: card.holder.trim(),
        exp_month: expiry.month,
        exp_year: expiry.year,
        cvc: card.cvc,
      },
      idempotency_key: attemptKey,
      expected_total_cop: data.total_cop,
    });

    if (!result.ok) {
      setPaying(false);
      if (result.status === 401) return router.push("/login?next=/checkout");
      if (result.code === "total_changed" || result.code === "cart_issues") {
        setFormError(result.message);
        retry(); // vuelve a pedir precios y stock al servidor
        return;
      }
      const mapped: Record<string, string> = {};
      for (const path of Object.keys(result.fields)) if (SERVER_FIELDS[path]) mapped[SERVER_FIELDS[path]] = "Revisa este dato.";
      setErrors(mapped);
      setFormError(Object.keys(mapped).length ? "Revisa los campos marcados." : result.message);
      return;
    }

    const order = result.data;
    if (order.status === "paid") {
      clearCart();
      toast.success(`¡Pedido ${order.number} confirmado!`);
      router.push(`/cuenta/pedidos/${order.id}?nuevo=1`);
      router.refresh();
      return;
    }

    // Pago rechazado: el pedido fallido queda en el historial, el carrito se conserva y el siguiente intento
    // lleva una clave nueva (con la misma, el servidor devolvería este mismo pedido fallido).
    setPaying(false);
    setAttemptKey(newAttemptKey());
    setFormError(`Pago rechazado: ${order.payment.failure_reason ?? "no se pudo procesar."} Tu carrito sigue intacto; prueba con otra tarjeta.`);
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_24rem] lg:items-start">
      <form id="checkout-form" onSubmit={onSubmit} noValidate className="flex flex-col gap-8">
        {formError && (
          <p role="alert" className="flex items-start gap-2 rounded-xl bg-accent px-4 py-3 text-sm font-semibold text-white">
            <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
            {formError}
          </p>
        )}

        <fieldset className="flex flex-col gap-4 rounded-2xl bg-card p-6 shadow-card">
          <legend className="float-left mb-2 font-display text-2xl font-bold text-brand-600">Envío</legend>
          <p className="clear-both text-sm text-brand-800">Precargado con los datos de tu cuenta. Puedes cambiarlos solo para este pedido.</p>
          <Input label="Nombre de quien recibe" autoComplete="name" {...field("shipping", "recipient_name")} onChange={(e) => editShipping("recipient_name", e.target.value)} />
          <Input label="Dirección" autoComplete="street-address" {...field("shipping", "line")} onChange={(e) => editShipping("line", e.target.value)} />
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="Ciudad" autoComplete="address-level2" {...field("shipping", "city")} onChange={(e) => editShipping("city", e.target.value)} />
            <Input label="Celular (opcional)" type="tel" inputMode="tel" autoComplete="tel-national" {...field("shipping", "phone")} onChange={(e) => editShipping("phone", e.target.value)} />
          </div>
          <Input label="Indicaciones (opcional)" {...field("shipping", "notes")} onChange={(e) => editShipping("notes", e.target.value)} />
        </fieldset>

        <fieldset className="flex flex-col gap-4 rounded-2xl bg-card p-6 shadow-card">
          <legend className="float-left mb-2 font-display text-2xl font-bold text-brand-600">Pago</legend>
          <p className="clear-both flex items-center gap-2 rounded-xl bg-brand-100 px-3 py-2 text-sm text-brand-800">
            <Lock className="size-4 shrink-0" aria-hidden />
            Pago simulado: no se cobra nada real y la tarjeta no se guarda.
          </p>
          <Input
            label="Número de tarjeta"
            inputMode="numeric"
            autoComplete="cc-number"
            placeholder="4242 4242 4242 4242"
            {...field("card", "number")}
            onChange={(e) => editCard("number", formatCardNumber(e.target.value))}
          />
          <Input label="Nombre en la tarjeta" autoComplete="cc-name" {...field("card", "holder")} onChange={(e) => editCard("holder", e.target.value)} />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Vencimiento"
              inputMode="numeric"
              autoComplete="cc-exp"
              placeholder="MM/AA"
              maxLength={5}
              {...field("card", "expiry")}
              onChange={(e) => editCard("expiry", formatExpiry(e.target.value))}
            />
            <Input
              label="CVC"
              inputMode="numeric"
              autoComplete="cc-csc"
              maxLength={4}
              {...field("card", "cvc")}
              onChange={(e) => editCard("cvc", digitsOnly(e.target.value))}
            />
          </div>

          <details className="rounded-xl border border-brand-200 p-3 text-sm">
            <summary className="cursor-pointer font-semibold text-brand-800">Tarjetas de prueba</summary>
            <ul className="mt-3 flex flex-col gap-1.5">
              {TEST_CARDS.map((test) => (
                <li key={test.number} className="flex flex-wrap items-center justify-between gap-2">
                  <span>
                    <code className="font-mono">{test.number}</code> <span className="text-brand-800">— {test.result}</span>
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setCard({ number: test.number, holder: card.holder || "ANA PEREZ", expiry: card.expiry || "12/35", cvc: card.cvc || "123" });
                      setErrors((current) => ({ ...current, number: "", holder: "", expiry: "", cvc: "" }));
                    }}
                    className="font-semibold text-accent underline underline-offset-4"
                  >
                    Usar
                  </button>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-brand-800">Cualquier fecha futura y cualquier CVC de 3 dígitos.</p>
          </details>
        </fieldset>

        <Button type="submit" size="lg" loading={paying} disabled={blocked} className="w-full lg:hidden">
          {paying ? "Procesando pago…" : `Pagar ${data ? formatCOP(data.total_cop) : ""}`}
        </Button>
      </form>

      <aside className="flex flex-col gap-4 rounded-2xl bg-card p-6 shadow-card lg:sticky lg:top-4" aria-label="Resumen del pedido">
        <h2 className="text-2xl font-bold">Tu pedido</h2>
        {data ? (
          <>
            <CartItemsSummary lines={lines} quantityOf={(id) => items.find((i) => i.bookId === id)?.quantity ?? 0} />
            {data.has_issues && (
              <p className="rounded-xl bg-brand-100 p-3 text-sm text-brand-800" role="status">
                Algunos libros ya no están disponibles como los pediste.{" "}
                <Link href="/carrito" className="font-semibold text-accent underline underline-offset-4">
                  Revisa tu carrito
                </Link>
                .
              </p>
            )}
            <OrderSummary cart={data} stale={loading} />
          </>
        ) : failed ? (
          <Button variant="outline" size="sm" onClick={retry}>
            No pudimos cargar tu pedido. Reintentar
          </Button>
        ) : (
          <div className="flex flex-col gap-3" role="status" aria-label="Cargando tu pedido">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        )}
        <Button
          type="submit"
          form="checkout-form"
          size="lg"
          loading={paying}
          disabled={blocked}
          className="hidden w-full lg:inline-flex"
        >
          {paying ? "Procesando pago…" : `Pagar ${data ? formatCOP(data.total_cop) : ""}`}
        </Button>
      </aside>
    </div>
  );
}
