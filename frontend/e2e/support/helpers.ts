import { expect, type APIRequestContext, type BrowserContext, type Page } from "@playwright/test";

export const API = "http://localhost:8300/api/v1";
export const ADMIN = { email: "admin.e2e@correo.com", password: "clave-admin-1" };
export const PASSWORD = "clave-segura-1";

export const CARD = {
  good: "4242424242424242",
  declined: "4000000000000002",
  noFunds: "4000000000009995",
};

let counter = 0;
/** Un correo distinto por prueba: el backend es el mismo para toda la ejecución. */
export const uniqueEmail = (tag: string) => `${tag}.${Date.now().toString(36)}${counter++}@correo.com`;

/**
 * Abre una página y espera a que cargue y se hidrate. Sin la espera final, un clic muy rápido puede llegar
 * antes de que React active los manejadores y perderse.
 */
export async function open(page: Page, url: string) {
  const response = await page.goto(url, { waitUntil: "load" });
  await page.waitForLoadState("networkidle", { timeout: 4_000 }).catch(() => {}); // el prefetch de Next puede no callar nunca
  await page.waitForTimeout(250);
  return response;
}

/** Crea una cuenta de cliente por la API; la cookie de sesión queda en el contexto del navegador. */
export async function registerCustomer(context: BrowserContext, tag = "cliente", firstName = "Ana") {
  const email = uniqueEmail(tag);
  const res = await context.request.post("/api/auth/register", {
    data: {
      first_name: firstName,
      last_name: "Pérez",
      email,
      phone: "3001234567",
      address: { line: "Calle 10 # 5-20", city: "Bogotá", notes: "Torre 2" },
      password: PASSWORD,
    },
  });
  expect(res.status(), "el registro por API").toBe(201);
  return { email, password: PASSWORD };
}

export async function loginAdmin(context: BrowserContext) {
  const res = await context.request.post("/api/auth/login", { data: ADMIN });
  expect(res.status(), "el inicio de sesión del administrador").toBe(200);
}

export async function getBook(request: APIRequestContext, slug: string) {
  const res = await request.get(`${API}/books/${slug}`);
  expect(res.status(), `GET /books/${slug}`).toBe(200);
  return res.json();
}

/** Compra un libro por la API con la sesión del contexto. Devuelve el pedido (estado `paid` o `failed`). */
export async function buyBook(context: BrowserContext, slug: string, quantity = 1, card = CARD.good) {
  const book = await getBook(context.request, slug);
  const res = await context.request.post("/api/orders", {
    data: {
      items: [{ book_id: book.id, quantity }],
      shipping: { recipient_name: "Ana Pérez", line: "Calle 10 # 5-20", city: "Bogotá" },
      card: { number: card, holder: "ANA PEREZ", exp_month: 12, exp_year: 2035, cvc: "123" },
      idempotency_key: `e2e-${Date.now().toString(36)}-${counter++}-${Math.random().toString(36).slice(2, 8)}`,
      expected_total_cop: book.final_price_cop * quantity + book.shipping_cost_cop,
    },
  });
  expect([200, 201], "el checkout por API").toContain(res.status());
  return res.json();
}

export const toasts = (page: Page) => page.locator("div.pointer-events-none[role=status]");

export async function addToCartFromBook(page: Page, slug: string, quantity = 1) {
  await open(page, `/libro/${slug}`);
  if (quantity > 1) await page.getByLabel("Cantidad").selectOption(String(quantity));
  await page.getByRole("button", { name: "Añadir al carrito" }).click();
  await page.locator("dialog[open]").waitFor();
  await page.keyboard.press("Escape");
  await expect(page.locator("dialog[open]")).toHaveCount(0);
}

export async function fillCard(page: Page, number: string, opts: { expiry?: string; cvc?: string } = {}) {
  await page.getByLabel("Número de tarjeta").fill(number);
  await page.getByLabel("Nombre en la tarjeta").fill("ANA PEREZ");
  await page.getByLabel("Vencimiento").fill(opts.expiry ?? "12/35");
  await page.getByLabel("CVC").fill(opts.cvc ?? "123");
}

/** Etiqueta accesible del botón del carrito: «Carrito» o «Carrito, 3 artículos». */
export const cartLabel = (page: Page) =>
  page
    .locator("header")
    .getByRole("button", { name: /^Carrito/ })
    .or(page.locator("header").getByRole("link", { name: /^Carrito/ }))
    .first();

export async function horizontalOverflow(page: Page) {
  return page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
}
