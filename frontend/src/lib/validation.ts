// Validación de los formularios en el navegador. Refleja las reglas del backend (schemas/auth.py), que es
// quien decide de verdad: esto solo da respuesta inmediata al usuario.

export const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
export const PASSWORD_MIN = 8;
export const PASSWORD_MAX = 128;

export type RegisterValues = {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  address_line: string;
  city: string;
  notes: string;
  password: string;
  password_confirm: string;
};

export type Errors = Partial<Record<keyof RegisterValues, string>>;

/** Celular colombiano: 10 dígitos que empiezan por 3 (acepta espacios, guiones y prefijo +57). */
export function normalizePhone(raw: string): string | null {
  const digits = raw.replace(/[\s\-().]/g, "");
  const local = digits.length > 10 ? digits.replace(/^\+?57/, "") : digits;
  return /^3\d{9}$/.test(local) ? local : null;
}

export function validateRegister(values: RegisterValues): Errors {
  const errors: Errors = {};
  const required = (key: keyof RegisterValues, label: string, min = 1) => {
    if (values[key].trim().length < min) errors[key] = min > 1 ? `${label} es demasiado corto.` : `Escribe ${label}.`;
  };

  required("first_name", "tu nombre");
  required("last_name", "tus apellidos");
  required("address_line", "tu dirección", 5);
  required("city", "tu ciudad", 2);

  if (!EMAIL_PATTERN.test(values.email.trim())) errors.email = "Escribe un correo válido.";
  if (values.phone.trim() && !normalizePhone(values.phone)) {
    errors.phone = "El celular debe tener 10 dígitos y empezar por 3.";
  }
  if (values.password.length < PASSWORD_MIN) errors.password = `Mínimo ${PASSWORD_MIN} caracteres.`;
  else if (values.password.length > PASSWORD_MAX) errors.password = `Máximo ${PASSWORD_MAX} caracteres.`;
  if (values.password_confirm !== values.password) errors.password_confirm = "Las contraseñas no coinciden.";

  return errors;
}

/** Nombres de campo del backend (`address.line`) -> nombres del formulario. */
export const SERVER_FIELD_MAP: Record<string, keyof RegisterValues> = {
  first_name: "first_name",
  last_name: "last_name",
  email: "email",
  phone: "phone",
  password: "password",
  "address.line": "address_line",
  "address.city": "city",
  "address.notes": "notes",
};
