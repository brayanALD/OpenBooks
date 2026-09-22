import io

import pytest
from PIL import Image

from app.core.images import MAX_HEIGHT, MAX_UPLOAD_BYTES, InvalidImage, open_upload, save_cover


def image_bytes(fmt: str, size=(300, 450), mode="RGB", **save_kwargs) -> bytes:
    buffer = io.BytesIO()
    Image.new(mode, size, "#754c24" if mode in ("RGB", "RGBA", "CMYK") else 5).save(buffer, fmt, **save_kwargs)
    return buffer.getvalue()


@pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP"])
def test_accepted_formats(fmt):
    assert open_upload(image_bytes(fmt)).size == (300, 450)


def test_cmyk_jpeg_and_palette_png_are_accepted_and_saved(tmp_path):
    cmyk = open_upload(image_bytes("JPEG", mode="CMYK"))
    palette = open_upload(image_bytes("PNG", mode="P"))
    for name, image in (("cmyk.webp", cmyk), ("palette.webp", palette)):
        width, height, _ = save_cover(image, tmp_path / name)
        assert (tmp_path / name).is_file() and (width, height) == (300, 450)


@pytest.mark.parametrize(
    "data, message",
    [
        pytest.param(b"esto no es una imagen", "no es una imagen", id="texto plano"),
        pytest.param(b"", "no es una imagen", id="vacío"),
        pytest.param(b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>", "no es una imagen", id="svg con script"),
        pytest.param(image_bytes("GIF"), "Formato no admitido", id="gif"),
        pytest.param(image_bytes("BMP"), "Formato no admitido", id="bmp"),
        pytest.param(image_bytes("PNG")[:200], "dañada", id="png truncado"),
    ],
)
def test_rejected_uploads(data, message):
    with pytest.raises(InvalidImage, match=message):
        open_upload(data)


def test_oversized_file_is_rejected_before_decoding():
    with pytest.raises(InvalidImage, match="5 MB"):
        open_upload(b"\x00" * (MAX_UPLOAD_BYTES + 1))


def test_pixel_bomb_is_rejected():
    """Un PNG uniforme pesa muy poco pero ocuparía cientos de MB al decodificarse."""
    data = image_bytes("PNG", size=(7000, 7000))
    assert len(data) < MAX_UPLOAD_BYTES
    with pytest.raises(InvalidImage, match="demasiados píxeles"):
        open_upload(data)


def test_tall_images_are_scaled_down_keeping_proportions(tmp_path):
    width, height, blur = save_cover(open_upload(image_bytes("PNG", size=(1000, 2000))), tmp_path / "a.webp")
    assert (width, height) == (400, MAX_HEIGHT) and blur.startswith("data:image/webp;base64,")
    with Image.open(tmp_path / "a.webp") as saved:
        assert saved.format == "WEBP" and saved.size == (400, MAX_HEIGHT)


def test_small_images_are_never_enlarged(tmp_path):
    assert save_cover(open_upload(image_bytes("PNG", size=(120, 180))), tmp_path / "b.webp")[:2] == (120, 180)


def test_real_transparency_survives(tmp_path):
    source = Image.new("RGBA", (300, 450), "#754c24")
    source.putpixel((0, 0), (0, 0, 0, 0))  # una esquina realmente transparente (un PNG opaco pierde el alfa: es correcto)
    buffer = io.BytesIO()
    source.save(buffer, "PNG")
    save_cover(open_upload(buffer.getvalue()), tmp_path / "c.webp")
    with Image.open(tmp_path / "c.webp") as saved:
        assert saved.mode == "RGBA" and saved.getpixel((0, 0))[3] == 0
