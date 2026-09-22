"""Reseñas de MUESTRA genéricas (`is_demo=True`), para libros que no tienen una reseña hecha a mano en
demo_reviews.py (que sí habla de la trama de cada libro). Estas no mencionan el contenido: valen para
cualquier libro, como las reseñas típicas de una tienda en línea (envío, empaque, precio, si lo recomiendan).

Deterministas a partir del slug del libro: mismo libro -> mismas reseñas, sin azar entre ejecuciones.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from app.domain.models import Review

REVIEWER_NAMES = [
    "Andrés M.", "Valeria O.", "Camilo R.", "Juliana P.", "Sebastián T.", "Laura C.", "Mateo G.",
    "Daniela H.", "Nicolás F.", "Paula V.", "Santiago B.", "Carolina D.", "Felipe N.", "Manuela S.",
    "Julián A.", "Isabella K.", "David L.", "Tatiana W.", "Óscar E.", "Verónica J.", "Emanuel Q.",
    "Lorena Z.", "Rafael I.", "Ángela Y.", "Cristian U.", "Marcela X.", "Álvaro Ñ.", "Natalia Ll.",
    "Diego C.", "Gabriela M.", "Hernán P.", "Melissa T.", "Ivonne R.", "Wilson G.", "Yesica H.",
    "Brandon F.", "Estefanía N.", "Jhonatan V.", "Milena B.", "Anderson D.", "Katherine S.",
    "Yeison A.", "Paola K.", "Duván L.", "Sandra W.", "Cristhian E.", "Erika J.", "Fabián Q.",
]

COMMENTS_BY_RATING: dict[int, list[str]] = {
    5: [
        "Llegó antes de lo esperado y en perfecto estado, bien protegido. Muy recomendado.",
        "Excelente calidad de impresión y encuadernación. Lo pedí como regalo y quedó encantado quien lo recibió.",
        "Tal cual la descripción, buen precio y despacho rápido. Volvería a comprar aquí sin dudarlo.",
        "Superó mis expectativas. El empaque cuidó muy bien la portada durante el envío.",
        "Un libro que tenía en la lista hace tiempo; la edición es muy buena y llegó impecable.",
        "Buena relación precio-calidad. El pedido llegó completo y a tiempo.",
        "Todo perfecto: desde la compra hasta la entrega. El papel y la impresión son de buena calidad.",
        "Me encantó la edición, se nota el cuidado en el acabado. Repetiré con esta tienda.",
        "Justo lo que buscaba, y a mejor precio que en otras librerías. Llegó muy bien empacado.",
        "Excelente servicio, seguimiento del pedido claro y el libro llegó sin ningún daño.",
        "Muy satisfecho con la compra. La portada es tal cual se ve en las fotos.",
        "Un acierto total. Buen papel, buena letra y llegó antes de la fecha estimada.",
        "Perfecto para regalar: la presentación es muy cuidada y el envío fue rápido.",
        "Excelente experiencia de compra de principio a fin. Lo recomiendo sin reservas.",
        "Buena edición, tapa firme y páginas bien encuadernadas. Nada que reprochar.",
    ],
    4: [
        "Buen libro y buen precio. El envío tardó un par de días más de lo esperado, pero llegó bien.",
        "Edición correcta, aunque la tapa es un poco más delgada de lo que imaginaba. Aun así, contento con la compra.",
        "Llegó en buen estado. Le quito una estrella solo porque el empaque venía algo justo.",
        "Buena calidad general. El proceso de compra fue sencillo y sin contratiempos.",
        "Cumple con lo prometido. La impresión es clara y el precio, competitivo.",
        "Muy buena opción para conseguirlo a este precio. El tiempo de entrega fue razonable.",
        "El libro está en buen estado, aunque llegó con una esquina levemente golpeada. Nada grave.",
        "Buena compra en general, seguiré comprando en esta tienda.",
        "Se ve tal como en las fotos. El despacho fue un poco lento pero sin mayor problema.",
        "Buena calidad de papel y encuadernación. Recomendado para quienes buscan buen precio.",
        "Todo en orden con el pedido. Esperaba un empaque un poco más protegido, pero llegó bien.",
        "Buena edición y buen servicio. Me hubiera gustado que el envío fuera un poco más rápido.",
        "Cumplió mis expectativas. Precio justo comparado con otras librerías.",
        "Buena experiencia de compra. El libro llegó completo y como se describía.",
    ],
    3: [
        "El libro está bien, pero el envío tardó más de lo que esperaba.",
        "Cumple, aunque la calidad del papel es más sencilla de lo que pensé por el precio.",
        "Todo normal: ni una mala experiencia ni algo destacable. Llegó como se pidió.",
        "Buen contenido, pero llegó con la caja algo maltratada por fuera; el libro en sí estaba bien.",
        "Precio razonable, aunque tardó bastante en despacharse.",
        "Correcto en general, sin más. Esperaba una edición un poco más grande.",
        "Cumple su función. El tiempo de entrega podría mejorar.",
        "Ni tan bien ni tan mal: llegó completo, aunque con algo de retraso frente a la fecha estimada.",
    ],
    2: [
        "El pedido tardó bastante más de lo indicado al comprar.",
        "El libro en sí está bien, pero llegó con la portada algo doblada por el empaque.",
        "Esperaba mejor calidad de impresión por el precio pagado.",
        "El servicio de entrega dejó que desear; el libro llegó varios días tarde.",
    ],
}

# Peso relativo de cada calificación (no una probabilidad exacta): la mayoría de reseñas son buenas,
# como suele pasar en las tiendas reales, con algunas más tibias o críticas.
RATING_WEIGHTS: list[tuple[int, int]] = [(5, 45), (4, 35), (3, 14), (2, 6)]


def review_count_for(slug: str) -> int:
    """0 a 4 reseñas por libro. Cerca de un tercio de los libros se queda sin reseñas todavía, como en
    cualquier catálogo real con artículos poco o nada comprados."""
    rng = random.Random(f"count:{slug}")
    if rng.random() < 0.32:
        return 0
    return rng.randint(1, 4)


def build_generic_reviews(
    *, book_id: str, slug: str, start_id: int, start_date: datetime, bonus: int = 0
) -> list[Review]:
    """`bonus`: reseñas extra para libros populares (destacados o más vendidos), para que se note."""
    count = review_count_for(slug)
    if count == 0:
        return []
    count = min(count + bonus, 8)

    rng = random.Random(f"reviews:{slug}")
    names = rng.sample(REVIEWER_NAMES, k=min(count, len(REVIEWER_NAMES)))
    ratings = [rng.choices(*zip(*RATING_WEIGHTS, strict=True), k=1)[0] for _ in range(count)]

    reviews: list[Review] = []
    for i, (name, rating) in enumerate(zip(names, ratings, strict=True)):
        pool = COMMENTS_BY_RATING[rating]
        comment = pool[rng.randrange(len(pool))]
        reviews.append(
            Review(
                id=f"rv_{start_id + i:03d}",
                book_id=book_id,
                author_name=name,
                rating=rating,
                comment=comment,
                is_demo=True,
                created_at=start_date + timedelta(hours=rng.randint(0, 72 * 24), minutes=rng.randint(0, 59)),
            )
        )
    return reviews
