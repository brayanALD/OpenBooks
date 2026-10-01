import { notFound } from "next/navigation";
import { getBook } from "@/lib/api-client";

/**
 * Comprueba que el libro existe ANTES de que `loading.tsx` empiece a enviar el skeleton: una vez enviado, el estado
 * HTTP ya no se puede cambiar y un libro inexistente respondería 200 en vez de 404 (mala señal para buscadores).
 * La petición se comparte con la de la página (Next deduplica los fetch iguales dentro de una misma respuesta).
 */
export default async function BookLayout({ children, params }: { children: React.ReactNode; params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!(await getBook(slug))) notFound();
  return children;
}
