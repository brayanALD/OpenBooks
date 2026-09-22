import { expect, test } from "@playwright/test";
import { cartLabel, open } from "./support/helpers";

test.describe("Vista rápida", () => {
  test("abre la descripción, permite elegir cantidad y añadir sin salir de la lista", async ({ page }) => {
    await open(page, "/categoria/clasicos");
    const card = page.locator("main article").first();
    const title = (await card.locator("h3").innerText()).trim();

    await card.getByRole("button", { name: `Vista rápida de ${title}` }).click();
    const dialog = page.locator("dialog[open]");
    await expect(dialog.getByRole("heading", { name: title })).toBeVisible();
    await expect(dialog.getByRole("link", { name: "Ver ficha completa" })).toBeVisible();
    // La descripción llega del servidor.
    await expect(dialog.getByText(/Editorial:|páginas/)).toBeVisible();

    await dialog.getByLabel("Cantidad").selectOption("2");
    await dialog.getByRole("button", { name: "Añadir al carrito" }).click();

    // El modal se cierra, se abre el panel del carrito y seguimos en la misma página.
    await expect(page.getByRole("dialog", { name: title })).toHaveCount(0);
    await expect(page.locator("dialog[open]").getByText(/Carrito|carrito/).first()).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(cartLabel(page)).toHaveAttribute("aria-label", "Carrito, 2 artículos");
    await expect(page).toHaveURL(/\/categoria\/clasicos$/);
  });

  test("Escape cierra la vista rápida y «Ver ficha completa» lleva al libro", async ({ page }) => {
    await open(page, "/");
    const card = page.locator("main article").first();
    await card.getByRole("button", { name: /^Vista rápida de / }).click();
    await expect(page.locator("dialog[open]")).toHaveCount(1);
    await page.keyboard.press("Escape");
    await expect(page.locator("dialog[open]")).toHaveCount(0);

    await card.getByRole("button", { name: /^Vista rápida de / }).click();
    await page.locator("dialog[open]").getByRole("link", { name: "Ver ficha completa" }).click();
    await expect(page).toHaveURL(/\/libro\//);
  });

  test("un invitado que toca favorito desde la vista rápida va al login", async ({ page }) => {
    await open(page, "/categoria/novela");
    await page.locator("main article").first().getByRole("button", { name: /^Vista rápida de / }).click();
    await page.locator("dialog[open]").getByRole("button", { name: "Añadir a favoritos" }).click();
    await expect(page).toHaveURL(/\/login\?/);
  });
});
