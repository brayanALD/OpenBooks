import threading
from pathlib import Path

_registry_guard = threading.Lock()
_locks: dict[Path, threading.RLock] = {}


def lock_for(path: Path) -> threading.RLock:
    """Un candado por archivo. Protege lecturas-modificaciones-escrituras dentro de un proceso.

    No coordina varios procesos (p. ej. varios workers de uvicorn): el almacenamiento JSON
    está pensado para un único proceso local.
    """
    key = path.resolve()
    with _registry_guard:
        return _locks.setdefault(key, threading.RLock())
