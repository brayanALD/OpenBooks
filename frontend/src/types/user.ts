// Espejo de backend/app/schemas/auth.py (UserOut). Nunca incluye la contraseña.

export type Address = { line: string; city: string; notes: string | null };

export type User = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  address: Address;
  role: "customer" | "admin";
};
