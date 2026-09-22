from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.catalog import ReviewOut

Text = Annotated[str, StringConstraints(strip_whitespace=True)]


class ReviewIn(BaseModel):
    rating: Annotated[int, Field(ge=1, le=5)]
    comment: Annotated[Text, Field(min_length=10, max_length=2000)]


class MyReviewOut(BaseModel):
    """Situación de la persona con sesión frente a un libro: si puede reseñarlo y su reseña, si ya la escribió."""

    can_review: bool  # compró el libro y aún no lo reseñó
    has_purchased: bool
    review: ReviewOut | None
