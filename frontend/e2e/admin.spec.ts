import { expect, test } from "@playwright/test";
import { buyBook, getBook, loginAdmin, open, registerCustomer } from "./support/helpers";

test.describe("Administración", () => {
  test("un cliente recibe 404 en /admin y no ve el panel en el menú", async ({ page, context }) => {
    await registerCustomer(context, "cliente-admin");
    const res = await page.goto("/admin");
    expect(res?.status()).toBe(404);
    await open(page, "/cuenta");
    await expect(page.getByRole("link", { name: "Panel de administración" })).toHaveCount(0);
  });

  test("sin sesión, /admin lleva al login", async ({ page }) => {
    await page.goto("/admin/libros");
    await expect(page).toHaveURL(/\/login\?/);
  });

  test("crear un libro, verlo en la tienda, editarlo y ocultarlo", async ({ page, context, browser }) => {
    await loginAdmin(context);
    const title = `Libro E2E ${Date.now().toString(36)}`;

    await open(page, "/admin/libros/nuevo");
    await page.getByLabel("Título").fill(title);
    await page.getByLabel("Autor").fill("Autora E2E");
    await page.getByLabel("Novela").check();
    await page.getByLabel("Editorial").fill("Editorial E2E");
    await page.getByLabel("Idioma").fill("Español");
    await page.getByLabel("Páginas").fill("321");
    await page.getByLabel("Descripción").fill("Primer párrafo de prueba.\n\nSegundo párrafo de prueba.");
    await page.getByLabel("Precio de lista (COP)").fill("50000");
    await page.getByLabel("Descuento (%)").fill("10");
    await page.getByLabel("Envío (COP)").fill("5000");
    await page.getByLabel("Stock").fill("4");
    await expect(page.locator("main form")).toContainText("$45.000");
    await page.getByRole("button", { name: "Crear libro" }).click();
    await page.waitForURL(/\/admin\/libros$/, { timeout: 15_000 });

    // Al crear vuelve al listado; se abre la ficha del libro nuevo para editarlo.
    const created = (await (await context.request.get(`/api/admin/books?q=${encodeURIComponent(title)}`)).json()).items[0] as { id: string };
    await open(page, `/admin/libros/${created.id}`);

    // La tienda (visitante anónimo) lo muestra con el precio final y la portada por defecto.
    const shopper = await browser.newContext();
    const shop = await shopper.newPage();
    await open(shop, `/buscar?q=${encodeURIComponent(title)}`);
    const card = shop.locator("main article", { hasText: title });
    await expect(card).toHaveCount(1);
    await expect(card).toContainText("$45.000");

    // Editar: el slug (URL) se mantiene aunque cambie el título.
    const slug = (await (await shopper.request.get(`http://localhost:8300/api/v1/books?q=${encodeURIComponent(title)}`)).json()).items[0].slug as string;
    await page.getByLabel("Título").fill(`${title} (editado)`);
    await page.getByLabel("Stock").fill("3");
    await page.getByRole("button", { name: "Guardar cambios" }).click();
    await expect.poll(async () => (await getBook(shopper.request, slug)).stock).toBe(3);
    await open(shop, `/libro/${slug}`);
    await expect(shop.getByRole("heading", { level: 1 })).toContainText("(editado)");

    // Ocultar (desde el listado, donde termina el guardado): desaparece de la tienda y su URL responde 404.
    await open(page, `/admin/libros?q=${encodeURIComponent(title)}`);
    await page.getByRole("button", { name: `Ocultar ${title} (editado)` }).click();
    await expect.poll(async () => (await shopper.request.get(`http://localhost:8300/api/v1/books/${slug}`)).status()).toBe(404);
    await shopper.close();
  });

  test("pedidos: pagado → enviado → entregado, y cancelar devuelve el stock una sola vez", async ({ page, context, browser }) => {
    const buyer = await browser.newContext();
    await registerCustomer(buyer, "pedido");
    const slug = "orgullo-y-prejuicio";
    const before = await getBook(buyer.request, slug);
    const order = await buyBook(buyer, slug, 2);
    expect((await getBook(buyer.request, slug)).stock).toBe(before.stock - 2);

    await loginAdmin(context);
    await open(page, `/admin/pedidos/${order.id}`);
    await page.getByRole("button", { name: /Marcar como enviado/ }).click();
    await expect(page.getByText("Enviado").first()).toBeVisible();
    await page.getByRole("button", { name: /Marcar como entregado/ }).click();
    await expect(page.getByText("Entregado").first()).toBeVisible();
    await expect(page.getByRole("button", { name: /Cancelar pedido/ })).toHaveCount(0);

    // Un segundo pedido, cancelado: el stock vuelve.
    const second = await buyBook(buyer, slug, 1);
    const mid = await getBook(buyer.request, slug);
    await open(page, `/admin/pedidos/${second.id}`);
    await page.getByRole("button", { name: /Cancelar pedido/ }).click();
    await page.getByRole("button", { name: /^Sí, cancelar/ }).click();
    await expect.poll(async () => (await getBook(buyer.request, slug)).stock).toBe(mid.stock + 1);
    await buyer.close();
  });
});
