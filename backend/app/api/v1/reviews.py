from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.deps import get_current_user, get_review_service
from app.domain.models import User
from app.schemas.catalog import ReviewOut
from app.schemas.reviews import MyReviewOut, ReviewIn
from app.services.review_service import ReviewError, ReviewService, to_out

# Se cuelga de /books/{slug}: el listado público de reseñas sigue en books.py.
router = APIRouter(prefix="/books/{slug}/reviews", tags=["reseñas"])

CurrentUser = Annotated[User, Depends(get_current_user)]
Reviews = Annotated[ReviewService, Depends(get_review_service)]

_STATUS = {"not_found": 404, "not_eligible": 403, "already_reviewed": 409}


def _fail(error: ReviewError) -> HTTPException:
    return HTTPException(_STATUS.get(error.code, 400), {"code": error.code, "message": error.message})


@router.get("/mine", response_model=MyReviewOut)
def my_status(slug: str, user: CurrentUser, reviews: Reviews) -> MyReviewOut:
    """¿Puede esta persona reseñar el libro? ¿Ya lo hizo?"""
    try:
        can_review, purchased, mine = reviews.status(user, slug)
    except ReviewError as error:
        raise _fail(error) from None
    return MyReviewOut(can_review=can_review, has_purchased=purchased, review=to_out(mine) if mine else None)


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(slug: str, body: ReviewIn, user: CurrentUser, reviews: Reviews) -> ReviewOut:
    try:
        return to_out(reviews.create(user, slug, body))
    except ReviewError as error:
        raise _fail(error) from None


@router.put("/mine", response_model=ReviewOut)
def update_review(slug: str, body: ReviewIn, user: CurrentUser, reviews: Reviews) -> ReviewOut:
    try:
        return to_out(reviews.update(user, slug, body))
    except ReviewError as error:
        raise _fail(error) from None


@router.delete("/mine", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(slug: str, user: CurrentUser, reviews: Reviews) -> Response:
    try:
        reviews.delete_mine(user, slug)
    except ReviewError as error:
        raise _fail(error) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
