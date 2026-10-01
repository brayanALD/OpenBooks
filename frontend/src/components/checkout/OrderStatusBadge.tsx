import { Badge, type Tone } from "@/components/ui/Badge";
import { ORDER_STATUS_LABEL, type OrderStatus } from "@/types/order";

const TONE: Record<OrderStatus, Tone> = {
  pending: "warning",
  paid: "info",
  failed: "danger",
  shipped: "info",
  delivered: "success",
  cancelled: "neutral",
};

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  return <Badge tone={TONE[status]}>{ORDER_STATUS_LABEL[status]}</Badge>;
}
