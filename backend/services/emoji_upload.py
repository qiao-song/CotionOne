import os
import uuid
from config import EMOJI_FOLDER


def save_emoji(file, filename: str) -> str | None:
    """Save an emoji image to uploads/emojis/ with UUID name."""
    if not file or not file.filename:
        return None

    from utils.upload import allowed_image
    if not allowed_image(file.filename):
        return None

    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    os.makedirs(EMOJI_FOLDER, exist_ok=True)
    filepath = os.path.join(EMOJI_FOLDER, unique_name)
    file.save(filepath)

    return f"/uploads/emojis/{unique_name}"
