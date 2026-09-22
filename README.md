# Open Books — Librería virtual

Tienda de libros full-stack, con catálogo, carrito, checkout con pago simulado, cuentas, reseñas verificadas, favoritos y un
panel de administración. Nace como la migración de un sitio estático en HTML (`legacy/`, que se conserva intacto como
referencia: de ahí sale el catálogo original) a una aplicación dinámica.

- **Frontend:** Next.js 16 (App Router) + TypeScript + Tailwind CSS v4 + Zustand
- **Backend:** FastAPI + Pydantic v2, persistencia en archivos JSON (**sin base de datos**)
- **Pagos:** simulados (`MockPaymentProvider`), intercambiables por una pasarela real

## Funcionalidades

- **Catálogo:** búsqueda, filtros (categoría, autor, precio, envío gratis, en oferta, disponibilidad), ordenamiento, vista
  rápida, libros relacionados y **recomendaciones en portada** (ver «API del catálogo») que se adaptan a cada cuenta.
- **Carrito:** persistente para invitados, sincronizado con la cuenta al iniciar sesión; precio, stock y totales los calcula
  siempre el servidor (ver «Carrito»).
- **Cuentas:** registro, login, sesión por cookie `httpOnly` con JWT, favoritos (ver «Cuentas y sesión» y «Favoritos»).
- **Checkout y pedidos:** pago simulado con tarjetas de prueba, historial de pedidos, reintentos si el pago falla
  (ver «Pedidos y pago simulado»).
- **Reseñas verificadas:** solo puede reseñar quien compró el libro (ver «Reseñas verificadas»).
- **Panel de administración:** libros, stock, portadas y pedidos, protegido por rol (ver «Panel de administración»).
- **Modo oscuro/claro** con persistencia y sin parpadeo al cargar (ver «Modo oscuro»).

Hay una suite de tests de backend (pytest) y una suite E2E de Playwright —catálogo, compra completa, panel de administración,
reseñas y accesibilidad WCAG 2.1 AA— descritas en «Tests».

## Arranque en local

Requisitos: Node 20+, Python 3.12+.

```powershell
# 1) Backend (docs interactivas en http://localhost:8000/docs)
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# 2) Frontend (http://localhost:3000), en otra terminal
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

### Puertos y variables de entorno

Si el puerto 8000 está ocupado por otro programa, usa otro para el backend y apunta el frontend a él
(**qué backend usa el frontend lo decide `frontend/.env.local`**, no el puerto en el que lo hayas arrancado):

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8010
```

```ini
# frontend/.env.local
API_URL=http://localhost:8010/api/v1
```

| Variable | Dónde | Por defecto | Para qué |
| --- | --- | --- | --- |
| `API_URL` | `frontend/.env.local` | `http://localhost:8000/api/v1` | URL del backend (incluye `/api/v1`) |
| `SITE_URL` | `frontend/.env.local` | `http://localhost:3000` | URL pública, para sitemap y datos estructurados |
| `JWT_SECRET` | `backend/.env` | valor de desarrollo | Firma de las sesiones. Con `ENVIRONMENT=production` es obligatoria y de 32+ caracteres |
| `ENVIRONMENT` | `backend/.env` | `development` | `production` activa las comprobaciones de seguridad |
| `DATA_DIR` | entorno del backend | `backend/data` | Carpeta de los archivos JSON (útil para pruebas con datos de mentira) |
| `PAYMENT_DELAY_SECONDS` | `backend/.env` | `0.8` | Espera de la pasarela simulada |
| `FRONTEND_ORIGIN` | `backend/.env` | `http://localhost:3000` | Origen permitido por CORS |

Next.js lee las variables solo al arrancar: tras editar `.env.local`, reinicia `npm run dev`.
El frontend consulta la API desde el servidor (Server Components), así que el backend debe estar en marcha.

## Estructura

