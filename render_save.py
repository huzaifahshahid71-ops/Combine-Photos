from __future__ import annotations
import os
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
from PIL import Image
from combine_photos_core import HEIF_AVAILABLE, TIFFFILE_AVAILABLE
try:
    import tifffile
except Exception:
    tifffile = None


class RenderSaveMixin:
    def _assemble_canvas_in_memory(self, prepared_info: List[Tuple[str, int, int]], mode: str) -> Image.Image:
        col_widths, row_heights, columns, rows, total_width, total_height = self._layout_from_prepared(prepared_info)
        if mode == "RGB":
            canvas = Image.new("RGB", (total_width, total_height), self._background_rgb())
        else:
            canvas = Image.new("RGBA", (total_width, total_height), self._background_color())
        self.root.after(0, lambda: self.layout_preview.set(
            f"Layout: {columns} columns × {rows} rows | output {total_width}x{total_height} px"
        ))
        self._set_canvas_progress(0, len(prepared_info), total_width, total_height)

        y = 0
        placed = 0
        for row in range(rows):
            x = 0
            for col in range(columns):
                idx = row * columns + col
                if idx >= len(prepared_info):
                    break
                prepared_path, _width, _height = prepared_info[idx]
                with Image.open(prepared_path) as img:
                    img.load()
                    if mode == "RGB":
                        if img.mode == "RGBA":
                            background = Image.new("RGB", img.size, self._background_rgb())
                            background.paste(img, mask=img.getchannel("A"))
                            canvas.paste(background, (x, y))
                            background.close()
                        else:
                            canvas.paste(img.convert("RGB"), (x, y))
                    else:
                        canvas.paste(img, (x, y), img if img.mode == "RGBA" else None)
                placed += 1
                self._set_canvas_progress(placed, len(prepared_info), total_width, total_height)
                x += col_widths[col]
            y += row_heights[row]
        return canvas

    def _save_standard_image(self, prepared_info: List[Tuple[str, int, int]], output_path: Path) -> None:
        col_widths, row_heights, columns, rows, total_width, total_height = self._layout_from_prepared(prepared_info)
        total_pixels = total_width * total_height
        self.root.after(0, lambda: self.layout_preview.set(
            f"Layout: {columns} columns × {rows} rows | output {total_width}x{total_height} px"
        ))

        if total_pixels > STANDARD_CANVAS_PIXEL_LIMIT and not self.allow_large_standard.get():
            raise RuntimeError(
                f"The final canvas is {total_width}x{total_height} ({total_pixels:,} pixels), which exceeds the normal in-memory PNG/JPEG threshold. "
                "Enable 'Allow very large PNG/JPEG in-memory builds' if you have enough RAM, or use TIFF/BIGTIFF."
            )

        if total_pixels > STANDARD_CANVAS_PIXEL_LIMIT:
            self._set_status(
                f"Attempting a very large {'JPEG' if self.output_format.get() == 'JPEG' else 'PNG'} build: {total_width}x{total_height} ({total_pixels:,} px)."
            )

        assemble_mode = "RGB" if self.output_format.get() == "JPEG" else "RGBA"
        canvas = self._assemble_canvas_in_memory(prepared_info, assemble_mode)
        width, height = canvas.size
        final_width, final_height, scale = self._enforce_standard_output_limit(width, height)
        if scale != 1.0:
            self._set_status(
                f"Final canvas is too large for PNG/JPEG ({width}x{height}). Resizing to {final_width}x{final_height}..."
            )
            resized = canvas.resize((final_width, final_height), Image.Resampling.LANCZOS)
            canvas.close()
            canvas = resized
            self.root.after(0, lambda: self.layout_preview.set(
                f"Layout: {columns} columns × {rows} rows | auto-fitted to {final_width}x{final_height} px"
            ))

        save_kwargs = {}
        if self.output_format.get() == "JPEG":
            if canvas.mode != "RGB":
                converted = canvas.convert("RGB")
                canvas.close()
                canvas = converted
            subsampling_map = {"4:4:4": 0, "4:2:2": 1, "4:2:0": 2}
            save_kwargs = {
                "quality": max(1, min(100, int(self.jpeg_quality.get()))),
                "optimize": bool(self.jpeg_optimize.get()),
                "subsampling": subsampling_map.get(self.jpeg_subsampling.get(), 2),
            }
        elif self.output_format.get() == "HEIC":
            if not HEIF_AVAILABLE:
                raise RuntimeError("HEIC output requires pillow-heif to be installed.")
            if canvas.mode != "RGB":
                converted = canvas.convert("RGB")
                canvas.close()
                canvas = converted
            save_kwargs = {"quality": max(1, min(100, int(self.heic_quality.get())))}

        canvas.save(output_path, **save_kwargs)
        canvas.close()
        self._set_canvas_progress(len(prepared_info), len(prepared_info), final_width, final_height)

    def _paste_image_to_array(self, dest: np.ndarray, img: Image.Image, x: int, y: int) -> None:
        rgba = img.convert("RGBA")
        arr = np.asarray(rgba, dtype=np.uint8)
        h, w = arr.shape[:2]

        alpha = arr[..., 3:4]
        if np.all(alpha == 255):
            dest[y:y+h, x:x+w, :] = arr[..., :3]
            return

        dest_region = dest[y:y+h, x:x+w, :].astype(np.uint16)
        src_rgb = arr[..., :3].astype(np.uint16)
        alpha_u16 = alpha.astype(np.uint16)
        inv_alpha = 255 - alpha_u16
        blended = (src_rgb * alpha_u16 + dest_region * inv_alpha + 127) // 255
        dest[y:y+h, x:x+w, :] = blended.astype(np.uint8)

    def _save_tiff_streaming(self, prepared_info: List[Tuple[str, int, int]], output_path: Path, force_bigtiff: bool) -> None:
        if not TIFFFILE_AVAILABLE:
            raise RuntimeError("tifffile is not installed, so TIFF/BIGTIFF export is unavailable.")

        col_widths, row_heights, columns, rows, total_width, total_height = self._layout_from_prepared(prepared_info)
        self.root.after(0, lambda: self.layout_preview.set(
            f"Layout: {columns} columns × {rows} rows | output {total_width}x{total_height} px"
        ))

        estimated_rgb_bytes = total_width * total_height * 3
        use_bigtiff = force_bigtiff or estimated_rgb_bytes >= (4 * 1024**3)
        compression = self.tiff_compression.get()

        self._set_status(
            f"Creating {'BigTIFF' if use_bigtiff else 'TIFF'} canvas on disk: {total_width}x{total_height}..."
        )

        temp_raw_path = output_path.with_suffix(output_path.suffix + ".raw_tmp.tif") if compression != "none" else output_path
        arr = tifffile.memmap(
            temp_raw_path,
            shape=(total_height, total_width, 3),
            dtype=np.uint8,
            photometric='rgb',
            bigtiff=use_bigtiff,
        )
        arr[:] = np.array(self._background_rgb(), dtype=np.uint8)
        self._set_canvas_progress(0, len(prepared_info), total_width, total_height)

        y = 0
        placed = 0
        for row in range(rows):
            x = 0
            for col in range(columns):
                idx = row * columns + col
                if idx >= len(prepared_info):
                    break
                prepared_path, _width, _height = prepared_info[idx]
                with Image.open(prepared_path) as img:
                    img.load()
                    self._paste_image_to_array(arr, img, x, y)
                placed += 1
                self._set_canvas_progress(placed, len(prepared_info), total_width, total_height)
                x += col_widths[col]
            y += row_heights[row]

        arr.flush()
        del arr

        if compression != "none":
            self._set_status(f"Applying TIFF compression: {compression}...")
            src = tifffile.memmap(temp_raw_path, mode="r")
            try:
                tifffile.imwrite(
                    output_path,
                    src,
                    photometric='rgb',
                    bigtiff=use_bigtiff,
                    compression=compression,
                )
            finally:
                del src
                try:
                    Path(temp_raw_path).unlink(missing_ok=True)
                except Exception:
                    pass

        self._set_canvas_progress(len(prepared_info), len(prepared_info), total_width, total_height)

    def _prepare_and_save(self, paths: List[Path], output_path: Path) -> None:
        with tempfile.TemporaryDirectory(prefix="combine_grid_") as temp_dir:
            prepared_info = self._prepare_images(paths, temp_dir)
            fmt = self.output_format.get()
            if fmt in ("PNG", "JPEG", "HEIC"):
                self._save_standard_image(prepared_info, output_path)
            elif fmt == "TIFF":
                self._save_tiff_streaming(prepared_info, output_path, force_bigtiff=False)
            elif fmt == "BIGTIFF":
                self._save_tiff_streaming(prepared_info, output_path, force_bigtiff=True)
            else:
                raise RuntimeError(f"Unsupported output format: {fmt}")
