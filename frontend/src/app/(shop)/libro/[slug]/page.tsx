import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ChevronRight, Info } from "lucide-react";
import { PriceTag } from "@/components/book/PriceTag";
import { PurchaseBox } from "@/components/book/PurchaseBox";
import { FavoriteButton } from "@/components/catalog/FavoriteButton";
import { ReviewComposer } from "@/components/book/ReviewComposer";
import { ReviewList } from "@/components/book/ReviewList";
import { ShippingBadge } from "@/components/book/ShippingBadge";
import { StarRating } from "@/components/book/StarRating";
import { BookCard } from "@/components/catalog/BookCard";
import { Badge } from "@/components/ui/Badge";
import { getBook, getRelatedBooks, getReviews } from "@/lib/api-client";
import { getMyReviewStatus } from "@/lib/reviews";
import { bookJsonLd, serializeJsonLd } from "@/lib/seo";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const book = await getBook(slug);
  if (!book) return { title: "Libro no encontrado" };

  const summary = book.description.replace(/\s+/g, " ").slice(0, 155).trim();
  const description = summary
    ? `${summary}${book.description.length > 155 ? "…" : ""}`
    : `${book.title}, de ${book.author.name}. Cómpralo en Open Books.`;
  return {
    title: `${book.title} — ${book.author.name}`,
    description,
    alternates: { canonical: `/libro/${slug}` },
    openGraph: { title: book.title, description, type: "website", images: [{ url: book.cover }] },
  };
}

export default async function BookPage({ params }: Props) {
  const { slug } = await params;
  const book = await getBook(slug);
  if (!book) notFound();

  const [related, reviews, mine] = await Promise.all([getRelatedBooks(slug, 6), getReviews(slug), getMyReviewStatus(slug)]);
  const others = reviews.filter((r) => r.id !== mine?.review?.id);
  const [intro, ...more] = book.description.split("\n\n").filter(Boolean);

  const specs = [
    ["Autor", book.author.name],
    ["Editorial", book.publisher],
    ["Páginas", book.pages?.toLocaleString("es-CO")],
    ["Idioma", book.language],
  ].filter((row): row is [string, string] => Boolean(row[1]));

  return (
    <article className="flex flex-col gap-12">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: serializeJsonLd(bookJsonLd(book)) }} />

      <nav aria-label="Ruta de navegación" className="text-sm text-brand-800">
        <ol className="flex flex-wrap items-center gap-1">
          <li>
            <Link href="/" className="hover:underline">
              Inicio
            </Link>
          </li>
          {book.categories[0] && (
            <>
              <ChevronRight className="size-4" aria-hidden />
              <li>
                <Link href={`/categoria/${book.categories[0].slug}`} className="hover:underline">
                  {book.categories[0].name}
                </Link>
              </li>
            </>
          )}
          <ChevronRight className="size-4" aria-hidden />
          <li aria-current="page" className="font-semibold">
            {book.title}
          </li>
        </ol>
      </nav>

      <div className="grid gap-8 md:grid-cols-[minmax(0,20rem)_1fr] md:gap-12">
        {/* Portada más pequeña en móvil para que el título y el precio se vean sin hacer scroll. */}
        <div className="mx-auto w-full max-w-[13rem] sm:max-w-xs md:max-w-none md:sticky md:top-4 md:self-start">
          <div className="relative aspect-[2/3] overflow-hidden rounded-2xl bg-card shadow-card">
            <Image
              src={book.cover}
              alt={`Portada de ${book.title}`}
              fill
              priority
              sizes="(min-width: 768px) 320px, 80vw"
              placeholder={book.cover_blur ? "blur" : "empty"}
              blurDataURL={book.cover_blur ?? undefined}
              className="object-contain p-4"
            />
          </div>
        </div>

        <div className="flex flex-col gap-5">
          <header className="flex flex-col gap-2">
            <h1 className="text-4xl font-bold leading-tight sm:text-5xl">{book.title}</h1>
            <p className="text-xl text-brand-800">por {book.author.name}</p>
            <div className="flex flex-wrap items-center gap-3">
              <a href="#resenas" className="hover:opacity-80">
                <StarRating rating={book.rating_avg} count={book.rating_count} />
              </a>
              {book.categories.map((c) => (
                <Link key={c.id} href={`/categoria/${c.slug}`}>
                  <Badge className="hover:bg-brand-200">{c.name}</Badge>
                </Link>
              ))}
            </div>
          </header>

          <div className="flex flex-col gap-3 rounded-2xl bg-card p-5 shadow-card sm:p-6">
            <PriceTag
              price_cop={book.price_cop}
              final_price_cop={book.final_price_cop}
              discount_pct={book.discount_pct}
              size="lg"
            />
            <div>
              <ShippingBadge free={book.free_shipping} cost={book.shipping_cost_cop} />
            </div>
            <PurchaseBox bookId={book.id} stock={book.stock} />
            <FavoriteButton bookId={book.id} title={book.title} variant="text" className="self-start" />
          </div>

          {specs.length > 0 && (
            <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1.5 text-brand-900">
              {specs.map(([label, value]) => (
                <div key={label} className="contents">
                  <dt className="font-semibold text-brand-800">{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          )}

          {book.incomplete && (
            <p className="flex items-start gap-2 rounded-xl bg-brand-100 p-3 text-sm text-brand-800">
              <Info className="mt-0.5 size-4 shrink-0" aria-hidden />
              Ficha en preparación: aún faltan la editorial, el número de páginas y la descripción de este libro.
            </p>
          )}
        </div>
      </div>

      {intro && (
        <section aria-labelledby="descripcion" className="max-w-3xl">
          <h2 id="descripcion" className="mb-3 text-3xl font-bold text-brand-600">
            Descripción
          </h2>
          <p className="leading-relaxed">{intro}</p>
          {more.length > 0 && (
            <details className="group mt-3">
              <summary className="cursor-pointer text-sm font-semibold uppercase tracking-wide text-accent group-open:mb-3">
                Ver más
              </summary>
              <div className="flex flex-col gap-3 leading-relaxed">
                {more.map((paragraph, i) => (
                  <p key={i}>{paragraph}</p>
                ))}
              </div>
            </details>
          )}
        </section>
      )}

      <section id="resenas" aria-labelledby="titulo-resenas" className="max-w-3xl scroll-mt-4">
        <h2 id="titulo-resenas" className="mb-4 text-3xl font-bold text-brand-600">
          Reseñas
        </h2>
        <div className="flex flex-col gap-6">
          <ReviewComposer slug={slug} mine={mine} />
          {/* Tu propia reseña ya se muestra arriba: si es la única, no se añade además un «sin reseñas». */}
          {(others.length > 0 || !mine?.review) && <ReviewList reviews={others} />}
        </div>
      </section>

      {related.length > 0 && (
        <section aria-labelledby="relacionados">
          <h2 id="relacionados" className="mb-4 text-3xl font-bold text-brand-600">
            También te puede interesar
          </h2>
          <ul className="grid grid-cols-3 gap-4 sm:grid-cols-6">
            {related.map((b) => (
              <li key={b.id}>
                <BookCard book={b} variant="mini" />
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  );
}