```text
legacy/     Sitio original intacto (referencia; de ahí sale el catálogo importado)
frontend/   Aplicación Next.js
  src/app/(shop)/      Rutas de la tienda: inicio, categoria/[slug], libro/[slug], buscar, terminos
  src/components/      ui/ (botón, input, modal…), layout/ (header, nav, footer), book/, catalog/
  src/lib/             api-client, recommendations, session (cookie), route-handlers (proxies), validation, listing, format, seo
  src/store/           Zustand: cart.store (carrito persistente) y ui.store (avisos, panel del carrito)
  src/app/api/         Route Handlers que hacen de proxy hacia FastAPI: auth/*, cart, cart/merge, cart/validate, orders
  src/components/      … también auth/ (formularios, sincronización del carrito), cart/ y checkout/
  src/app/admin/       Panel de administración (resumen, libros, pedidos); su propio layout, sin cabecera de la tienda
  src/app/media/       Ruta que sirve las portadas subidas desde el panel (viven en el backend)
  e2e/                 Tests E2E de Playwright (catálogo, compra, admin, reseñas, accesibilidad)
  src/proxy.ts         Comprobación optimista de sesión para /cuenta, /checkout y /admin
  public/covers/       Portadas en webp (generadas por los scripts de importación) y sin-portada.webp (la de por defecto)
backend/    API FastAPI: routers -> services -> repositories -> JSON
  app/api/v1/          books.py, categories.py, cart.py, auth.py, orders.py, reviews.py, wishlist.py, admin.py, media.py
  app/services/        Catálogo, carrito (validación y guardado), autenticación, pedidos, administración
  app/core/            security (argon2, JWT), deps (usuario actual, admin), locks (candado de inventario), images, file_lock
  app/repositories/    Interfaz Repository + adaptadores JSON y en memoria
  app/payments/        Puerto PaymentProvider + MockPaymentProvider (pasarela simulada)
  data/                books, authors, categories, reviews (.json) e import_report.md
                       (users.json, carts.json, wishlists.json y orders.json se crean solos y no se versionan)
  data/media/covers/   Portadas subidas desde el panel (se crea sola)
  scripts/             import_legacy.py, process_images.py, demo_reviews.py, seed_admin.py, make_placeholder_cover.py,
                       add_catalog.py + catalog_extra.txt (262 libros reales más, 9 categorías nuevas),
                       catalog_rules.py (envío, ISBN, descuento), generic_reviews.py (reseñas de muestra genéricas),
                       enrich_catalog.py (aplica esas reglas al catálogo ya importado)
  tests/
```

## API del catálogo

Base: `/api/v1`. Documentación completa en `/docs`.

| Endpoint | Descripción |
| --- | --- |
| `GET /books` | Listado con `q`, `category`, `author`, `min_price`, `max_price`, `free_shipping`, `on_sale`, `in_stock`, `featured`, `bestseller`, `sort`, `page`, `page_size` |
| `GET /books/{slug}` | Detalle de un libro |
| `GET /books/{slug}/related` | Libros relacionados (mismo autor, luego misma categoría) |
| `GET /books/recommended` | Recomendaciones de portada, `limit` (por defecto 8). Público, pero se personaliza si hay sesión: sin compras pagadas da lo mismo que a un cliente nuevo (destacados y más vendidos); con compras pagadas (`paid`/`shipped`/`delivered`), libros afines por autor y categoría a lo ya comprado |
| `GET /books/{slug}/reviews` | Reseñas de un libro (con `verified` y `updated_at`) |
| `GET /books/{slug}/reviews/mine` | Si puedo reseñar el libro (`can_review`, `has_purchased`) y mi reseña, si la hay |
| `POST /books/{slug}/reviews` | Publica mi reseña (`rating` 1–5, `comment` 10–2000). 403 si no compré el libro, 409 si ya reseñé |
| `PUT/DELETE /books/{slug}/reviews/mine` | Edita o borra mi reseña |
| `GET /categories`, `GET /categories/{slug}` | Categorías con su número de libros |
| `POST /cart/validate` | Recibe `{items: [{book_id, quantity}]}` y devuelve precios, stock, avisos y totales calculados por el servidor |
| `POST /auth/register` | Crea la cuenta (siempre rol `customer`) y devuelve el token y el usuario |
| `POST /auth/login` | Inicia sesión; 401 con el mismo mensaje si falla el correo o la contraseña; 429 tras 5 fallos |
| `GET /auth/me` | Usuario de la sesión (`Authorization: Bearer <token>`) |
| `GET/PUT /cart`, `POST /cart/merge` | Carrito guardado de la cuenta (requieren sesión) |
| `POST /orders` | Checkout: crea el pedido y cobra. 201 (o 200 si la `idempotency_key` ya existía). Un pago rechazado devuelve el pedido con `status: "failed"`, no un error |
| `GET /orders`, `GET /orders/{id}` | Mis pedidos (404 si el pedido es de otra persona) |
| `GET /wishlist`, `GET /wishlist/ids` | Mis favoritos (con tarjetas, del más reciente al más antiguo) o solo sus ids |
| `PUT/DELETE /wishlist/{book_id}` | Añade o quita un favorito (idempotente). 404 si el libro no existe o está oculto; máximo 200 |

