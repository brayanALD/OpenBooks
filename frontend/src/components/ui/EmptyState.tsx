import { cn } from "@/lib/cn";

type EmptyStateProps = {
  icon: React.ComponentType<{ className?: string; "aria-hidden"?: boolean }>;
  title: string;
  description?: string;
  /** Acción principal (una sola: Ley de Hick). */
  children?: React.ReactNode;
  /** `error`: no se pudo obtener la información (distinto de «no hay nada»). */
  tone?: "empty" | "error";
  /** Como encabezado de página (404, error) en vez de texto de apoyo. */
  as?: "h1" | "h2" | "p";
  className?: string;
};

/** Estado vacío o de error, con la misma forma en toda la tienda: icono, título, una frase y una acción. */
export function EmptyState({ icon: Icon, title, description, children, tone = "empty", as: Title = "p", className }: EmptyStateProps) {
  const error = tone === "error";
  return (
    <div
      role={error ? "alert" : undefined}
      className={cn("mx-auto flex w-full max-w-xl flex-col items-center gap-4 rounded-2xl bg-card p-10 text-center shadow-card", className)}
    >
      <Icon className={cn("size-12", error ? "text-danger" : "text-ink-faint")} aria-hidden />
      <Title className="font-display text-2xl font-bold">{title}</Title>
      {description && <p className="text-ink-soft">{description}</p>}
      {children}
    </div>
  );
}
