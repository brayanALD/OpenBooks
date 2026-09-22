# Informe de importación del sitio original

Generado por `backend/scripts/import_legacy.py`. Revisa lo marcado como **por revisar**.

## Resumen

- **37 libros** (30 con ficha completa, 7 incompletos).
- Por categoría: Clásicos 9, Fantasía 6, Novela 6, Biografías 6, Historia 8, Desarrollo personal 3 (un libro puede estar en varias).
- 72 reseñas de **muestra** (`is_demo`). Las 6 reseñas idénticas del original se descartaron.
- Stock: entre 3 y 30 unidades, determinista por libro. **Es un dato inventado**: el original no tenía stock.
- Descuento del 15 % en los libros de «Libros en Descuento»: Cabeza, Corazón y Manos, Crimen y Castigo, El Jardín de la Bruja Verde, Los renglones torcidos de Dios, Sin Límites.

## Precios en conflicto (por revisar)

Regla acordada: manda el precio de la página de categoría.

- **Crimen y Castigo**: detalle $14.000, index.html $14.000, clasicos.html $45.000 → se usa **$45.000** (listado clasicos.html).
- **Estuche Harry Potter (7 libros)**: detalle $600.000, index.html $600.000, fantasia.html $349.000 → se usa **$349.000** (listado fantasia.html).

> Crimen y Castigo aparecía a $14.000 en la portada, dentro de «Libros en Descuento». Lo más probable es que
> $14.000 fuera su precio ya rebajado y $45.000 el de lista. Con el descuento del 15 % queda a $38.250.

## Envío en conflicto

Regla: los libros de la sección «con ENVÍO GRATUITO» tienen envío gratis; el resto, listado de categoría y luego detalle.

- **Crimen y Castigo**: detalle $0, index.html $0, clasicos.html $5.000 → se usa **$0** (sección «con ENVÍO GRATUITO» de la portada).

## Correcciones de contenido (por revisar)

- **La verdad sobre el caso Savolta**: el original decía autor «Manuel Rivas»; corregido a «Eduardo Mendoza».

## Datos anómalos normalizados (por revisar)

- **Mi Lucha (Lite)**: envío de $500.000 en el original (dato de prueba probable); normalizado a $5.000.

## Libros incompletos

Solo aparecían en el listado de Historia, sin página de detalle: no tienen editorial, páginas, idioma ni
descripción. Se importan con `incomplete = true` para completarlos desde el panel de administración.

- **De animales a dioses** (Yuval Noah Harari)
- **El olvido que seremos** (Héctor Abad Faciolince)
- **La verdad sobre el caso Savolta** (Eduardo Mendoza)
- **Las Venas Abiertas de América Latina (Edición 50 Aniversario)** (Eduardo Galeano)
- **Lecciones de histeria de Colombia (Edición Bicentenario)** (Daniel Samper Pizano)
- **Los peligros de fumar en la cama** (Mariana Enriquez)
- **Mi Lucha (Lite)** (Adolf Hitler)

## Imágenes

- 37 portadas convertidas a webp en `frontend/public/covers/<slug>.webp`.
- Peso: 820 KB de origen → 611 KB.
- No se amplía ninguna imagen; las portadas originales miden ~360 px de alto.
- Imágenes de `legacy/imagenes` que ningún HTML referencia (no se copian, `legacy/` no se toca): 16.
  `1984.webp`, `4go.webp`, `A_las_de_Sangre.webp`, `Baldor.jpg`, `ElonMonda.webp`, `En_agosto.jpg`, `GoticaCulona2.webp`, `bola.png`, `dinos.jpg`, `estrellas.png`, `logo.png`, `maus.jpg`, `muerteAnunciada.webp`, `primera entrega invstigacion.docx`, `rebelinGranja.webp`, `sys.webp`

## Otras erratas del original corregidas

- Editorial «Plaza & Jane» → «Plaza & Janés»; «Penguin Pg» → «Penguin»; editoriales en MAYÚSCULAS normalizadas.
- Autor «Lev N. Tolstói (Leon Tolstói)» y «León Tolstói» unificados; «Fiódor M./Fiódor Dostoyevski» unificados.
- «Gabriel Garcia Márquez» → «Gabriel García Márquez»; «Mark Manson - Will Smith» → «Mark Manson y Will Smith».
- Títulos con tildes o mayúsculas erróneas (Steve Jobs, Autobiografía…, Récords…) y sin «(ingles)» en A Promised Land.
- `???frase???` → `«frase»` en la descripción de Sin Límites.
- Se conservan sin tocar las descripciones con faltas de tilde (p. ej. El Jardín de la Bruja Verde).
- La capitalización de los títulos es heterogénea en el original («En Agosto Nos Vemos» junto a
  «Cien años de soledad») y se respeta; unificarla es una decisión editorial.
- La portada de «The Mamba Mentality: Los secretos de mi éxito» dice «Mentalidad Mamba»; el título es el del original.