Precios en pesos colombianos enteros. `final_price_cop` ya incluye el descuento.
La búsqueda ignora mayúsculas y tildes (`garcia` encuentra «García Márquez»).

## Carrito

- **Desde las tarjetas** (portada, categorías y búsqueda) hay tres botones de solo icono (el tercero, un ojo, abre la *vista rápida*; ver más abajo) y los dos de compra: un carrito (añade 1 unidad y abre el panel
  del carrito) y un icono de billetes («Comprar ahora»: añade 1 y va a `/carrito`). Respetan el stock y el máximo por libro; los agotados no
  los muestran. Componente: `frontend/src/components/catalog/CardActions.tsx`.
- El navegador guarda solo `{bookId, quantity}` en `localStorage` (`openbooks-cart-v1`). **Los precios, el stock y los totales
  los calcula siempre el servidor** con `POST /cart/validate`; nada de lo que envíe el cliente se toma como precio.
- El navegador no habla con FastAPI directamente: llama a `/api/cart/validate` (Next), que reenvía al backend.
- Máximo 10 unidades por libro y por pedido, y nunca más que el stock. Si el stock cambia, el carrito se ajusta solo y avisa;
  los libros agotados se quedan a la vista, sin sumar al total; los que dejan de existir se quitan.
- **Envío:** un solo paquete por pedido, se cobra el envío **más caro** entre los libros (no la suma). Es una regla provisional
  y vive en una sola función: `shipping_for` en `backend/app/services/cart_service.py`.
- Un `localStorage` corrupto o con entradas inválidas se limpia al cargar en vez de romper la página.

## Cuentas y sesión

- **Registro:** nombre, apellidos, correo, celular (opcional, 10 dígitos que empiezan por 3), dirección, ciudad, indicaciones
  (opcional) y contraseña (mínimo 8 caracteres, escrita dos veces). Para pagar hay que iniciar sesión; el carrito de invitado no.
- **Dónde vive la sesión:** el backend emite un JWT y **Next lo guarda en una cookie `httpOnly`** (`SameSite=Lax`, `Secure` en
  producción). El JavaScript del navegador nunca ve el token, así que un XSS no puede robar la sesión. Los Route Handlers de
  `/api` lo reenvían a FastAPI como `Authorization: Bearer`.
- **Contraseñas** con argon2id. Correo y contraseña incorrectos dan el mismo error y tardan lo mismo (no se puede saber qué
  correos tienen cuenta por el mensaje ni por el tiempo). Tras 5 fallos seguidos con un correo, se bloquea 15 minutos
  (en memoria y por proceso: vale para un único worker).
- **Rutas protegidas:** `src/proxy.ts` manda al login sin cookie (comprobación optimista); cada página privada valida de
  verdad la sesión con el backend (`requireUser`). El destino `?next=` solo admite rutas internas (evita *open redirect*).
- **Carrito con cuenta:** se guarda en el servidor y se sincroniza al cambiarlo. Al iniciar sesión, el carrito de invitado se
  **suma** al de la cuenta (10 por libro como máximo). Al cerrar sesión se vacía el del navegador y el de la cuenta se conserva.
