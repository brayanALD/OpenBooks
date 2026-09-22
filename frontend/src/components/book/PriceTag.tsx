import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/cn";
import { formatCOP } from "@/lib/format";

type PriceTagProps = {
  price_cop: number;
  final_price_cop: number;
  discount_pct: number;
  size?: "md" | "lg";
  className?: string;
};

export function PriceTag({ price_cop, final_price_cop, discount_pct, size = "md", className }: PriceTagProps) {
  const hasDiscount = discount_pct > 0;
  return (
    <div className={cn("flex flex-wrap items-baseline gap-x-2 gap-y-1", className)}>
      <span className={cn("font-bold text-accent", size === "lg" ? "text-4xl" : "text-xl")}>
        <span className="sr-only">Precio: </span>
        {formatCOP(final_price_cop)}
      </span>
      {hasDiscount && (
        <>
          <span className={cn("text-brand-600 line-through", size === "lg" ? "text-lg" : "text-sm")}>
            <span className="sr-only">Precio anterior: </span>
            {formatCOP(price_cop)}
          </span>
          <Badge tone="accent">-{discount_pct} %</Badge>
        </>
      )}
    </div>
  );
}
