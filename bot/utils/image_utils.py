import io

from PIL import Image


def compress_image(img_bytes: bytes, max_size: int = 1024) -> bytes:
    img = Image.open(io.BytesIO(img_bytes))
    img = img.convert("RGB")
    w, h = img.size
    if w > max_size or h > max_size:
        ratio = max_size / max(w, h)
        new_w = int(w * ratio)
        new_h = int(h * ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()
