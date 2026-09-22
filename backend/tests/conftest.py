from datetime import datetime, timedelta, timezone

import pytest

from app.config import settings
from app.core import deps
from app.domain.models import Author, Book, Category, Review
from app.repositories.memory_repo import InMemoryRepository
from app.services.catalog_service import CatalogService
from scripts.catalog_rules import isbn_for

NOW = datetime(2025, 1, 1, tzinfo=timezone.utc)


def make_book(id: str, title: str, author_id: str, category_ids: list[str], **overrides) -> Book:
    fields = dict(
        id=id,
        slug=title.lower().replace(" ", "-"),
        title=title,
        isbn=isbn_for(id, None),
        author_id=author_id,
        category_ids=category_ids,
        price_cop=50_000,
        stock=10,
        cover=f"/covers/{id}.webp",
        cover_width=240,
        cover_height=360,
        created_at=NOW,
    )
    fields.update(overrides)
    return Book(**fields)


@pytest.fixture
def catalog() -> CatalogService:
    """Catálogo pequeño y controlado, en memoria."""
    authors = [
        Author(id="a1", name="Gabriel García Márquez", slug="gabriel-garcia-marquez"),
        Author(id="a2", name="Jane Austen", slug="jane-austen"),
        Author(id="a3", name="Brandon Sanderson", slug="brandon-sanderson"),
    ]
    categories = [
        Category(id="c1", name="Clásicos", slug="clasicos", position=0),
        Category(id="c2", name="Fantasía", slug="fantasia", position=1),
        Category(id="c3", name="Novela", slug="novela", position=2),
    ]
    books = [
        make_book("b1", "Cien años de soledad", "a1", ["c3", "c1"], price_cop=70_000, bestseller=True),
        make_book("b2", "En agosto nos vemos", "a1", ["c3"], price_cop=50_000, stock=0),
        make_book("b3", "Orgullo y prejuicio", "a2", ["c1"], price_cop=40_000, featured=True),
        make_book(
            "b4", "Nacidos de la bruma", "a3", ["c2"],
            price_cop=100_000, discount_pct=20, shipping_cost_cop=5_000,
            description="Una saga de magia y rebelión.",
        ),
    ]
    reviews = [
        Review(id="r1", book_id="b1", author_name="Ana", rating=5, comment="Genial", created_at=NOW),
        Review(id="r2", book_id="b1", author_name="Beto", rating=4, comment="Muy bueno", created_at=NOW + timedelta(days=1)),
        Review(id="r3", book_id="b3", author_name="Cami", rating=3, comment="Bien", created_at=NOW),
    ]
    return CatalogService(
        InMemoryRepository(books),
        InMemoryRepository(authors),
        InMemoryRepository(categories),
        InMemoryRepository(reviews),
    )


def _clear_service_caches() -> None:
    """Los servicios de `deps` se crean una vez por proceso con la carpeta de datos de ese momento."""
    for factory in (
        deps.get_catalog_service,
        deps.get_auth_service,
        deps.get_cart_storage,
        deps.get_order_service,
        deps.get_admin_service,
        deps.get_review_service,
        deps.get_wishlist_service,
    ):
        factory.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def seed_data_dir(tmp_path_factory):
    """Toda la suite trabaja con un catálogo recién importado en una carpeta temporal.

    Así los tests no dependen de `backend/data` (que cambia al vender, al editar desde el panel o al
    subir portadas) ni escriben en ella: users.json, orders.json y media/ de las pruebas quedan en la carpeta temporal.
    """
    import scripts.import_legacy as importer

    tmp = tmp_path_factory.mktemp("catalogo")
    original_dir, original_covers, original_report = settings.data_dir, importer.COVERS_DIR, importer.REPORT_PATH
    settings.data_dir = tmp
    importer.COVERS_DIR = tmp / "covers"
    importer.REPORT_PATH = tmp / "import_report.md"
    _clear_service_caches()
    assert importer.main(force=True) == 0

    yield tmp

    settings.data_dir, importer.COVERS_DIR, importer.REPORT_PATH = original_dir, original_covers, original_report
    _clear_service_caches()
