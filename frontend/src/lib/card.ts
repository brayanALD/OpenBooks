// Ayudas del formulario de pago (navegador). El backend valida otra vez: esto solo da respuesta inmediata.

export const digitsOnly = (value: string) => value.replace(/\D/g, "");

/** "4242424242424242" -> "4242 4242 4242 4242" */
export function formatCardNumber(value: string): string {
  return digitsOnly(value)
    .slice(0, 19)
    .replace(/(.{4})/g, "$1 ")
    .trim();
}

/** "1228" -> "12/28" */
export function formatExpiry(value: string): string {
  const digits = digitsOnly(value).slice(0, 4);
  return digits.length > 2 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits;
}

export function luhnValid(digits: string): boolean {
  let total = 0;
  for (let i = 0; i < digits.length; i++) {
    let n = Number(digits[digits.length - 1 - i]);
    if (i % 2 === 1) {
      n *= 2;
      if (n > 9) n -= 9;
    }
    total += n;
  }
  return total % 10 === 0;
}

/** "12/28" -> { month: 12, year: 2028 }; null si no es una fecha. */
export function parseExpiry(value: string): { month: number; year: number } | null {
  const match = /^(\d{2})\/(\d{2})$/.exec(value);
  if (!match) return null;
  const month = Number(match[1]);
  return month >= 1 && month <= 12 ? { month, year: 2000 + Number(match[2]) } : null;
}

export type CardValues = { number: string; holder: string; expiry: string; cvc: string };
export type CardErrors = Partial<Record<keyof CardValues, string>>;

export function validateCard(values: CardValues, now = new Date()): CardErrors {
  const errors: CardErrors = {};
  const number = digitsOnly(values.number);
  if (number.length < 13 || number.length > 19 || !luhnValid(number)) errors.number = "Número de tarjeta inválido.";
  if (values.holder.trim().length < 2) errors.holder = "Escribe el nombre que aparece en la tarjeta.";

  const expiry = parseExpiry(values.expiry);
  if (!expiry) errors.expiry = "Usa el formato MM/AA.";
  else if (expiry.year * 12 + expiry.month < now.getFullYear() * 12 + now.getMonth() + 1) errors.expiry = "La tarjeta está vencida.";

  if (!/^\d{3,4}$/.test(values.cvc)) errors.cvc = "3 o 4 dígitos.";
  return errors;
}

/** Tarjetas del modo de prueba (deben coincidir con backend/app/payments/mock_provider.py). */
export const TEST_CARDS = [
  { number: "4242 4242 4242 4242", result: "Aprobada (Visa)" },
  { number: "5555 5555 5555 4444", result: "Aprobada (Mastercard)" },
  { number: "4000 0000 0000 0002", result: "Rechazada por el banco" },
  { number: "4000 0000 0000 9995", result: "Fondos insuficientes" },
  { number: "4000 0000 0000 0069", result: "Tarjeta vencida" },
  { number: "4000 0000 0000 0127", result: "CVC incorrecto" },
] as const;
