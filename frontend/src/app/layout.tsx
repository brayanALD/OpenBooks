import type { Metadata } from "next";
import localFont from "next/font/local";
import { Toaster } from "@/components/ui/Toaster";
import { SITE_URL } from "@/lib/seo";
import { SITE } from "@/lib/site";
import "./globals.css";

// Fuentes autoalojadas (Inter y Playfair Display, licencia OFL): sin peticiones a Google al compilar ni al visitar.
const inter = localFont({
  src: "./fonts/Inter-latin.woff2",
  variable: "--font-inter",
  weight: "100 900",
  display: "swap",
});

const playfair = localFont({
  src: "./fonts/PlayfairDisplay-latin.woff2",
  variable: "--font-playfair",
  weight: "400 900",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: `${SITE.name} — Librería virtual`,
    template: `%s | ${SITE.name}`,
  },
  description: SITE.description,
};

// Se ejecuta antes de pintar para que no haya un parpadeo claro→oscuro: usa la elección guardada o, si no hay, la del sistema.
const THEME_SCRIPT = `try{var t=localStorage.getItem("openbooks-theme");if(t!=="light"&&t!=="dark"){t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}document.documentElement.dataset.theme=t}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang={SITE.locale} className={`${inter.variable} ${playfair.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body className="flex min-h-screen flex-col">
        {children}
        <Toaster />
      </body>
    </html>
  );
}
