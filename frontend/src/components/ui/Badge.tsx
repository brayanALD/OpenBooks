import { cn } from "@/lib/cn";

type Tone = "neutral" | "accent" | "success";

const TONES: Record<Tone, string> = {
  neutral: "bg-brand-100 text-brand-800",
  accent: "bg-accent text-white",
  success: "bg-emerald-100 text-emerald-900",
};

export function Badge({
  tone = "neutral",
  className,
  ...props
}: React.ComponentProps<"span"> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold",
        TONES[tone],
        className,
      )}
      {...props}
    />
  );
}
