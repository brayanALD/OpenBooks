import { Badge } from "@/components/ui/Badge";
import { ORDER_STATUS_LABEL, type OrderStatus } from "@/types/order";

const TONE: Record<OrderStatus, "neutral" | "accent" | "success"> = {
  pending: "neutral",
  paid: "success",
  failed: "accent",
  shipped: "success",
  delivered: "success",
  cancelled: "neutral",
};

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  return <Badge tone={TONE[status]}>{ORDER_STATUS_LABEL[status]}</Badge>;
}
