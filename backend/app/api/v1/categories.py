from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_catalog_service
from app.schemas.catalog import CategoryOut
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/categories", tags=["categorías"])

Catalog = Annotated[CatalogService, Depends(get_catalog_service)]


@router.get("", response_model=list[CategoryOut])
def list_categories(catalog: Catalog) -> list[CategoryOut]:
    return catalog.list_categories()


@router.get("/{slug}", response_model=CategoryOut)
def get_category(slug: str, catalog: Catalog) -> CategoryOut:
    category = catalog.get_category(slug)
    if category is None:
        raise HTTPException(404, "Categoría no encontrada")
    return category
