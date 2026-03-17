import os

from .ui import IMAGE_EXTS


def size_str(path: str) -> str:
    size = os.path.getsize(path)
    return f"{size / 1024:.1f}KB" if size >= 1024 else f"{size}B"


def is_image(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in IMAGE_EXTS


def load_attachment(path: str) -> dict:
    """Lê um arquivo e retorna um dict de anexo sem side-effects de UI."""
    if is_image(path):
        return {"type": "image", "path": path}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"type": "text", "path": path, "content": content}


def build_message(text: str, attachments: list[dict]) -> dict:
    parts = []
    images = []

    for att in attachments:
        if att["type"] == "image":
            images.append(att["path"])
        else:
            parts.append(f"[{os.path.basename(att['path'])}]\n{att['content']}")

    if parts:
        parts.append(text)
        content = "\n\n".join(parts)
    else:
        content = text

    msg = {"role": "user", "content": content}
    if images:
        msg["images"] = images
    return msg
