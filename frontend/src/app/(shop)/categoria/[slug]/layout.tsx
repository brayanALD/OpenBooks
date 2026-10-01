import { notFound } from "next/navigation";
import { getCategory } from "@/lib/api-client";

/** Igual que en `libro/[slug]`: el 404 se decide antes del skeleton de `loading.tsx` para que el estado HTTP sea correcto. */
export default async function CategoryLayout({ children, params }: { children: React.ReactNode; params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!(await getCategory(slug))) notFound();
  return children;
}
