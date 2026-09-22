import { API_URL } from "@/lib/backend";

// Sirve las portadas subidas desde el panel. Viven en el backend (backend/data/media), y esta ruta las expone
// desde el propio origen: así se ven al instante, sin recompilar (los archivos nuevos de /public no se sirven en producción).
const NAME = /^[a-f0-9]{32}\.webp$/;

export async function GET(_request: Request, { params }: { params: Promise<{ file: string }> }) {
  const { file } = await params;
  if (!NAME.test(file)) return new Response("No encontrado", { status: 404 });

  try {
    const upstream = await fetch(`${API_URL}/media/covers/${file}`, { cache: "no-store" });
    if (!upstream.ok || !upstream.body) return new Response("No encontrado", { status: 404 });
    return new Response(upstream.body, {
      headers: {
        "content-type": "image/webp",
        // El nombre es un uuid y el contenido no cambia: se puede cachear siempre.
        "cache-control": "public, max-age=31536000, immutable",
      },
    });
  } catch {
    return new Response("No se pudo contactar con la API", { status: 502 });
  }
}
