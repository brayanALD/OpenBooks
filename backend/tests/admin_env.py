"""Entorno del panel de administración: comparte repositorios con el checkout para probar que conviven."""

from dataclasses import dataclass

from app.domain.models import Author, Category
from app.repositories.memory_repo import InMemoryRepository
from app.schemas.admin import BookCreateIn
from app.services.admin_service import AdminService
from app.services.catalog_service import CatalogService
from tests.order_env import Env, build_env


@dataclass
class AdminEnv:
    env: Env
    admin: AdminService
    catalog: CatalogService
    authors: InMemoryRepository
    categories: InMemoryRepository


def build_admin_env() -> AdminEnv:
    env = build_env()
    authors = InMemoryRepository([Author(id="a1", name="Autora Uno", slug="autora-uno")])
    categories = InMemoryRepository(
        [
            Category(id="c1", name="Novela", slug="novela", position=0),
            Category(id="c2", name="Historia", slug="historia", position=1),
        ]
    )
    admin = AdminService(env.books, authors, categories, env.orders, env.auth._users)
    catalog = CatalogService(env.books, authors, categories, InMemoryRepository([]))
    return AdminEnv(env, admin, catalog, authors, categories)


def new_book(**overrides) -> BookCreateIn:
    data = dict(
        title="Un libro nuevo",
        isbn="978-958-04-1234-5",
        author_name="Autora Uno",
        category_ids=["c1"],
        price_cop=25_000,
        stock=10,
        publisher="Editorial Prueba",
        pages=200,
        description="Una descripción de prueba.",
    )
    data.update(overrides)
    return BookCreateIn(**data)
