import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { buyBook, loginAdmin, open, registerCustomer } from "./support/helpers";

const theme = (page: Page) => page.evaluate(() => document.documentElement.dataset.theme);

test.describe("Modo oscuro", () => {
  test("sigue la preferencia del sistema cuando no hay elección guardada", async ({ browser }) => {
    for (const scheme of ["dark", "light"] as const) {
      const context = await browser.newContext({ colorScheme: scheme });
      const page = await context.newPage();
      await open(page, "/");
      expect(await theme(page)).toBe(scheme);
      await context.close();
    }
  });

  test("el botón cambia el tema y la elección se recuerda al recargar (sin parpadeo)", async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: "light" });
    const page = await context.newPage();
    await open(page, "/");
    expect(await theme(page)).toBe("light");

    const toggle = page.locator("header").getByRole("button", { name: "Modo oscuro" });
    await expect(toggle).toHaveAttribute("aria-pressed", "false");
    await toggle.click();
    expect(await theme(page)).toBe("dark");
    await expect(toggle).toHaveAttribute("aria-pressed", "true");
    // El fondo cambia de verdad (no solo el atributo).
    const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    expect(bg).toBe("rgb(23, 16, 10)");

    await page.reload();
    expect(await theme(page)).toBe("dark"); // el script del <head> lo pone antes de pintar
    await page.locator("header").getByRole("button", { name: "Modo oscuro" }).click();
    await page.reload();
    expect(await theme(page)).toBe("light");
    await context.close();
  });
});

test.describe("Accesibilidad en modo oscuro (contraste WCAG AA)", () => {
  test.use({ colorScheme: "dark" });

  async function scan(page: Page, label: string) {
    expect(await theme(page), `tema en ${label}`).toBe("dark");
    const { violations } = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"]).analyze();
    const summary = violations.map((v) => `${v.id}: ${v.help} → ${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(" | ")}`);
    expect(summary, `Problemas en ${label}`).toEqual([]);
  }

  for (const url of ["/", "/categoria/novela", "/libro/1984", "/carrito", "/login", "/registro"]) {
    test(`público: ${url}`, async ({ page }) => {
      await open(page, url);
      await scan(page, url);
    });
  }

  test("vista rápida abierta", async ({ page }) => {
    await open(page, "/categoria/clasicos");
    await page.locator("main article").first().getByRole("button", { name: /^Vista rápida de / }).click();
    await expect(page.locator("dialog[open]").getByRole("button", { name: "Añadir al carrito" })).toBeVisible();
    await scan(page, "vista rápida");
  });

  test("cliente: cuenta, favoritos, pedido y checkout", async ({ page, context }) => {
    await registerCustomer(context, "oscuro");
    const order = await buyBook(context, "orgullo-y-prejuicio");
    for (const url of ["/cuenta", "/cuenta/favoritos", "/cuenta/pedidos", `/cuenta/pedidos/${order.id}`]) {
      await open(page, url);
      await scan(page, url);
    }
    await open(page, "/libro/moby-dick");
    await page.getByRole("button", { name: "Añadir al carrito" }).click();
    await page.keyboard.press("Escape");
    await open(page, "/checkout");
    await scan(page, "/checkout");
  });

  test("administración", async ({ page, context }) => {
    await loginAdmin(context);
    for (const url of ["/admin", "/admin/libros", "/admin/libros/nuevo", "/admin/pedidos"]) {
      await open(page, url);
      await scan(page, url);
    }
  });
});
