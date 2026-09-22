/**
 * Destino al que volver tras iniciar sesión (`?next=`). Solo se aceptan rutas internas: cualquier otra cosa
 * (`https://evil.com`, `//evil.com`, `/\evil.com`, `javascript:…`) se sustituye por `fallback`.
 * Sin esta comprobación el login sería un "open redirect" para campañas de phishing.
 */
export function safeNext(next: string | string[] | null | undefined, fallback = "/"): string {
  const value = Array.isArray(next) ? next[0] : next;
  if (!value || typeof value !== "string") return fallback;
  // Debe empezar por una sola "/" y no contener caracteres de control ni barras invertidas.
  if (!value.startsWith("/") || value.startsWith("//") || /[\\\u0000-\u001f]/.test(value)) return fallback;
  return value;
}