- **CSRF:** además de `SameSite=Lax`, los Route Handlers rechazan peticiones con un `Origin` de otro sitio.
- **Administrador:** no hay uno por defecto. Se crea a mano; la contraseña se pide por teclado (o `--password-stdin`):

  ```powershell
  cd backend
  .\.venv\Scripts\python.exe -m scripts.seed_admin --email admin@correo.com --first-name Ana --last-name Pérez
  ```

- **Fuera de alcance por ahora:** verificación del correo y recuperación de contraseña (necesitan un servicio de correo).

## Pedidos y pago simulado

- **Flujo:** carrito → `/checkout` (requiere sesión) → pedido → `/cuenta/pedidos/[id]`. La dirección se precarga desde la cuenta y se puede
  cambiar **solo para ese pedido**; el pedido guarda su propia copia y la cuenta no cambia.
- **El servidor decide precios y stock**, igual que en el carrito. El navegador envía el total que vio en pantalla (`expected_total_cop`):
  si los precios cambiaron mientras tanto, el servidor responde 409 en vez de cobrar otra cifra.
- **Sin vender de más ni cobrar dos veces.** Orden interno: (1) bajo candado se reserva el stock y se crea el pedido «pending»,
  (2) se cobra, (3) si se aprueba pasa a «paid» y se vacía el carrito; si se rechaza, se devuelve el stock y queda «failed». Cada intento
  lleva una `idempotency_key`: si la petición se repite (doble clic, recarga) se devuelve el mismo pedido y no se cobra otra vez.
- **Pago rechazado:** el pedido queda en el historial como «Pago fallido», el stock no se toca y el carrito se conserva para reintentar
  (cada reintento es un pedido nuevo).
- **Datos de tarjeta:** nunca se guardan ni se devuelven; el pedido solo conserva la marca y los 4 últimos dígitos («Visa •••• 4242»).
  Los errores de validación (422) tampoco repiten lo que escribió el usuario.
- **Tarjetas de prueba** (el formulario las lista y permite rellenarlas), con cualquier fecha futura y cualquier CVC de 3 dígitos:

  | Número | Resultado |
  | --- | --- |
  | `4242 4242 4242 4242` | Aprobada (Visa) |
  | `5555 5555 5555 4444` | Aprobada (Mastercard) |
  | `4000 0000 0000 0002` | Rechazada por el banco |
  | `4000 0000 0000 9995` | Fondos insuficientes |
  | `4000 0000 0000 0069` | Tarjeta vencida |
  | `4000 0000 0000 0127` | CVC incorrecto |

  Cualquier otra tarjeta válida se rechaza, para que se note que es un simulador.
- **Pasarela real:** `MockPaymentProvider` implementa el puerto `PaymentProvider` (`backend/app/payments`). Mercado Pago, Wompi o Stripe
  serían otro adaptador. Con una real, la tarjeta **no debe pasar por este servidor**: se tokeniza en el navegador y aquí solo llegaría el token.
- **Límites conocidos:** el candado que evita la sobreventa es de un solo proceso (un único worker), como el almacenamiento JSON. Si el
  proceso muere justo entre reservar y cobrar, el pedido queda «pending» con el stock reservado. La espera de la pasarela simulada
  (0,8 s) se cambia con `PAYMENT_DELAY_SECONDS`.

## Panel de administración

Solo para cuentas con rol `admin` (se crean con `seed_admin`, ver «Cuentas y sesión»). Entrada: `/admin`, o el enlace «Panel» del
header y de `/cuenta`. A un cliente `/admin/*` le responde 404 (como si no existiera) y su API, 403.

- **Resumen:** libros activos/ocultos/agotados/con pocas unidades, ingresos y pedidos por estado.
- **Libros:** listado con búsqueda y filtros (visibles, ocultos, poco stock), crear y editar (título, ISBN, autor, categorías, precio,
  descuento, envío, stock, recomendado/más vendido, visibilidad, portada). El autor se reutiliza si ya existe (sin distinguir mayúsculas
  ni tildes) o se crea.
  El **slug no cambia** al editar el título, para no romper enlaces guardados.
