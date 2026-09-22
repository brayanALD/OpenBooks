"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { mergeGuestCart, postJson, type SessionResult } from "@/lib/auth-client";
import {
  normalizePhone,
  SERVER_FIELD_MAP,
  validateRegister,
  type Errors,
  type RegisterValues,
} from "@/lib/validation";

const EMPTY: RegisterValues = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  address_line: "",
  city: "",
  notes: "",
  password: "",
  password_confirm: "",
};

export function RegisterForm({ next }: { next: string }) {
  const router = useRouter();
  const [values, setValues] = useState<RegisterValues>(EMPTY);
  const [errors, setErrors] = useState<Errors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const field = (key: keyof RegisterValues) => ({
    name: key,
    value: values[key],
    error: errors[key],
    onChange: (event: React.ChangeEvent<HTMLInputElement>) => {
      setValues((current) => ({ ...current, [key]: event.target.value }));
      if (errors[key]) setErrors((current) => ({ ...current, [key]: undefined }));
    },
  });

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);

    const found = validateRegister(values);
    setErrors(found);
    const firstInvalid = Object.keys(found)[0];
    if (firstInvalid) {
      (event.currentTarget.elements.namedItem(firstInvalid) as HTMLElement | null)?.focus();
      return;
    }

    setLoading(true);
    const result = await postJson<SessionResult>("/api/auth/register", {
      first_name: values.first_name.trim(),
      last_name: values.last_name.trim(),
      email: values.email.trim(),
      phone: values.phone.trim() ? normalizePhone(values.phone) : null,
      address: { line: values.address_line.trim(), city: values.city.trim(), notes: values.notes.trim() || null },
      password: values.password,
    });

    if (!result.ok) {
      setLoading(false);
      if (result.status === 409) {
        setErrors({ email: result.message });
      } else {
        const mapped: Errors = {};
        for (const [path, message] of Object.entries(result.fields)) {
          const key = SERVER_FIELD_MAP[path];
          if (key) mapped[key] = message;
        }
        setErrors(mapped);
        setFormError(Object.keys(mapped).length > 0 ? "Revisa los campos marcados." : result.message);
      }
      return;
    }

    await mergeGuestCart();
    router.push(next);
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-8">
      {formError && (
        <p role="alert" className="rounded-xl bg-accent px-4 py-3 text-sm font-semibold text-white">
          {formError}
        </p>
      )}

      <fieldset className="flex flex-col gap-4">
        <legend className="mb-2 font-display text-xl font-bold text-brand-600">Tus datos</legend>
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Nombre" autoComplete="given-name" {...field("first_name")} />
          <Input label="Apellidos" autoComplete="family-name" {...field("last_name")} />
        </div>
        <Input label="Correo electrónico" type="email" autoComplete="email" {...field("email")} />
        <Input
          label="Celular (opcional)"
          type="tel"
          inputMode="tel"
          autoComplete="tel-national"
          hint="Ejemplo: 300 123 4567"
          {...field("phone")}
        />
      </fieldset>

      <fieldset className="flex flex-col gap-4">
        <legend className="mb-2 font-display text-xl font-bold text-brand-600">Dirección de envío</legend>
        <Input label="Dirección" autoComplete="street-address" hint="Calle, número, apartamento…" {...field("address_line")} />
        <Input label="Ciudad" autoComplete="address-level2" {...field("city")} />
        <Input label="Indicaciones (opcional)" hint="Torre, portería, referencias…" {...field("notes")} />
      </fieldset>

      <fieldset className="flex flex-col gap-4">
        <legend className="mb-2 font-display text-xl font-bold text-brand-600">Contraseña</legend>
        <Input label="Contraseña" type="password" autoComplete="new-password" hint="Mínimo 8 caracteres." {...field("password")} />
        <Input label="Repite la contraseña" type="password" autoComplete="new-password" {...field("password_confirm")} />
      </fieldset>

      <Button type="submit" size="lg" loading={loading}>
        Crear cuenta
      </Button>
      <p className="text-center text-sm text-brand-800">
        ¿Ya tienes cuenta?{" "}
        <Link
          href={next === "/" ? "/login" : `/login?next=${encodeURIComponent(next)}`}
          className="font-semibold text-accent underline underline-offset-4"
        >
          Inicia sesión
        </Link>
      </p>
    </form>
  );
}
