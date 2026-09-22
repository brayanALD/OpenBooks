import Link from "next/link";
import { FaFacebookF, FaInstagram, FaTiktok, FaXTwitter, FaYoutube } from "react-icons/fa6";
import { SITE } from "@/lib/site";
import { Logo } from "./Logo";

// Mismos destinos genéricos que el sitio original; se sustituirán por los perfiles reales.
const SOCIALS = [
  { name: "Facebook", href: "https://facebook.com", Icon: FaFacebookF },
  { name: "X (Twitter)", href: "https://twitter.com", Icon: FaXTwitter },
  { name: "Instagram", href: "https://instagram.com", Icon: FaInstagram },
  { name: "YouTube", href: "https://youtube.com", Icon: FaYoutube },
  { name: "TikTok", href: "https://tiktok.com", Icon: FaTiktok },
] as const;

export function Footer() {
  return (
    <footer className="mt-16 rounded-t-2xl bg-brand-400 text-brand-900">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-6 px-4 py-8 text-center md:flex-row md:justify-between md:text-left">
        <div className="flex flex-col items-center gap-2 md:items-start">
          <Logo />
          <p className="text-sm">
            © {new Date().getFullYear()} {SITE.name}. Todos los derechos reservados.
          </p>
          <Link href="/terminos" className="text-sm font-semibold underline underline-offset-4 hover:text-accent-dark">
            Términos y condiciones
          </Link>
        </div>

        <ul aria-label="Redes sociales" className="flex gap-3">
          {SOCIALS.map(({ name, href, Icon }) => (
            <li key={name}>
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={name}
                className="grid size-11 place-items-center rounded-full bg-brand-900 text-brand-50 transition duration-150 hover:-translate-y-0.5 hover:bg-accent"
              >
                <Icon className="size-5" aria-hidden />
              </a>
            </li>
          ))}
        </ul>
      </div>
    </footer>
  );
}
