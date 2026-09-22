"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { mergeGuestCart, postJson, type SessionResult } from "@/lib/auth-client";
import { EMAIL_PATTERN } from "@/lib/validation";

type LoginFormProps = { next: string };

export function LoginForm({ next }: LoginFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);

    const found: typeof errors = {};
    if (!EMAIL_PATTERN.test(email.trim())) found.email = "Escribe un correo válido.";
    if (!password) found.password = "Escribe tu contraseña.";
    setErrors(found);
    if (Object.keys(found).length > 0) {
      (event.currentTarget.elements.namedItem(found.email ? "email" : "password") as HTMLElement | null)?.focus();
      return;
    }

    setLoading(true);
    const result = await postJson<SessionResult>("/api/auth/login", { email: email.trim(), password });
    if (!result.ok) {
      setLoading(false);
      setFormError(result.message);
      return;
    }

    await mergeGuestCart();
    router.push(next);
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-5">
      {formError && (
        <p role="alert" className="rounded-xl bg-accent px-4 py-3 text-sm font-semibold text-white">
          {formError}
        </p>
      )}
      <Input
        label="Correo electrónico"
        name="email"
        type="email"
        autoComplete="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={errors.email}
      />
      <Input
        label="Contraseña"
        name="password"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={errors.password}
      />
      <Button type="submit" size="lg" loading={loading}>
        Iniciar sesión
      </Button>
      <p className="text-center text-sm text-brand-800">
        ¿No tienes cuenta?{" "}
        <Link
          href={next === "/" ? "/registro" : `/registro?next=${encodeURIComponent(next)}`}
          className="font-semibold text-accent underline underline-offset-4"
        >
          Regístrate
        </Link>
      </p>
    </form>
  );
}
