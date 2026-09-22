import type { Metadata } from "next";

export const metadata: Metadata = { title: "Términos y condiciones" };

export default function TermsPage() {
  return (
    <article className="mx-auto max-w-2xl">
      <h1 className="text-4xl font-bold text-brand-600">Términos y condiciones</h1>
      <p className="mt-4 text-brand-800">
        Esta sección todavía no tiene contenido. El sitio original tampoco lo tenía: el enlace estaba vacío.
      </p>
    </article>
  );
}
