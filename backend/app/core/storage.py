import os
import uuid
import io
from pathlib import Path
from PIL import Image
from typing import Optional, Dict
from app.core.config import settings

class StorageManager:
    def __init__(self, root_dir: str = settings.STORAGE_LOCAL_ROOT):
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        # Ensure subdirectories exist
        for folder in ["selfies", "enrollments", "event_photos", "thumbnails", "recordings", "frames", "crops"]:
            (self.root / folder).mkdir(parents=True, exist_ok=True)

    def save_bytes(self, content: bytes, folder: str, extension: str = "jpg") -> str:
        filename = f"{uuid.uuid4().hex}.{extension.lstrip('.')}"
        rel_path = os.path.join(folder, filename)
        abs_path = self.root / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(content)
        # Return normalized forward-slash reference
        return rel_path.replace("\\", "/")

    def get_absolute_path(self, storage_ref: str) -> Path:
        clean_ref = storage_ref.replace("/", os.sep).replace("\\", os.sep)
        return self.root / clean_ref

    def read_bytes(self, storage_ref: str) -> Optional[bytes]:
        path = self.get_absolute_path(storage_ref)
        if not path.exists():
            return None
        with open(path, "rb") as f:
            return f.read()

    def delete_file(self, storage_ref: str) -> bool:
        path = self.get_absolute_path(storage_ref)
        if path.exists():
            try:
                path.unlink()
                return True
            except OSError:
                return False
        return False

    def create_thumbnail(self, image_bytes: bytes, max_size=(320, 320)) -> str:
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return self.save_bytes(buf.getvalue(), "thumbnails", "jpg")

    def create_crop(self, image_bytes: bytes, box: Dict[str, int], subfolder: str = "crops") -> str:
        img = Image.open(io.BytesIO(image_bytes))
        w_img, h_img = img.size
        
        x = max(0, min(box.get("x", 0), w_img - 1))
        y = max(0, min(box.get("y", 0), h_img - 1))
        bw = max(1, min(box.get("width", w_img - x), w_img - x))
        bh = max(1, min(box.get("height", h_img - y), h_img - y))
        
        cropped = img.crop((x, y, x + bw, y + bh))
        buf = io.BytesIO()
        cropped.save(buf, format="JPEG", quality=90)
        return self.save_bytes(buf.getvalue(), subfolder, "jpg")

storage_manager = StorageManager()
