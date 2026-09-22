import { Truck } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { formatCOP } from "@/lib/format";

export function ShippingBadge({ free, cost }: { free: boolean; cost: number }) {
  return free ? (
    <Badge tone="success">
      <Truck className="size-3.5" aria-hidden />
      Envío gratis
    </Badge>
  ) : (
    <Badge>
      <Truck className="size-3.5" aria-hidden />
      Envío {formatCOP(cost)}
    </Badge>
  );
}