- **Ocultar, no borrar:** un libro oculto desaparece de la tienda, de las búsquedas, del sitemap y de los carritos (se quita con un aviso), y no
  se puede comprar; sigue en el panel y los pedidos antiguos conservan su copia. Se puede volver a mostrar.
- **Portadas:** se suben en JPG, PNG o WebP (máx. 5 MB) y se convierten a webp. El servidor comprueba el **contenido**, no la extensión ni el tipo
  que declare el navegador; rechaza SVG, GIF, archivos corruptos y «bombas» de píxeles; y guarda el archivo con un nombre aleatorio (nunca el
  subido). Se guardan en `backend/data/media/covers/` y se sirven por `/media/covers/<uuid>.webp`, así se ven al instante sin recompilar.
- **Pedidos:** listado con búsqueda (número, cliente, correo) y filtro por estado; detalle con cliente, envío y pago. Estados:
  `Pagado → Enviado → Entregado`, y `Pagado → Cancelado`. **Solo se cancela antes de enviar**, y al cancelar las unidades vuelven al inventario
  (una sola vez). Entregado y Cancelado son finales; los pedidos fallidos no admiten cambios. El pago es simulado: no se calcula reembolso.
- **Sin pisarse con las compras:** administrador y checkout comparten un candado de inventario (`app/core/locks.py`), así una edición no pierde el
  stock que acaba de descontar una venta. Hay un test que falla si se quita (con el disco real la carrera es mucho más probable que en memoria).
- Todo el texto que se escribe (título, autor, descripción) se muestra como texto, nunca como HTML.

## Modo oscuro

- El botón de sol/luna del encabezado (y del panel de administración) cambia entre claro y oscuro. Sin elección guardada se sigue la preferencia del
  sistema; la elección se recuerda en `localStorage` (`openbooks-theme`). Un pequeño script en el `<head>` (`layout.tsx`) fija el tema antes de
  pintar, así que no hay parpadeo.
- Se activa con `<html data-theme="dark">`. En `globals.css` el bloque `:root[data-theme="dark"]` reasigna los tonos de fondo de la escala `brand`
  (y `--color-card`, que sustituye a `bg-white`); el texto y algunos bordes, que comparten tono con fondos que siguen oscuros (botones, chips),
  se corrigen clase a clase justo debajo. Para retocar la paleta oscura basta con editar ese bloque.
- Los tests E2E (`theme.spec.ts`) comprueban la preferencia del sistema, el botón, la persistencia y el contraste WCAG AA en modo oscuro
  de la tienda, la cuenta, el checkout y el panel.

## Vista rápida

El ojo de cada tarjeta abre un modal con la portada, precio, envío, valoración, descripción, editorial, páginas e ISBN, el selector de cantidad,
«Añadir al carrito», «Comprar ahora», el corazón de favoritos y un enlace a la ficha completa. La ficha se pide al abrir
(`GET /api/books/{slug}`, público) y se guarda mientras la página siga abierta. Al añadir al carrito el modal se cierra y se abre el
panel del carrito; con Escape, la X o un clic fuera se cierra. Componente: `frontend/src/components/catalog/QuickView.tsx`.

## Favoritos

- Cada tarjeta (portada, categorías, búsqueda) tiene un corazón sobre la portada, y la ficha del libro un botón «Añadir a favoritos».
  Sin sesión llevan al login y, al entrar, se vuelve a la misma página.
- La lista vive en la cuenta (`backend/data/wishlists.json`, no se versiona), se ve en `/cuenta/favoritos` (también desde el icono de corazón del
  encabezado) y solo guarda ids: si el administrador oculta un libro deja de verse, y reaparece si se reactiva.
- El navegador solo conoce los ids (`WishlistSync` → `GET /wishlist/ids`) para pintar los corazones; los cambios son optimistas y se revierten si el servidor falla.

## Reseñas verificadas

