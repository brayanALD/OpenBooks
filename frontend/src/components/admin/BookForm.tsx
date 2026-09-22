"use client";

import { useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { CircleAlert, ImageUp } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { requestJson } from "@/lib/auth-client";
import { formatCOP } from "@/lib/format";
import { toast } from "@/store/ui.store";
import type { AdminBook, CoverUpload } from "@/types/admin";

type Props = {
  book?: AdminBook; // sin libro = crear
  categories: { id: string; name: string }[];
  authors: string[];
};

type Values = {
  title: string;
  author_name: string;
  category_ids: string[];
  publisher: string;
  language: string;
  pages: string;
  description: string;
  price_cop: string;
  discount_pct: string;
  shipping_cost_cop: string;
  stock: string;
  featured: boolean;
  bestseller: boolean;
  active: boolean;
};

const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;
const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];
const PLACEHOLDER = "/covers/sin-portada.webp";

const int = (text: string) => (text.trim() === "" ? null : Number(text));
const isInt = (n: number | null): n is number => n !== null && Number.isInteger(n);

function initial(book?: AdminBook): Values {
  return {
    title: book?.title ?? "",
    author_name: book?.author_name ?? "",
    category_ids: book?.category_ids ?? [],
    publisher: book?.publisher ?? "",
    language: book?.language ?? "",
    pages: book?.pages?.toString() ?? "",
    description: book?.description ?? "",
    price_cop: book?.price_cop.toString() ?? "",
    discount_pct: book?.discount_pct.toString() ?? "0",
    shipping_cost_cop: book?.shipping_cost_cop.toString() ?? "0",
    stock: book?.stock.toString() ?? "0",
    featured: book?.featured ?? false,
    bestseller: book?.bestseller ?? false,
    active: book?.active ?? true,
  };
}

function validate(v: Values): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!v.title.trim()) errors.title = "Escribe el título.";
  else if (v.title.trim().length > 200) errors.title = "Máximo 200 caracteres.";
  if (v.author_name.trim().length < 2) errors.author_name = "Escribe el autor.";
  if (v.category_ids.length === 0) errors.category_ids = "Elige al menos una categoría.";

  const price = int(v.price_cop);
  if (!isInt(price) || price < 0 || price > 100_000_000) errors.price_cop = "Un precio entero en pesos, de 0 en adelante.";
  const discount = int(v.discount_pct);
  if (!isInt(discount) || discount < 0 || discount > 90) errors.discount_pct = "Entre 0 y 90.";
  const shipping = int(v.shipping_cost_cop);
  if (!isInt(shipping) || shipping < 0) errors.shipping_cost_cop = "0 si el envío es gratis.";
  const stock = int(v.stock);
  if (!isInt(stock) || stock < 0 || stock > 100_000) errors.stock = "Un número entero, de 0 en adelante.";
  const pages = int(v.pages);
  if (pages !== null && (!isInt(pages) || pages < 1 || pages > 20_000)) errors.pages = "Déjalo vacío o entre 1 y 20.000.";
  if (v.description.length > 20_000) errors.description = "Máximo 20.000 caracteres.";
  return errors;
}

