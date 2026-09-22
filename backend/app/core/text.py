import re
import unicodedata


def slugify(text: str, max_len: int = 60) -> str:
    """'Cien años de soledad' -> 'cien-anos-de-soledad' (solo a-z, 0-9 y guiones)."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:max_len].rstrip("-")
