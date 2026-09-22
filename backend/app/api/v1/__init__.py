from fastapi import APIRouter

from app.api.v1 import admin, auth, books, cart, categories, media, orders, reviews, wishlist

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(admin.router)
api_router.include_router(reviews.router)
api_router.include_router(media.router)
api_router.include_router(auth.router)
api_router.include_router(orders.router)
api_router.include_router(books.router)
api_router.include_router(categories.router)
api_router.include_router(cart.router)
api_router.include_router(wishlist.router)
