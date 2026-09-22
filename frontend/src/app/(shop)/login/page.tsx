import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { Info } from "lucide-react";
import { LoginForm } from "@/components/auth/LoginForm";
import { safeNext } from "@/lib/safe-next";
import { getCurrentUser } from "@/lib/session";

export const metadata: Metadata = { title: "Iniciar sesión", robots: { index: false, follow: false } };

type Props = { searchParams: Promise<{ next?: string | string[]; reason?: string | string[] }> };

export default async function LoginPage({ searchParams }: Props) {
  const params = await searchParams;
  const next = safeNext(params.next);
  if (await getCurrentUser()) redirect(next === "/" ? "/cuenta" : next);

  return (
    <div className="mx-auto flex max-w-md flex-col gap-6">
      <h1 className="text-4xl font-bold text-brand-600">Iniciar sesión</h1>
      {params.reason === "checkout" && (
        <p className="flex items-start gap-2 rounded-xl bg-brand-100 p-3 text-sm text-brand-800" role="status">
          <Info className="mt-0.5 size-4 shrink-0" aria-hidden />
          Inicia sesión para finalizar tu compra. Tu carrito se conserva.
        </p>
      )}
      {params.reason === "favoritos" && (
        <p className="flex items-start gap-2 rounded-xl bg-brand-100 p-3 text-sm text-brand-800" role="status">
          <Info className="mt-0.5 size-4 shrink-0" aria-hidden />
          Inicia sesión para guardar libros en tus favoritos.
        </p>
      )}
      <div className="rounded-2xl bg-card p-6 shadow-card sm:p-8">
        <LoginForm next={next} />
      </div>
    </div>
  );
}
