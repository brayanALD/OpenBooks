import json

import pytest

from app.domain.models import Author
from app.repositories.json_repo import JsonRepository


@pytest.fixture
def repo(tmp_path):
    return JsonRepository(tmp_path / "authors.json", Author)


def author(id="a1", name="Jane Austen"):
    return Author(id=id, name=name, slug=name.lower().replace(" ", "-"))


def test_missing_file_is_an_empty_collection(repo):
    assert repo.list() == []
    assert repo.get("a1") is None


def test_add_get_list_roundtrip(repo):
    repo.add(author("a1", "Jane Austen"))
    repo.add(author("a2", "Fiódor Dostoyevski"))
    assert [a.id for a in repo.list()] == ["a1", "a2"]
    assert repo.get("a2").name == "Fiódor Dostoyevski"


def test_file_keeps_unicode_readable(repo, tmp_path):
    repo.add(author("a1", "Gabriel García Márquez"))
    assert "García Márquez" in (tmp_path / "authors.json").read_text(encoding="utf-8")


def test_add_duplicate_id_fails(repo):
    repo.add(author("a1"))
    with pytest.raises(ValueError):
        repo.add(author("a1", "Otro"))
    assert len(repo.list()) == 1


def test_update_replaces_and_unknown_id_fails(repo):
    repo.add(author("a1", "Jane Austen"))
    repo.update(author("a1", "Jane Austen (ed.)"))
    assert repo.get("a1").name == "Jane Austen (ed.)"
    with pytest.raises(KeyError):
        repo.update(author("nope"))


def test_delete(repo):
    repo.add(author("a1"))
    assert repo.delete("a1") is True
    assert repo.delete("a1") is False
    assert repo.list() == []


def test_write_is_atomic_and_leaves_no_temp_file(repo, tmp_path):
    repo.add(author("a1"))
    assert [p.name for p in tmp_path.iterdir()] == ["authors.json"]


def test_reads_see_external_changes(repo, tmp_path):
    repo.add(author("a1"))
    assert len(repo.list()) == 1  # llena la caché
    path = tmp_path / "authors.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    rows.append({"id": "a9", "name": "Editado a mano", "slug": "editado-a-mano"})
    path.write_text(json.dumps(rows), encoding="utf-8")
    # La caché se invalida por fecha de modificación; se fuerza un mtime distinto por si el reloj es grueso.
    import os

    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
    assert {a.id for a in repo.list()} == {"a1", "a9"}


def test_entities_are_immutable():
    a = author()
    with pytest.raises(Exception):
        a.name = "Cambiado"
