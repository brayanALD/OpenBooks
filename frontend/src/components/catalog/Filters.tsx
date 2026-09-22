import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { SORT_OPTIONS, type ListingValues } from "@/lib/listing";
import { FiltersPanel } from "./FiltersPanel";

type FiltersProps = {
  /** Ruta a la que se envía el formulario (p. ej. /categoria/clasicos). */
  action: string;
  values: ListingValues;
  activeCount: number;
  /** Parámetros que deben conservarse al filtrar (p. ej. la búsqueda `q`). */
  hidden?: Record<string, string>;
};

const CHECKBOXES = [
  { name: "free_shipping", label: "Envío gratis", key: "free_shipping" },
  { name: "on_sale", label: "En descuento", key: "on_sale" },
  { name: "in_stock", label: "Solo disponibles", key: "in_stock" },
] as const;

/**
 * Formulario GET nativo: aplicar filtros es navegar a la misma ruta con otra query.
 * Funciona sin JavaScript, se puede compartir la URL y el servidor renderiza el resultado.
 */
export function Filters({ action, values, activeCount, hidden = {} }: FiltersProps) {
  const clearHref = Object.keys(hidden).length ? `${action}?${new URLSearchParams(hidden)}` : action;

  return (
    <FiltersPanel activeCount={activeCount}>
      <form
        action={action}
        method="get"
        className="flex flex-col gap-5 rounded-2xl bg-card p-5 shadow-card"
        aria-label="Filtros y orden"
      >
        {Object.entries(hidden).map(([name, value]) => (
          <input key={name} type="hidden" name={name} value={value} />
        ))}

        <Select label="Ordenar por" name="sort" defaultValue={values.sort}>
          {SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1 text-sm font-semibold text-brand-800">Precio (COP)</legend>
          <div className="grid grid-cols-2 gap-2">
            <Input label="Mínimo" name="min_price" type="number" min={0} step={1000} inputMode="numeric" defaultValue={values.min_price} />
            <Input label="Máximo" name="max_price" type="number" min={0} step={1000} inputMode="numeric" defaultValue={values.max_price} />
          </div>
        </fieldset>

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1 text-sm font-semibold text-brand-800">Mostrar</legend>
          {CHECKBOXES.map(({ name, label, key }) => (
            <label key={name} className="flex cursor-pointer items-center gap-2.5 text-brand-900">
              <input
                type="checkbox"
                name={name}
                value="true"
                defaultChecked={values[key]}
                className="size-5 rounded border-brand-200 accent-accent"
              />
              {label}
            </label>
          ))}
        </fieldset>

        <div className="flex items-center gap-3">
          <Button type="submit" size="sm">
            Aplicar
          </Button>
          <Link href={clearHref} className="text-sm font-semibold text-brand-600 underline underline-offset-4 hover:text-accent">
            Limpiar
          </Link>
        </div>
      </form>
    </FiltersPanel>
  );
}
