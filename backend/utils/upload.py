import os
import uuid
from config import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_VIDEO_EXTENSIONS, AVATAR_FOLDER, GOODS_FOLDER, VIDEOS_FOLDER, EMOJI_FOLDER, POSTS_FOLDER


def allowed_image(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def allowed_video(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def save_upload(file, subfolder: str) -> str | None:
    if not file or not file.filename or not allowed_image(file.filename):
        return None

    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    if subfolder == 'goods':
        target_dir = GOODS_FOLDER
    elif subfolder == 'avatars':
        target_dir = AVATAR_FOLDER
    elif subfolder == 'emojis':
        target_dir = EMOJI_FOLDER
    elif subfolder == 'posts':
        target_dir = POSTS_FOLDER
    else:
        return None

    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, unique_name)
    file.save(filepath)

    return f"/uploads/{subfolder}/{unique_name}"


def save_video(file) -> str | None:
    """Save a video file to uploads/videos/ with UUID name."""
    if not file or not file.filename or not allowed_video(file.filename):
        return None

    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    os.makedirs(VIDEOS_FOLDER, exist_ok=True)
    filepath = os.path.join(VIDEOS_FOLDER, unique_name)
    file.save(filepath)

    return f"/uploads/videos/{unique_name}"
