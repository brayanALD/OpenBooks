import threading

# Candado del inventario. Lo comparten las compras (OrderService) y el panel de administración (AdminService):
# ambos hacen "leer libro -> cambiar -> guardar" sobre books.json, y sin un candado común una edición del
# administrador podría pisar el stock que acaba de descontar una compra (y vender de más).
# Como el almacenamiento JSON, solo vale para un proceso.
inventory_lock = threading.RLock()
