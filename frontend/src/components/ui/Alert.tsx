import { CircleAlert, CircleCheck, Info, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/cn";

export type AlertTone = "info" | "success" | "warning" | "danger";

const TONES: Record<AlertTone, { icon: typeof Info; style: string }> = {
  info: { icon: Info, style: "border-info-edge bg-info-soft text-info" },
  success: { icon: CircleCheck, style: "border-success-edge bg-success-soft text-success" },
  warning: { icon: TriangleAlert, style: "border-warning-edge bg-warning-soft text-warning" },
  danger: { icon: CircleAlert, style: "border-danger-edge bg-danger-soft text-danger" },
};

type AlertProps = Omit<React.ComponentProps<"div">, "title"> & {
  tone?: AlertTone;
  title?: React.ReactNode;
  /** Anuncia el mensaje al aparecer (errores y confirmaciones tras una acción). Sin esto es contenido estático. */
  live?: boolean;
};

/**
 * Mensaje en línea (éxito, aviso, error, información). Icono + texto + color: nunca solo color.
 * Los errores se anuncian con `role="alert"`; el resto con `role="status"`.
 */
export function Alert({ tone = "info", title, live = false, className, children, ...props }: AlertProps) {
  const { icon: Icon, style } = TONES[tone];
  const role = live ? (tone === "danger" ? "alert" : "status") : undefined;

  return (
    <div role={role} className={cn("flex items-start gap-3 rounded-2xl border p-4 text-sm", style, className)} {...props}>
      <Icon className="mt-0.5 size-5 shrink-0" aria-hidden />
      <div className="min-w-0 flex-1">
        {title && <p className="font-bold">{title}</p>}
        {children && <div className={cn(title && "mt-0.5")}>{children}</div>}
      </div>
    </div>
  );
}
