"""Saving and deleting uploaded shelter photos."""
import os
import uuid

from flask import current_app

# File signatures ("magic bytes"), so a renamed non-image is rejected.
_SIGNATURES = {
    b"\xff\xd8\xff": ".jpg",
    b"\x89PNG\r\n\x1a\n": ".png",
}


def _detect_extension(head):
    for sig, ext in _SIGNATURES.items():
        if head.startswith(sig):
            return ext
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp"
    return None


def save_photo(file_storage):
    """Save an uploaded image. Returns the stored filename, or None if it isn't a real image."""
    head = file_storage.stream.read(16)
    file_storage.stream.seek(0)
    ext = _detect_extension(head)
    if ext is None:
        return None
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    filename = uuid.uuid4().hex + ext  # random name; never trust the uploaded filename
    file_storage.save(os.path.join(folder, filename))
    return filename


def delete_photo(filename):
    if not filename:
        return
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(filename))
    if os.path.exists(path):
        os.remove(path)
