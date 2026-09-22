import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Generic

from app.core.file_lock import lock_for
from app.repositories.base import Repository, T


class JsonRepository(Repository[T], Generic[T]):
    """Una colección = un archivo JSON con una lista de objetos.

    - Escritura atómica: se escribe a un temporal y se reemplaza con `os.replace`, así un fallo
      a mitad de escritura nunca deja el archivo a medias.
    - Lectura con caché por fecha de modificación: se relee solo si el archivo cambió.
    - Un archivo que no existe equivale a una colección vacía.
    """

    def __init__(self, path: Path, model: type[T]) -> None:
        self._path = path
        self._model = model
        self._lock = lock_for(path)
        self._cache: tuple[int, list[T]] | None = None

    # -- lectura ---------------------------------------------------------------------------

    def _read(self) -> list[T]:
        with self._lock:
            try:
                mtime = self._path.stat().st_mtime_ns
            except FileNotFoundError:
                return []
            if self._cache and self._cache[0] == mtime:
                return self._cache[1]
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            items = [self._model.model_validate(row) for row in raw]
            self._cache = (mtime, items)
            return items

    def list(self) -> list[T]:
        return list(self._read())

    def get(self, id: str) -> T | None:
        return next((i for i in self._read() if i.id == id), None)

    # -- escritura -------------------------------------------------------------------------

    # `Sequence` y no `list[T]`: este método se define después de `def list`, que ocultaría el tipo.
    def _write(self, items: Sequence[T]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            [i.model_dump(mode="json") for i in items], ensure_ascii=False, indent=2
        )
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self._path)
        self._cache = None

    def add(self, item: T) -> T:
        with self._lock:
            items = self._read()
            if any(i.id == item.id for i in items):
                raise ValueError(f"Ya existe un registro con id {item.id!r}")
            self._write([*items, item])
            return item

    def update(self, item: T) -> T:
        with self._lock:
            items = self._read()
            if not any(i.id == item.id for i in items):
                raise KeyError(item.id)
            self._write([item if i.id == item.id else i for i in items])
            return item

    def delete(self, id: str) -> bool:
        with self._lock:
            items = self._read()
            kept = [i for i in items if i.id != id]
            if len(kept) == len(items):
                return False
            self._write(kept)
            return True
