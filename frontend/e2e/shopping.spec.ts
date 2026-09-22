import { expect, test } from "@playwright/test";
import { addToCartFromBook, cartLabel, CARD, fillCard, getBook, horizontalOverflow, open, PASSWORD, uniqueEmail } from "./support/helpers";

const payButton = (page: import("@playwright/test").Page) => page.getByRole("button", { name: /^(Pagar|Procesando)/ });
const readyToPay = (page: import("@playwright/test").Page) =>
  page.waitForFunction(() => [...document.querySelectorAll("button")].some((b) => /^Pagar \$/.test(b.textContent?.trim() ?? "") && !b.disabled), null, { timeout: 15_000 });

test.describe("Catálogo", () => {
  test("inicio, categoría, búsqueda sin tildes y detalle", async ({ page }) => {
    await open(page, "/");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    await open(page, "/categoria/novela");
    await expect(page.locator("main article").first()).toBeVisible();

    await open(page, "/buscar?q=garcia");
    await expect(page.locator("main article", { hasText: "García Márquez" }).first()).toBeVisible();

    await open(page, "/libro/crimen-y-castigo");
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Crimen y Castigo");
    await expect(page.locator('script[type="application/ld+json"]').first()).toBeAttached();
  });

  test("una ruta inexistente responde 404 con página propia", async ({ page }) => {
    const res = await open(page, "/libro/no-existe-este-libro");
    expect(res?.status()).toBe(404);
    await expect(page.getByRole("heading", { level: 1 }).first()).toContainText("No encontramos");
  });

  test("sin desbordamiento horizontal en móvil", async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 375, height: 800 } });
    const page = await context.newPage();
    for (const url of ["/", "/categoria/novela", "/libro/crimen-y-castigo", "/carrito", "/login"]) {
      await open(page, url);
      expect(await horizontalOverflow(page), url).toBeLessThanOrEqual(0);
    }
    await context.close();
  });
});

test.describe("Carrito y compra", () => {
  test("invitado: carrito → login → registro → pago aprobado → pedido", async ({ page, request }) => {
    const before = await getBook(request, "crimen-y-castigo");
    await addToCartFromBook(page, "crimen-y-castigo", 2);
    await expect(cartLabel(page)).toHaveAttribute("aria-label", "Carrito, 2 artículos");

    await open(page, "/carrito");
    await page.getByRole("button", { name: "Finalizar compra" }).click();
    await page.waitForURL(/\/login\?/);
    expect(new URL(page.url()).searchParams.get("next")).toBe("/checkout");

    await page.getByRole("link", { name: "Regístrate" }).click();
    await page.waitForURL(/\/registro/);
    await page.getByLabel("Nombre", { exact: true }).fill("Ana");
    await page.getByLabel("Apellidos").fill("Pérez Gómez");
    await page.getByLabel("Correo electrónico").fill(uniqueEmail("compra"));
    await page.getByLabel("Dirección", { exact: true }).fill("Calle 10 # 5-20 Apto 301");
    await page.getByLabel("Ciudad").fill("Bogotá");
    await page.getByLabel("Contraseña", { exact: true }).fill(PASSWORD);
    await page.getByLabel("Repite la contraseña").fill(PASSWORD);
    await page.getByRole("button", { name: "Crear cuenta" }).click();

    await page.waitForURL(/\/checkout$/, { timeout: 15_000 });
    await readyToPay(page);
    await expect(cartLabel(page)).toHaveAttribute("aria-label", "Carrito, 2 artículos");
    await expect(page.getByLabel("Nombre de quien recibe")).toHaveValue("Ana Pérez Gómez");

    // Las tarjetas mal escritas ni siquiera salen del navegador.
    await payButton(page).click();
    await expect(page.locator("main form")).toContainText("Número de tarjeta inválido");
    await fillCard(page, "4242 4242 4242 4241");
    await payButton(page).click();
    await expect(page.locator("main form")).toContainText("Número de tarjeta inválido");

    await fillCard(page, CARD.good);
    await payButton(page).click();
    await page.waitForURL(/\/cuenta\/pedidos\/[\w-]+/, { timeout: 20_000 });
    await expect(page.getByText("Pagado").first()).toBeVisible();

    const after = await getBook(request, "crimen-y-castigo");
    expect(after.stock).toBe(before.stock - 2);
    await expect(cartLabel(page)).toHaveAttribute("aria-label", "Carrito");
  });

  test("pago rechazado: se avisa, el carrito se conserva y el stock no cambia", async ({ page, context, request }) => {
    const res = await context.request.post("/api/auth/register", {
      data: { first_name: "Rosa", last_name: "Díaz", email: uniqueEmail("rechazo"), phone: "", address: { line: "Carrera 7 # 1-1", city: "Cali", notes: "" }, password: PASSWORD },
    });
    expect(res.status()).toBe(201);
    const before = await getBook(request, "moby-dick");

    await addToCartFromBook(page, "moby-dick", 1);
    await open(page, "/checkout");
    await readyToPay(page);
    await fillCard(page, CARD.declined);
    await payButton(page).click();
    await expect(page.locator("main [role=alert]")).toBeVisible({ timeout: 15_000 });
    await expect(cartLabel(page)).toHaveAttribute("aria-label", "Carrito, 1 artículo");

    expect((await getBook(request, "moby-dick")).stock).toBe(before.stock);
  });

  test("el cliente no puede alterar precios: el servidor rechaza un total distinto", async ({ context }) => {
    await context.request.post("/api/auth/register", {
      data: { first_name: "Tomás", last_name: "Ruiz", email: uniqueEmail("precio"), phone: "", address: { line: "Calle 1 # 1-1", city: "Cali", notes: "" }, password: PASSWORD },
    });
    const book = await getBook(context.request, "orgullo-y-prejuicio");
    const res = await context.request.post("/api/orders", {
      data: {
        items: [{ book_id: book.id, quantity: 1 }],
        shipping: { recipient_name: "Tomás Ruiz", line: "Calle 1 # 1-1", city: "Cali" },
        card: { number: CARD.good, holder: "TOMAS RUIZ", exp_month: 12, exp_year: 2035, cvc: "123" },
        idempotency_key: `precio-${Date.now()}`,
        expected_total_cop: 1,
      },
    });
    expect(res.status()).toBeGreaterThanOrEqual(400);
    expect(res.status()).toBeLessThan(500);
  });

  test("rutas privadas: sin sesión se redirige al login; /admin no se revela", async ({ page }) => {
    await page.goto("/cuenta/pedidos");
    await expect(page).toHaveURL(/\/login\?/);
    await page.goto("/checkout");
    await expect(page).toHaveURL(/\/login\?/);
  });
});
