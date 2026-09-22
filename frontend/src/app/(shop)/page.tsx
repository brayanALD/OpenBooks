import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { BookCard } from "@/components/catalog/BookCard";
import { BookGrid } from "@/components/catalog/BookGrid";
import { ButtonLink } from "@/components/ui/Button";
import { getBooks, getCategories } from "@/lib/api-client";
import { getRecommendedBooks } from "@/lib/recommendations";

export default async function HomePage() {
  // Las cuatro consultas son independientes: se lanzan a la vez.
  const [recommended, bestsellers, onSale, categories] = await Promise.all([
    // Sin sesión, o con sesión pero sin compras pagadas: genéricos (destacados/más vendidos).
    // Con compras pagadas: afines a ellas. El backend decide el modo (ver /books/recommended).
    getRecommendedBooks(4),
    getBooks({ bestseller: true, page_size: 5 }),
    getBooks({ on_sale: true, sort: "price_asc", page_size: 5 }),
    getCategories(),
  ]);

  return (
    <div className="flex flex-col gap-14">
      <section className="rounded-3xl bg-brand-600 px-6 py-12 text-center text-white shadow-card sm:px-12 sm:py-16">
        <h1 className="mx-auto max-w-2xl text-balance text-4xl font-bold leading-tight sm:text-5xl">
          Tu próxima lectura empieza aquí
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-lg text-brand-100">
          Clásicos, fantasía, biografías e historia. Libros en descuento y con envío gratuito.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <ButtonLink href="/categoria/clasicos" size="lg" variant="light">
            Explorar clásicos
          </ButtonLink>
          <ButtonLink href="/buscar" size="lg" variant="primary">
            Ver todo el catálogo
          </ButtonLink>
        </div>
      </section>

      <section aria-labelledby="recomendados">
        <h2 id="recomendados" className="mb-6 text-3xl font-bold text-brand-600">
          Productos recomendados
        </h2>
        <ul className="grid gap-4 lg:grid-cols-2">
          {recommended.map((book, i) => (
            <li key={book.id}>
              <BookCard book={book} variant="horizontal" priority={i < 2} />
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="mas-vendidos">
        <div className="mb-6 flex items-end justify-between gap-4">
          <h2 id="mas-vendidos" className="text-3xl font-bold text-brand-600">
            Más vendidos
          </h2>
        </div>
        <BookGrid books={bestsellers.items} />
      </section>

      <section aria-labelledby="descuentos">
        <h2 id="descuentos" className="mb-1 text-3xl font-bold text-brand-600">
          Libros en descuento
        </h2>
        <p className="mb-6 text-brand-800">Con envío gratuito.</p>
        <BookGrid books={onSale.items} />
      </section>

      <section aria-labelledby="categorias">
        <h2 id="categorias" className="mb-6 text-3xl font-bold text-brand-600">
          Explora por categoría
        </h2>
        <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {categories.map(({ slug, name, book_count }) => (
            <li key={slug}>
              <Link
                href={`/categoria/${slug}`}
                className="group flex items-center justify-between rounded-2xl bg-card p-6 shadow-card transition duration-200 hover:-translate-y-1 hover:shadow-card-hover"
              >
                <span>
                  <span className="block font-display text-xl font-bold">{name}</span>
                  <span className="text-sm text-brand-800">
                    {book_count} {book_count === 1 ? "libro" : "libros"}
                  </span>
                </span>
                <ArrowRight
                  className="size-5 text-accent transition-transform group-hover:translate-x-1"
                  aria-hidden
                />
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
