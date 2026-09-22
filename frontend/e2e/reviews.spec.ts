import { expect, test } from "@playwright/test";
import { buyBook, getBook, loginAdmin, open, registerCustomer, toasts, API } from "./support/helpers";

const SLUG = "moby-dick";
const COMMENT = "Una travesía enorme: la prosa te arrastra desde la primera página.";

test.describe("Reseñas verificadas", () => {
  test("un invitado ve las reseñas de muestra y la invitación a iniciar sesión", async ({ page }) => {
    await open(page, `/libro/${SLUG}`);
    await expect(page.getByRole("heading", { name: "¿Lo has leído?" })).toBeVisible();
    await expect(page.getByRole("link", { name: /Inicia sesión/ })).toBeVisible();
    await expect(page.getByText("de muestra", { exact: false }).first()).toBeVisible();
    await expect(page.locator("li", { hasText: "Compra verificada" })).toHaveCount(0); // ninguna reseña de muestra lleva la insignia
  });

  test("quien no compró el libro no puede reseñarlo (ni forzando la API)", async ({ page, context }) => {
    await registerCustomer(context, "sincompra");
    await open(page, `/libro/${SLUG}`);
    await expect(page.getByText("Solo pueden reseñar quienes compraron este libro")).toBeVisible();
    await expect(page.getByRole("button", { name: "Publicar reseña" })).toHaveCount(0);

    const forced = await context.request.post(`/api/books/${SLUG}/reviews`, { data: { rating: 5, comment: COMMENT } });
    expect(forced.status()).toBe(403);
  });

  test("comprar → reseñar → editar → eliminar, con la nota del libro al día", async ({ page, context }) => {
    await registerCustomer(context, "lector", "Lucía");
    const before = await getBook(context.request, SLUG);
    const order = await buyBook(context, SLUG);
    expect(order.status).toBe("paid");

    await open(page, `/libro/${SLUG}`);
    await expect(page.getByRole("heading", { name: "Deja tu reseña" })).toBeVisible();

    // Validación en el navegador: sin nota ni texto no se envía nada.
    await page.getByRole("button", { name: "Publicar reseña" }).click();
    await expect(page.getByText(/Elige una valoración|valoración/i).first()).toBeVisible();

    await page.getByRole("radio", { name: "5 estrellas" }).check({ force: true });
    await page.getByLabel("Tu reseña").fill(COMMENT);
    await page.getByRole("button", { name: "Publicar reseña" }).click();
    await expect(toasts(page).getByText("¡Gracias por tu reseña!")).toBeVisible();

    // Aparece como «Tu reseña» y ya no se ofrece escribir otra.
    await expect(page.getByRole("heading", { name: "Tu reseña" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Deja tu reseña" })).toHaveCount(0);
    await expect(page.getByText(COMMENT)).toHaveCount(1); // no duplicada en la lista pública
    await expect(page.getByText("Compra verificada").first()).toBeVisible();

    const afterCreate = await getBook(context.request, SLUG);
    expect(afterCreate.rating_count).toBe(before.rating_count + 1);

    // Segunda reseña del mismo libro: el servidor la rechaza.
    const dup = await context.request.post(`/api/books/${SLUG}/reviews`, { data: { rating: 1, comment: "Intento de duplicado del mismo libro." } });
    expect(dup.status()).toBe(409);

    // Editar.
    await page.getByRole("button", { name: "Editar" }).click();
    await page.getByRole("radio", { name: "1 estrella", exact: true }).check({ force: true });
    await page.getByLabel("Tu reseña").fill("Cambié de opinión tras releerlo: demasiado denso para mí.");
    await page.getByRole("button", { name: "Guardar cambios" }).click();
    await expect(toasts(page).getByText("Reseña actualizada.")).toBeVisible();
    await expect(page.getByText("· editada")).toBeVisible();
    await expect(page.getByText("demasiado denso para mí")).toBeVisible();

    // Eliminar con confirmación.
    await page.getByRole("button", { name: "Eliminar" }).click();
    await page.getByRole("button", { name: "Sí, eliminar" }).click();
    await expect(toasts(page).getByText("Reseña eliminada.")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Deja tu reseña" })).toBeVisible();

    const afterDelete = await getBook(context.request, SLUG);
    expect(afterDelete.rating_count).toBe(before.rating_count);
    expect(afterDelete.rating_avg).toBeCloseTo(before.rating_avg, 5);
  });

  test("un pedido con pago rechazado no da derecho a reseñar", async ({ context }) => {
    await registerCustomer(context, "rechazado");
    const failed = await buyBook(context, "steve-jobs", 1, "4000000000000002");
    expect(failed.status).toBe("failed");
    const status = await context.request.get(`/api/books/steve-jobs/reviews/mine`).catch(() => null);
    // El estado se consulta desde el servidor de Next; aquí basta con comprobar que publicar sigue prohibido.
    void status;
    const forced = await context.request.post(`/api/books/steve-jobs/reviews`, { data: { rating: 4, comment: "No debería poder reseñar esto." } });
    expect(forced.status()).toBe(403);
  });

  test("el administrador puede eliminar cualquier reseña, incluidas las de muestra", async ({ page, context }) => {
    await loginAdmin(context);
    const book = await getBook(context.request, "1984");
    const list = await context.request.get(`/api/admin/books/${book.id}/reviews`);
    expect(list.status()).toBe(200);
    const reviews = (await list.json()) as { id: string }[];
    expect(reviews.length).toBeGreaterThan(0);

    await open(page, `/admin/libros/${book.id}`);
    const section = page.locator("section[aria-labelledby=moderacion]");
    await expect(section.getByText("De muestra").first()).toBeVisible();
    const rows = section.locator("li");
    const count = await rows.count();
    await rows.first().getByRole("button", { name: /^Eliminar la reseña/ }).click();
    await page.getByRole("button", { name: "Sí, eliminar" }).click();
    await expect(toasts(page).getByText("Reseña eliminada.")).toBeVisible();
    await expect(rows).toHaveCount(count - 1);

    const after = await (await context.request.get(`${API}/books/1984`)).json();
    expect(after.rating_count).toBe(book.rating_count - 1);
  });

  test("un cliente no puede usar los endpoints de moderación", async ({ context }) => {
    await registerCustomer(context, "intruso");
    const res = await context.request.delete("/api/admin/reviews/rv_001", { headers: { origin: "http://localhost:3300" } });
    expect([401, 403, 404]).toContain(res.status());
  });
});