export function BookForm({ book, categories, authors }: Props) {
  const router = useRouter();
  const fileInput = useRef<HTMLInputElement>(null);
  const [values, setValues] = useState<Values>(() => initial(book));
  const [cover, setCover] = useState<CoverUpload | null>(null); // solo si se subió una nueva en esta sesión
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const set = <K extends keyof Values>(key: K, value: Values[K]) => {
    setValues((current) => ({ ...current, [key]: value }));
    setErrors((current) => (current[key] ? { ...current, [key]: "" } : current));
  };
  const text = (key: keyof Values) => ({
    name: key,
    value: values[key] as string,
    error: errors[key],
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => set(key, e.target.value as never),
  });

  const price = int(values.price_cop);
  const discount = int(values.discount_pct);
  const finalPrice = isInt(price) && isInt(discount) && discount >= 0 && discount <= 90 ? Math.floor((price * (100 - discount)) / 100) : null;
  const shownCover = cover?.cover ?? book?.cover ?? PLACEHOLDER;

  async function onFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = ""; // permite volver a elegir el mismo archivo
    if (!file) return;
    setUploadError(null);
    if (!ACCEPTED.includes(file.type)) return setUploadError("Usa una imagen JPG, PNG o WebP.");
    if (file.size > MAX_UPLOAD_BYTES) return setUploadError("La imagen pesa más de 5 MB.");

    setUploading(true);
    try {
      const body = new FormData();
      body.append("file", file);
      const response = await fetch("/api/admin/uploads/cover", { method: "POST", body });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message = data?.detail?.message;
        setUploadError(typeof message === "string" ? message : "No se pudo subir la imagen.");
        return;
      }
      setCover(data as CoverUpload);
    } catch {
      setUploadError("No pudimos conectar con el servidor.");
    } finally {
      setUploading(false);
    }
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);

    const found = validate(values);
    setErrors(found);
    const firstInvalid = Object.keys(found)[0];
    if (firstInvalid) {
      (event.currentTarget.elements.namedItem(firstInvalid) as HTMLElement | null)?.focus?.();
      setFormError("Revisa los campos marcados.");
      return;
    }

    const payload = {
      title: values.title.trim(),
      author_name: values.author_name.trim(),
      category_ids: values.category_ids,
      publisher: values.publisher.trim() || null,
      language: values.language.trim() || null,
      pages: int(values.pages),
      description: values.description.trim(),
      price_cop: int(values.price_cop),
      discount_pct: int(values.discount_pct),
      shipping_cost_cop: int(values.shipping_cost_cop),
      stock: int(values.stock),
      featured: values.featured,
      bestseller: values.bestseller,
      active: values.active,
      ...(cover ?? {}),
    };

    setSaving(true);
    const result = book
      ? await requestJson<AdminBook>("PATCH", `/api/admin/books/${book.id}`, payload)
      : await requestJson<AdminBook>("POST", "/api/admin/books", payload);
    setSaving(false);

    if (!result.ok) {
      if (result.status === 401 || result.status === 403) return router.push("/login?next=/admin/libros");
      const mapped: Record<string, string> = {};
      for (const path of Object.keys(result.fields)) mapped[path] = "Revisa este dato.";
      setErrors(mapped);
      setFormError(result.message);
      return;
    }

    toast.success(book ? `«${result.data.title}» guardado.` : `«${result.data.title}» creado.`);
    router.push("/admin/libros");
    router.refresh();
  }

  const toggle = (key: "featured" | "bestseller" | "active", label: string, hint: string) => (
    <label className="flex cursor-pointer items-start gap-3">
      <input type="checkbox" name={key} checked={values[key]} onChange={(e) => set(key, e.target.checked)} className="mt-1 size-5 rounded accent-accent" />
      <span>
        <span className="font-semibold">{label}</span>
        <span className="block text-sm text-brand-800">{hint}</span>
      </span>
    </label>
  );

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-8">
      {formError && (
        <p role="alert" className="flex items-start gap-2 rounded-xl bg-accent px-4 py-3 text-sm font-semibold text-white">
          <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
          {formError}
        </p>
      )}

      <div className="grid gap-8 lg:grid-cols-[1fr_16rem]">
        <div className="flex flex-col gap-8">
          <fieldset className="flex flex-col gap-4 rounded-2xl bg-card p-6 shadow-card">
            <legend className="float-left mb-2 font-display text-2xl font-bold text-brand-600">Datos del libro</legend>
            <Input className="clear-both" label="Título" {...text("title")} />
            <div>
              <Input label="Autor" list="autores" autoComplete="off" hint="Si el autor ya existe se reutiliza; si no, se crea." {...text("author_name")} />
              <datalist id="autores">
                {authors.map((name) => (
                  <option key={name} value={name} />
                ))}
              </datalist>
            </div>

            <fieldset className="flex flex-col gap-2" aria-describedby={errors.category_ids ? "cat-error" : undefined}>
              <legend className="mb-1 text-sm font-semibold text-brand-800">Categorías</legend>
              <div className="flex flex-wrap gap-x-5 gap-y-2">
                {categories.map((category) => (
                  <label key={category.id} className="flex cursor-pointer items-center gap-2">
                    <input
                      type="checkbox"
                      name="category_ids"
                      checked={values.category_ids.includes(category.id)}
                      onChange={(e) =>
                        set("category_ids", e.target.checked ? [...values.category_ids, category.id] : values.category_ids.filter((c) => c !== category.id))
                      }
                      className="size-5 rounded accent-accent"
                    />
                    {category.name}
                  </label>
                ))}
              </div>
              {errors.category_ids && (
                <p id="cat-error" className="text-sm text-accent">
                  {errors.category_ids}
                </p>
              )}
            </fieldset>

            <div className="grid gap-4 sm:grid-cols-3">
              <Input label="Editorial" {...text("publisher")} />
              <Input label="Idioma" {...text("language")} />
              <Input label="Páginas" type="number" min={1} inputMode="numeric" {...text("pages")} />
            </div>
            <Textarea label="Descripción" hint="Separa los párrafos con una línea en blanco." {...text("description")} />
          </fieldset>

          <fieldset className="flex flex-col gap-4 rounded-2xl bg-card p-6 shadow-card">
            <legend className="float-left mb-2 font-display text-2xl font-bold text-brand-600">Precio e inventario</legend>
            <div className="clear-both grid gap-4 sm:grid-cols-2">
              <Input label="Precio de lista (COP)" type="number" min={0} step={1} inputMode="numeric" {...text("price_cop")} />
              <Input label="Descuento (%)" type="number" min={0} max={90} inputMode="numeric" {...text("discount_pct")} />
              <Input label="Envío (COP)" type="number" min={0} step={1} inputMode="numeric" hint="0 = envío gratis" {...text("shipping_cost_cop")} />
              <Input label="Stock" type="number" min={0} step={1} inputMode="numeric" {...text("stock")} />
            </div>
            <p className="rounded-xl bg-brand-100 px-4 py-3" aria-live="polite">
              Precio final al cliente:{" "}
              <strong className="text-accent">{finalPrice === null ? "—" : formatCOP(finalPrice)}</strong>
              {isInt(price) && finalPrice !== null && finalPrice < price && <span className="text-brand-800"> (antes {formatCOP(price)})</span>}
            </p>
          </fieldset>

          <fieldset className="flex flex-col gap-4 rounded-2xl bg-card p-6 shadow-card">
            <legend className="float-left mb-2 font-display text-2xl font-bold text-brand-600">Visibilidad</legend>
            <div className="clear-both flex flex-col gap-4">
              {toggle("active", "Visible en la tienda", "Si lo desmarcas, el libro se oculta: no aparece, no se puede comprar y se quita de los carritos.")}
              {toggle("featured", "Recomendado", "Aparece en «Productos recomendados» de la portada.")}
              {toggle("bestseller", "Más vendido", "Aparece en «Más vendidos» de la portada.")}
            </div>
          </fieldset>
        </div>

        <aside aria-label="Portada y estado" className="flex flex-col gap-3 lg:sticky lg:top-4 lg:self-start">
          <div className="rounded-2xl bg-card p-4 shadow-card">
            <p className="mb-2 text-sm font-semibold text-brand-800">Portada</p>
            <div className="relative mx-auto aspect-[2/3] w-full max-w-44 overflow-hidden rounded-xl bg-brand-100">
              <Image src={shownCover} alt="Portada actual del libro" fill sizes="176px" className="object-contain p-1" unoptimized={shownCover.startsWith("/media/")} />
            </div>
            <input ref={fileInput} type="file" accept={ACCEPTED.join(",")} onChange={onFile} className="sr-only" aria-label="Elegir imagen de portada" />
            <Button type="button" variant="outline" size="sm" className="mt-3 w-full" loading={uploading} onClick={() => fileInput.current?.click()}>
              <ImageUp className="size-4" aria-hidden />
              {uploading ? "Subiendo…" : "Cambiar portada"}
            </Button>
            <p className="mt-2 text-xs text-brand-800">JPG, PNG o WebP, hasta 5 MB.</p>
            {cover && <p className="mt-1 text-xs font-semibold text-brand-600">Portada nueva: se guarda al guardar el libro.</p>}
            {uploadError && (
              <p role="alert" className="mt-2 text-sm font-semibold text-accent">
                {uploadError}
              </p>
            )}
          </div>

          <Button type="submit" size="lg" loading={saving} className="w-full">
            {book ? "Guardar cambios" : "Crear libro"}
          </Button>
          <Link href="/admin/libros" className="text-center text-sm font-semibold text-brand-600 underline underline-offset-4 hover:text-accent">
            Cancelar
          </Link>
        </aside>
      </div>
    </form>
  );
}
