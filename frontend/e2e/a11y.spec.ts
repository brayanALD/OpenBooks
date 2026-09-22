import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { buyBook, loginAdmin, open, registerCustomer } from "./support/helpers";

const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"];

async function scan(page: Page, label: string) {
  const { violations } = await new AxeBuilder({ page }).withTags(TAGS).analyze();
  const summary = violations.map((v) => `${v.id} (${v.impact}): ${v.help} → ${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(" | ")}`);
  expect(summary, `Problemas de accesibilidad en ${label}`).toEqual([]);
}

test.describe("Accesibilidad (axe, WCAG 2.1 AA)", () => {
  for (const url of ["/", "/categoria/novela", "/buscar?q=garcia", "/libro/crimen-y-castigo", "/carrito", "/login", "/registro"]) {
    test(`público: ${url}`, async ({ page }) => {
      await open(page, url);
      await scan(page, url);
    });
  }

  test("página 404", async ({ page }) => {
    await open(page, "/libro/no-existe");
    await scan(page, "404");
  });

  test("carrito con artículos (cajón abierto)", async ({ page }) => {
    await open(page, "/libro/crimen-y-castigo");
    await page.getByRole("button", { name: "Añadir al carrito" }).click();
    await page.locator("dialog[open]").waitFor();
    await scan(page, "cajón del carrito");
  });

  test("cliente: cuenta, checkout, pedido y reseñas", async ({ page, context }) => {
    await registerCustomer(context, "a11y");
    const order = await buyBook(context, "orgullo-y-prejuicio");
    await open(page, "/cuenta");
    await scan(page, "/cuenta");
    await open(page, "/cuenta/favoritos"); // vacía
    await scan(page, "/cuenta/favoritos (vacía)");
    await open(page, "/libro/orgullo-y-prejuicio");
    await page.getByRole("button", { name: "Añadir a favoritos" }).click();
    await open(page, "/cuenta/favoritos");
    await scan(page, "/cuenta/favoritos");
    await open(page, "/cuenta/pedidos");
    await scan(page, "/cuenta/pedidos");
    await open(page, `/cuenta/pedidos/${order.id}`);
    await scan(page, "detalle de pedido");
    await open(page, "/libro/orgullo-y-prejuicio"); // con el formulario de reseña visible
    await scan(page, "detalle con formulario de reseña");
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
