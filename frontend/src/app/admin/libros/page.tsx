import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { Pencil, Plus } from "lucide-react";
import { ToggleActiveButton } from "@/components/admin/ToggleActiveButton";
import { Pagination } from "@/components/catalog/Pagination";
import { Badge } from "@/components/ui/Badge";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { getAdminBooks, requireAdmin } from "@/lib/admin";
import { formatCOP } from "@/lib/format";
import { flattenParams, type RawSearchParams } from "@/lib/listing";

export const metadata: Metadata = { title: "Libros" };

type Props = { searchParams: Promise<RawSearchParams> };

const first = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v);

export default async function AdminBooksPage({ searchParams }: Props) {
  await requireAdmin("/admin/libros");
  const sp = await searchParams;
  const q = first(sp.q)?.trim().slice(0, 100) || undefined;
  const estado = first(sp.estado) ?? "";
  const ordenRaw = first(sp.orden);
  const orden = ordenRaw === "stock_asc" || ordenRaw === "stock_desc" ? ordenRaw : undefined;
  const page = Math.max(1, Number.parseInt(first(sp.page) ?? "1", 10) || 1);

  const data = await getAdminBooks({
    q,
    page,
    active: estado === "activos" ? true : estado === "ocultos" ? false : undefined,
    low_stock: estado === "poco-stock" || undefined,
    sort: orden,
  });

  // El contenedor de la tabla lleva `relative`: los textos `sr-only` son position:absolute y, sin un ancestro posicionado,
  // escapan del recorte del scroll horizontal y ensanchan toda la página en móvil.
  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-4xl font-bold text-brand-600">Libros</h1>
        <ButtonLink href="/admin/libros/nuevo">
          <Plus className="size-4" aria-hidden />
          Nuevo libro
        </ButtonLink>
      </header>

      <form method="get" className="flex flex-wrap items-end gap-3 rounded-2xl bg-card p-4 shadow-card" role="search" aria-label="Buscar libros">
        <div className="min-w-56 flex-1">
          <Input label="Buscar" name="q" defaultValue={q} placeholder="Título o autor" />
        </div>
        <div className="w-48">
          <Select label="Mostrar" name="estado" defaultValue={estado}>
            <option value="">Todos</option>
            <option value="activos">Visibles</option>
            <option value="ocultos">Ocultos</option>
            <option value="poco-stock">Poco o ningún stock</option>
          </Select>
        </div>
        <div className="w-48">
          <Select label="Ordenar por stock" name="orden" defaultValue={orden ?? ""}>
            <option value="">Por defecto (título)</option>
            <option value="stock_asc">Menor a mayor</option>
            <option value="stock_desc">Mayor a menor</option>
          </Select>
        </div>
        <Button type="submit" size="md">
          Filtrar
        </Button>
      </form>

      <p className="text-brand-800" aria-live="polite">
        {data.total} {data.total === 1 ? "libro" : "libros"}
      </p>

      {data.items.length === 0 ? (
        <p className="rounded-2xl bg-card p-8 text-center text-brand-800 shadow-card">No hay libros con esos criterios.</p>
      ) : (
        <div className="relative overflow-x-auto rounded-2xl bg-card shadow-card">
          <table className="w-full min-w-[42rem] text-left">
            <caption className="sr-only">Libros del catálogo</caption>
            <thead className="border-b border-brand-200 text-sm text-brand-800">
              <tr>
                <th scope="col" className="p-3 font-semibold">Libro</th>
                <th scope="col" className="p-3 text-right font-semibold">Precio</th>
                <th scope="col" className="p-3 text-right font-semibold">Stock</th>
                <th scope="col" className="p-3 font-semibold">Estado</th>
                <th scope="col" className="p-3"><span className="sr-only">Acciones</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-100">
              {data.items.map((book) => (
                <tr key={book.id} className={book.active ? undefined : "bg-brand-50 text-brand-800"}>
                  <td className="p-3">
                    <div className="flex items-center gap-3">
                      <span className="relative block h-14 w-10 shrink-0 overflow-hidden rounded bg-brand-100">
                        <Image src={book.cover} alt="" fill sizes="40px" className="object-contain" />
                      </span>
                      <span className="min-w-0">
                        <Link href={`/admin/libros/${book.id}`} className="line-clamp-1 font-semibold hover:underline">
                          {book.title}
                        </Link>
                        <span className="block text-sm text-brand-800">{book.author_name}</span>
                      </span>
                    </div>
                  </td>
                  <td className="p-3 text-right tabular-nums">
                    {formatCOP(book.final_price_cop)}
                    {book.discount_pct > 0 && <span className="block text-xs text-accent">-{book.discount_pct} %</span>}
                  </td>
                  <td className="p-3 text-right tabular-nums">
                    <span className={book.stock === 0 ? "font-bold text-accent" : book.stock <= 5 ? "font-semibold text-accent" : undefined}>{book.stock}</span>
                  </td>
                  <td className="p-3">
                    <span className="flex flex-wrap gap-1">
                      {book.active ? <Badge tone="success">Visible</Badge> : <Badge>Oculto</Badge>}
                      {book.incomplete && <Badge>Incompleto</Badge>}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="flex items-center justify-end gap-1">
                      <Link href={`/admin/libros/${book.id}`} aria-label={`Editar ${book.title}`} title="Editar" className="rounded-full p-2 text-brand-600 hover:bg-brand-100 hover:text-accent">
                        <Pencil className="size-5" aria-hidden />
                      </Link>
                      <ToggleActiveButton id={book.id} title={book.title} active={book.active} />
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Pagination page={data.page} pages={data.pages} basePath="/admin/libros" query={flattenParams(sp)} />
    </div>
  );
}