- Reseña quien tiene un pedido `paid`, `shipped` o `delivered` con ese libro (un pago rechazado o un pedido cancelado no cuentan).
  Es **una reseña por libro y persona**, que se puede editar y borrar; la comprueba el servidor, no el navegador.
- Se muestran con la insignia «Compra verificada». Las reseñas de muestra (`is_demo`) siguen visibles, sin insignia y con un aviso:
  72 escritas a mano para los 37 libros originales (`scripts/demo_reviews.py`) y varios cientos genéricas repartidas al azar en el
  resto del catálogo (`scripts/generic_reviews.py`), para que no se vea vacío.
- El administrador puede eliminar cualquier reseña (real o de muestra) desde la ficha del libro en `/admin`, pero no editarla.
- La nota media y el número de reseñas del libro se recalculan al publicar, editar o borrar.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q     # servicios, repositorio JSON, seguridad, datos, imágenes y API
cd ..\frontend
npm run lint
npx tsc --noEmit
npm run build
npm run test:e2e        # E2E con Playwright (requiere haber hecho `npm run build`)
```

**E2E** (`frontend/e2e/`): catálogo, compra completa (invitado → registro → pago aprobado/rechazado), panel de administración,
reseñas verificadas y un escaneo de accesibilidad con axe (WCAG 2.1 AA) de las páginas públicas, de cliente y de admin.
Levanta su propio backend (puerto 8300, catálogo nuevo en `frontend/.e2e/`, que se borra en cada ejecución) y su propio frontend (3300),
así que no toca `backend/data` ni tus servidores de desarrollo. Usa el Google Chrome instalado; para el Chromium de Playwright:
`npx playwright install chromium` y `PW_CHANNEL=chromium-bundled npm run test:e2e`. El informe queda en `frontend/playwright-report`.

**Rendimiento** (Lighthouse sobre la build de producción): escritorio 98–100 en Rendimiento; móvil con throttling simulado 84–87
(LCP ≈ 3,8 s, dominado por el coste de JavaScript en una CPU 4× más lenta). Accesibilidad, Buenas prácticas y SEO: 100 en todas.

La suite de pytest es **hermética**: al empezar importa el catálogo en una carpeta temporal y trabaja ahí, así que no depende de `backend/data`
(que cambia al vender o editar desde el panel) ni escribe en ella (ni en `public/covers`).

**Probar contra el backend real crea cuentas y carritos de verdad** en `backend/data/users.json` y `carts.json`. Para
pruebas de navegador con datos de mentira, arranca un backend con `DATA_DIR` apuntando a una copia del catálogo y
haz que el frontend lo use con `API_URL` (que tiene prioridad sobre `.env.local`); si `API_URL` apunta a tu backend
habitual, los datos de prueba acaban en tu carpeta de datos.

## Catálogo importado

Los 37 libros originales salen del sitio HTML antiguo mediante un script que se puede repetir:

```powershell
cd backend
.\.venv\Scripts\python.exe -m scripts.import_legacy --force
```

- Sin `--force` se niega a sobrescribir un catálogo existente, para no perder cambios hechos desde el admin.
- Genera `backend/data/import_report.md` con lo que decidió y corrigió (precios en conflicto, erratas, libros incompletos).
- El importador deja los **37 libros originales**, 35 autores y 6 categorías (Clásicos, Fantasía, Novela, Biografías, Historia, Desarrollo personal).
  El catálogo completo (ver «Catálogo ampliado») se obtiene ejecutando después `add_catalog`.
- **Datos inventados para desarrollo:** el stock (3–30 unidades), el 15 % de descuento en los 5 libros de «Libros en Descuento» y las 72 reseñas de muestra (marcadas `is_demo`). El sitio original no tenía nada de esto.

## Catálogo ampliado

Además de los 37 libros originales hay **262 libros reales** más y **9 categorías nuevas** (Ciencia ficción, Misterio, Poesía, Terror, Romance,
Ciencia, Infantil, Cocina y Tecnología), de modo que **cada una de las 15 categorías tiene exactamente 20 libros** (299 en total; un libro
está en dos categorías). La lista sale de `backend/scripts/catalog_extra.txt` (categoría, título, autor, descripción):

```powershell
cd backend
.\.venv\Scripts\python.exe -m scripts.add_catalog     # necesita internet; se puede repetir, salta lo que ya existe
```

- **Reales:** título, autor y portada. Las portadas se descargan de [Open Library](https://openlibrary.org) y se convierten a webp en
  `frontend/public/covers`; las páginas y la editorial también salen de allí cuando existen (solo «La historia interminable» se queda sin número de páginas).
  Algunas portadas son de otra edición o idioma del mismo libro (p. ej. inglesas, alemanas o francesas): se pueden cambiar desde el panel de administración.
- **Datos completados:** los 7 libros del sitio original que solo tenían ficha en el listado (Sapiens, El olvido que seremos, etc.) ahora tienen
  descripción, páginas y editorial, y a los libros nuevos sin páginas se les puso las de una edición habitual (`COMPLETIONS` en `add_catalog.py`; solo rellena huecos).
- **Inventados para desarrollo:** precio (25.000–95.000 COP), ISBN, stock (3–30) y las descripciones, escritas a mano en español.
  El envío no es fijo: sigue la misma regla que el resto del catálogo (ver «Envío inventado» más abajo).
- Si repites `import_legacy --force` el catálogo vuelve a los 37 libros originales (las portadas nuevas no se borran): ejecuta `add_catalog` después.
- La barra de categorías es una sola fila que se desliza en horizontal (con flechas en pantallas anchas) y deja a la vista la categoría activa.
- Los libros sin portada utilizable se descartaron y se sustituyeron por otros del mismo tipo, para llegar siempre a 20.

### Envío, ISBN, destacados y descuento (inventados)

Reglas centralizadas en `backend/scripts/catalog_rules.py` y aplicadas por `import_legacy.py`, `add_catalog.py` y
`enrich_catalog.py` (este último las reaplica sobre el catálogo ya importado, sin tocar pedidos/usuarios/carritos):

- **Envío:** gratis si el precio de lista supera $70.000; si no, $5.000 con 150 páginas o menos y $10.000 con más
  (o si no se conocen las páginas).
- **ISBN:** inventado, con el formato y el dígito de control de un ISBN-13 real (no corresponde a una edición existente).
- **Destacado / más vendido:** repartidos de forma determinista en el catálogo ampliado (los 37 originales conservan
  los que tenía el sitio original).
- **Descuento:** 15 % del catálogo, elegido al azar con semilla fija (reproducible), la mitad al 10 % y la mitad al 15 %.
  Se recalcula entero cada vez que se corre `enrich_catalog.py`, no es acumulativo.

```powershell
cd backend
.\.venv\Scripts\python.exe -m scripts.enrich_catalog     # aplica/reaplica estas reglas sobre backend/data
```

## Notas

- Next.js 16: `params`/`searchParams` son asíncronos y el antiguo `middleware` se llama `proxy.ts`.
  La documentación de esta versión está en `frontend/node_modules/next/dist/docs/`.
- Las páginas de la tienda se generan en cada petición (`force-dynamic`): el catálogo cambia desde el panel.
  Habrá que revisar el caché antes de desplegar.
- Los datos de usuarios, carritos y pedidos (`backend/data/*.json`) no se versionan.
- **`books.json` y `authors.json` son datos vivos y se versionan:** las compras (stock) y el panel (libros, autores, precios) los
  modifican, así que aparecerán como cambios en git. Las portadas subidas desde el panel van a `data/media/`, que no se versiona
  (igual que `users.json`, `carts.json`, `wishlists.json` y `orders.json`: ver `.gitignore`).
- **El stock vive en `books.json`:** cada compra lo modifica. Es una consecuencia de no
  usar base de datos (el catálogo y el inventario comparten archivo). Reimportar con `--force` restablece el stock inventado.
- El almacenamiento JSON es solo para un proceso local (un único worker); está aislado tras la interfaz
  `Repository` para poder migrar a una base de datos más adelante.
