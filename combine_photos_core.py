from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageOps, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None

try:
    import pillow_heif  # type: ignore
    pillow_heif.register_heif_opener()
    HEIF_AVAILABLE = True
except Exception:
    HEIF_AVAILABLE = False

try:
    import tifffile  # type: ignore
    TIFFFILE_AVAILABLE = True
except Exception:
    TIFFFILE_AVAILABLE = False

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif",
    ".heic", ".heif"
}
EXIF_DATE_TAGS = [36867, 36868, 306]
PNG_JPEG_SIDE_LIMIT = 65500
STANDARD_CANVAS_PIXEL_LIMIT = 1_600_000_000


@dataclass
class ImageItem:
    path: Path
    sort_datetime: datetime
    display_name: str


def _prepare_image_worker(task: Tuple[int, str, str, int, int, str]) -> Tuple[int, str, int, int]:
    index, input_path, resize_mode, target_width, target_height, temp_dir = task
    try:
        if HEIF_AVAILABLE:
            try:
                import pillow_heif  # type: ignore
                pillow_heif.register_heif_opener()
            except Exception:
                pass

        with Image.open(input_path) as img:
            img.load()
            img = ImageOps.exif_transpose(img)
            img.load()
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")
            else:
                img = img.copy()

            if resize_mode == "common_width":
                w, h = img.size
                if w <= 0 or h <= 0:
                    raise ValueError(f"Invalid image size for {input_path}")
                new_h = max(1, round((target_width / w) * h))
                img = img.resize((target_width, new_h), Image.Resampling.LANCZOS)
            elif resize_mode == "custom_resolution":
                if target_width <= 0 or target_height <= 0:
                    raise ValueError(f"Invalid custom resolution {target_width}x{target_height}")
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

            output_path = os.path.join(temp_dir, f"prepared_{index:06d}.png")
            img.save(output_path, format="PNG", compress_level=1)
            width, height = img.size
            img.close()
            return index, output_path, width, height
    except Exception as exc:
        raise RuntimeError(f"Failed to process image '{input_path}': {exc}") from exc
