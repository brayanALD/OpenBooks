from app.domain.rules import MAX_QUANTITY_PER_BOOK
from app.schemas.cart import CartIssue, CartItemIn, CartLineOut, CartOut
from app.services.catalog_service import CatalogService


def shipping_for(costs: list[int]) -> int:
    """Envío del pedido: un solo paquete, así que se cobra el envío más caro entre los libros.

    Regla de negocio provisional (el sitio original solo tenía envío por libro): es la única
    función a cambiar si se decide sumar los envíos o cobrar por unidad.
    """
    return max(costs, default=0)


class CartService:
    """Valida un carrito contra el catálogo. No guarda nada: el cliente conserva sus ids y cantidades
    y el servidor decide precios, stock y totales, sin fiarse de lo que envíe el navegador."""

    def __init__(self, catalog: CatalogService) -> None:
        self._catalog = catalog

    def validate(self, items: list[CartItemIn]) -> CartOut:
        requested: dict[str, int] = {}  # conserva el orden y une líneas repetidas
        for item in items:
            requested[item.book_id] = requested.get(item.book_id, 0) + item.quantity

        summaries = self._catalog.summaries_by_id(requested)
        unavailable = [book_id for book_id in requested if book_id not in summaries]

        lines: list[CartLineOut] = []
        for book_id, quantity in requested.items():
            book = summaries.get(book_id)
            if book is None:
                continue
            cap = min(book.stock, MAX_QUANTITY_PER_BOOK)
            accepted = min(quantity, cap)

            # El aviso indica qué límite se aplicó de verdad: con stock 20 y 25 pedidos manda el máximo por
            # pedido (10), no el stock; decir "quedan 20" sería falso.
            issue = None
            if book.stock == 0:
                issue = CartIssue.out_of_stock
            elif quantity > cap:
                issue = CartIssue.limited_stock if book.stock <= MAX_QUANTITY_PER_BOOK else CartIssue.quantity_capped

            lines.append(
                CartLineOut(
                    book=book,
                    requested_quantity=quantity,
                    quantity=accepted,
                    max_quantity=cap,
                    unit_price_cop=book.final_price_cop,
                    line_total_cop=book.final_price_cop * accepted,
                    issue=issue,
                )
            )

        buying = [line for line in lines if line.quantity > 0]
        subtotal = sum(line.line_total_cop for line in buying)
        shipping = shipping_for([line.book.shipping_cost_cop for line in buying])
        return CartOut(
            lines=lines,
            unavailable_ids=unavailable,
            item_count=sum(line.quantity for line in buying),
            subtotal_cop=subtotal,
            shipping_cop=shipping,
            total_cop=subtotal + shipping,
            has_issues=bool(unavailable) or any(line.issue for line in lines),
        )
