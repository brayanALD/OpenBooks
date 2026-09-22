import { expect, test } from "@playwright/test";
import { open, registerCustomer, toasts } from "./support/helpers";

test.describe("Favoritos", () => {
  test("un invitado que toca el corazón va al login y vuelve a la misma página", async ({ page }) => {
    await open(page, "/categoria/novela");
    await page.getByRole("button", { name: /^Añadir .* a favoritos$/ }).first().click();
    await expect(page).toHaveURL(/\/login\?next=%2Fcategoria%2Fnovela&reason=favoritos/);
    await expect(page.getByText("Inicia sesión para guardar libros en tus favoritos")).toBeVisible();
  });

  test("añadir desde la tarjeta y desde la ficha, verlos en la lista y quitarlos", async ({ page, context }) => {
    await registerCustomer(context, "fav");

    // Desde la tarjeta (categoría).
    await open(page, "/categoria/novela");
    const card = page.locator("main article").first();
    const title = (await card.locator("h3").innerText()).trim();
    await card.getByRole("button", { name: /a favoritos$/ }).click();
    await expect(toasts(page).getByText("Añadido a tus favoritos.")).toBeVisible();
    await expect(card.getByRole("button", { name: `Quitar ${title} de favoritos` })).toHaveAttribute("aria-pressed", "true");

    // Desde la ficha de otro libro.
    await open(page, "/libro/moby-dick");
    await page.getByRole("button", { name: "Añadir a favoritos" }).click();
    await expect(page.getByRole("button", { name: "En tus favoritos" })).toBeVisible();

    // El corazón sigue lleno tras recargar (viene de la cuenta, no del navegador).
    await open(page, "/libro/moby-dick");
    await expect(page.getByRole("button", { name: "En tus favoritos" })).toBeVisible();

    // La lista: el más reciente primero.
    await open(page, "/cuenta/favoritos");
    const items = page.locator("main article");
    await expect(items).toHaveCount(2);
    await expect(items.first()).toContainText("Moby Dick");
    await expect(items.nth(1)).toContainText(title);

    // Quitar desde la lista: el libro desaparece.
    await items.first().getByRole("button", { name: /Quitar .* de favoritos/ }).click();
    await expect(items).toHaveCount(1);
    await expect(items.first()).toContainText(title);
  });

  test("un libro inexistente no se puede guardar y otra cuenta no ve mis favoritos", async ({ page, context, browser }) => {
    await registerCustomer(context, "fav-a");
    const missing = await context.request.put("/api/wishlist/no-existe", { headers: { origin: "http://localhost:3300" } });
    expect(missing.status()).toBe(404);

    await open(page, "/libro/1984");
    await page.getByRole("button", { name: "Añadir a favoritos" }).click();
    await expect(page.getByRole("button", { name: "En tus favoritos" })).toBeVisible();

    const other = await browser.newContext();
    await registerCustomer(other, "fav-b");
    const ids = await (await other.request.get("/api/wishlist/ids")).json();
    expect(ids.book_ids).toEqual([]);
    await other.close();
  });

  test("sin sesión, la lista de favoritos lleva al login", async ({ page }) => {
    await page.goto("/cuenta/favoritos");
    await expect(page).toHaveURL(/\/login\?/);
  });
});
