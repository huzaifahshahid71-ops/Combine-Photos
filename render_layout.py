from __future__ import annotations
import math
import os
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple
from PIL import Image
from combine_photos_core import PNG_JPEG_SIDE_LIMIT, STANDARD_CANVAS_PIXEL_LIMIT, _prepare_image_worker


class RenderLayoutMixin:
    def _background_color(self) -> Tuple[int, int, int, int]:
        if self.bg_color.get() == "black":
            return (0, 0, 0, 255)
        return (255, 255, 255, 255)

    def _background_rgb(self) -> Tuple[int, int, int]:
        bg = self._background_color()
        return bg[0], bg[1], bg[2]

    def _compute_columns(self, count: int) -> int:
        if self.columns_mode.get() == "manual":
            return max(1, int(self.columns_value.get()))
        return max(1, math.ceil(math.sqrt(count)))

    def _effective_worker_count(self, image_count: int) -> int:
        if not self.use_multicore.get() or image_count <= 1:
            return 1
        cpu_count = os.cpu_count() or 1
        return max(1, min(cpu_count, image_count))

    def _fit_size_within_limit(self, width: int, height: int) -> Tuple[int, int, float]:
        limit = max(1000, int(self.max_output_dimension.get()))
        longest_side = max(width, height)
        if longest_side <= limit:
            return width, height, 1.0
        scale = limit / float(longest_side)
        new_width = max(1, int(round(width * scale)))
        new_height = max(1, int(round(height * scale)))
        return new_width, new_height, scale

    def _layout_from_prepared(self, prepared_info: List[Tuple[str, int, int]]) -> Tuple[List[int], List[int], int, int, int, int]:
        columns = self._compute_columns(len(prepared_info))
        rows = math.ceil(len(prepared_info) / columns)
        row_heights = [0] * rows
        col_widths = [0] * columns

        for idx, (_path, width, height) in enumerate(prepared_info):
            row = idx // columns
            col = idx % columns
            col_widths[col] = max(col_widths[col], width)
            row_heights[row] = max(row_heights[row], height)

        total_width = sum(col_widths)
        total_height = sum(row_heights)
        return col_widths, row_heights, columns, rows, total_width, total_height

    def _enforce_standard_output_limit(self, width: int, height: int) -> Tuple[int, int, float]:
        max_dim = max(width, height)
        effective_limit = min(max(1000, int(self.max_output_dimension.get())), PNG_JPEG_SIDE_LIMIT)
        if max_dim <= effective_limit:
            return width, height, 1.0
        if not self.auto_limit_output.get():
            raise RuntimeError(
                f"Final image size is {width}x{height} pixels, which exceeds the supported PNG/JPEG maximum side length of {effective_limit}. "
                f"Enable auto-fit, increase columns, reduce width, or save as TIFF/BIGTIFF instead."
            )
        return self._fit_size_within_limit(width, height)

    def _prepare_images(self, paths: List[Path], temp_dir: str) -> List[Tuple[str, int, int]]:
        resize_mode = self.resize_mode.get()
        target_width = max(50, int(self.common_width.get()))
        target_height = max(16, int(self.custom_height.get()))
        custom_width = max(16, int(self.custom_width.get()))
        workers = self._effective_worker_count(len(paths))

        if resize_mode == "custom_resolution":
            target_width = custom_width
        tasks = [(idx, str(path), resize_mode, target_width, target_height, temp_dir) for idx, path in enumerate(paths)]
        results = [None] * len(tasks)

        if workers == 1:
            for idx, task in enumerate(tasks, start=1):
                try:
                    processed_index, prepared_path, width, height = _prepare_image_worker(task)
                    results[processed_index] = (prepared_path, width, height)
                except Exception as exc:
                    raise RuntimeError(
                        f"Image {idx} failed during preparation. Try disabling multi-core or remove the problematic file.\n{exc}"
                    ) from exc
                self._set_status(f"Processed {idx}/{len(tasks)} images on 1 core...")
                self._set_prepare_progress(idx, len(tasks), 1)
        else:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(_prepare_image_worker, task): task[0] for task in tasks}
                completed = 0
                for future in as_completed(futures):
                    try:
                        processed_index, prepared_path, width, height = future.result()
                    except Exception as exc:
                        raise RuntimeError(
                            "A source image failed during multi-core preparation. This is often caused by a damaged "
                            f"or partially downloaded image file. Try disabling multi-core or remove the problematic image.\n{exc}"
                        ) from exc
                    results[processed_index] = (prepared_path, width, height)
                    completed += 1
                    self._set_status(f"Processed {completed}/{len(tasks)} images on {workers} cores...")
                    self._set_prepare_progress(completed, len(tasks), workers)

        if any(result is None for result in results):
            raise RuntimeError("One or more images could not be prepared.")
        return results
