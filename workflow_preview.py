from __future__ import annotations
import math
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from PIL import Image
from combine_photos_core import ImageItem, EXIF_DATE_TAGS


class PreviewMixin:
    def _on_control_changed(self, _event=None) -> None:
        if self.scale_preset.get() == "1920x1080":
            self.custom_width.set(1920)
            self.custom_height.set(1080)
        elif self.scale_preset.get() == "1280x720":
            self.custom_width.set(1280)
            self.custom_height.set(720)
        self._on_layout_control_changed()
        if self.image_paths and not getattr(self, "_is_busy", False):
            self.refresh_preview()

    def _toggle_controls(self) -> None:
        columns_state = "normal" if self.columns_mode.get() == "manual" else "disabled"
        self.columns_spin.configure(state=columns_state)

        width_state = "normal" if self.resize_mode.get() == "common_width" else "disabled"
        self.width_spin.configure(state=width_state)

        custom_state = "normal" if self.resize_mode.get() == "custom_resolution" else "disabled"
        self.scale_preset_combo.configure(state=custom_state)
        self.custom_width_spin.configure(state=custom_state)
        self.custom_height_spin.configure(state=custom_state)
        self._update_layout_summary()

    def _on_layout_control_changed(self) -> None:
        if self.scale_preset.get() == "1920x1080":
            if self.custom_width.get() != 1920:
                self.custom_width.set(1920)
            if self.custom_height.get() != 1080:
                self.custom_height.set(1080)
        elif self.scale_preset.get() == "1280x720":
            if self.custom_width.get() != 1280:
                self.custom_width.set(1280)
            if self.custom_height.get() != 720:
                self.custom_height.set(720)
        self._toggle_controls()
        if self.current_items and not getattr(self, "_is_busy", False):
            self._update_layout_summary()

    def _update_layout_summary(self) -> None:
        total = len(self.current_items)
        if total <= 0:
            self.quick_layout_label.configure(text="Auto")
            self.layout_preview.set("")
            return
        columns_value = self._compute_columns(total)
        rows_value = math.ceil(total / columns_value) if columns_value else 0
        self.quick_layout_label.configure(text=f"{columns_value} × {rows_value}" if columns_value else "Auto")
        if self.resize_mode.get() == "original_size":
            mode_label = "original size"
        elif self.resize_mode.get() == "custom_resolution":
            mode_label = f"custom {self.custom_width.get()}x{self.custom_height.get()}"
        else:
            mode_label = f"common width {self.common_width.get()} px"
        self.layout_preview.set(f"Planned layout: {columns_value} columns × {rows_value} rows | sizing: {mode_label} | format: {self.output_format.get()} | order: {self.sort_direction.get()}")

    def refresh_preview(self) -> None:
        self._toggle_controls()
        paths = list(self.image_paths)
        if not paths:
            self.current_items.clear()
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.count_label.configure(text="0")
            self._end_busy("Add images to begin.")
            self.layout_preview.set("")
            return

        self._preview_job_id += 1
        job_id = self._preview_job_id
        basis = self.sort_basis.get()
        reverse = self.sort_direction.get() == "reverse chronological"

        self._start_busy(f"Scanning and sorting {len(paths)} image(s)...")
        self.progress_detail.set("Reading image dates for preview...")
        self.prepare_progress.set(0.0)
        self.prepare_percent_text.set("0.0%")
        self._canvas_target_progress = 0.0
        self.canvas_percent_text.set("0.0%")

        threading.Thread(
            target=self._refresh_preview_worker,
            args=(job_id, paths, basis, reverse),
            daemon=True,
        ).start()

    def _refresh_preview_worker(self, job_id: int, paths: List[Path], basis: str, reverse: bool) -> None:
        try:
            items = self._build_sorted_items(paths, basis, reverse, preview_job_id=job_id)
            self.root.after(0, lambda: self._apply_preview_results(job_id, items))
        except Exception as exc:
            error_msg = str(exc)
            self.root.after(0, lambda msg=error_msg, jid=job_id: self._handle_preview_error(jid, msg))

    def _apply_preview_results(self, job_id: int, items: List[ImageItem]) -> None:
        if job_id != self._preview_job_id:
            return

        self.current_items = items
        self._tree_insert_job_id += 1
        tree_job_id = self._tree_insert_job_id

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.count_label.configure(text=str(len(self.current_items)))
        self._prep_target_progress = 100.0 if self.current_items else 0.0
        self.prepare_percent_text.set("100.0%" if self.current_items else "0.0%")
        self.progress_detail.set(f"Rendering preview list ({self.sort_direction.get()})...")
        self.layout_preview.set("")
        columns_value = self._compute_columns(len(self.current_items)) if self.current_items else 0
        rows_value = math.ceil(len(self.current_items) / columns_value) if columns_value else 0
        self.quick_layout_label.configure(text=f"{columns_value} × {rows_value}" if columns_value else "Auto")

        if not self.current_items:
            self._end_busy("Add images to begin.")
            return

        self._populate_treeview_in_batches(job_id, tree_job_id, start_index=0)

    def _populate_treeview_in_batches(self, preview_job_id: int, tree_job_id: int, start_index: int) -> None:
        if preview_job_id != self._preview_job_id or tree_job_id != self._tree_insert_job_id:
            return

        batch_size = 200
        end_index = min(start_index + batch_size, len(self.current_items))

        for idx in range(start_index, end_index):
            item = self.current_items[idx]
            self.tree.insert(
                "",
                "end",
                values=(idx + 1, item.display_name, item.sort_datetime.strftime("%Y-%m-%d %H:%M:%S")),
            )

        total = len(self.current_items)
        pct = 100.0 if total <= 0 else (end_index / total) * 100.0
        self.progress_detail.set(f"Rendering preview list... {end_index}/{total}")
        self._canvas_target_progress = pct
        self.canvas_percent_text.set(f"{pct:.1f}%")

        if end_index < total:
            self.root.after(1, lambda: self._populate_treeview_in_batches(preview_job_id, tree_job_id, end_index))
            return

        self._canvas_target_progress = 0.0
        self.canvas_percent_text.set("0.0%")
        self.progress_detail.set("Preview order ready.")
        self._end_busy("Preview updated.")

    def _handle_preview_error(self, job_id: int, error: object) -> None:
        if job_id != self._preview_job_id:
            return
        self._end_busy("Failed to refresh preview.")
        self.progress_detail.set(str(error))

    def _build_sorted_items(
        self,
        paths: List[Path],
        basis: str,
        reverse: bool,
        preview_job_id: Optional[int] = None,
    ) -> List[ImageItem]:
        items: List[ImageItem] = []
        total = len(paths)

        for idx, path in enumerate(paths, start=1):
            sort_dt = self._get_sort_datetime(path, basis)
            items.append(ImageItem(path=path, sort_datetime=sort_dt, display_name=path.name))

            if preview_job_id is not None and (idx % 10 == 0 or idx == total):
                if preview_job_id != self._preview_job_id:
                    return []
                pct = 100.0 if total <= 0 else (idx / total) * 100.0

                def _update_preview_progress(p: float = pct, i: int = idx, t: int = total) -> None:
                    self.prepare_progress.set(p)
                    self.prepare_percent_text.set(f"{p:.1f}%")
                    self.progress_detail.set(f"Scanned {i}/{t} image(s) for preview...")

                self.root.after(0, _update_preview_progress)

        def _natural_name_key(name: str):
            parts = []
            current = ""
            is_digit = None
            for ch in name.lower():
                ch_is_digit = ch.isdigit()
                if is_digit is None or ch_is_digit == is_digit:
                    current += ch
                else:
                    parts.append(int(current) if is_digit else current)
                    current = ch
                is_digit = ch_is_digit
            if current:
                parts.append(int(current) if is_digit else current)
            return tuple(parts)

        if basis == "filename":
            items.sort(key=lambda x: _natural_name_key(x.display_name), reverse=reverse)
        else:
            items.sort(key=lambda x: (x.sort_datetime, _natural_name_key(x.display_name)), reverse=reverse)
        return items

    def _get_sort_datetime(self, path: Path, basis: str) -> datetime:
        if basis == "filename":
            ts = path.stat().st_mtime
            return datetime.fromtimestamp(ts)

        if basis == "modified":
            ts = path.stat().st_mtime
            return datetime.fromtimestamp(ts)

        captured = self._read_capture_time(path)
        if captured is not None:
            return captured

        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts)

    def _read_capture_time(self, path: Path) -> Optional[datetime]:
        try:
            with Image.open(path) as img:
                img.load()
                exif = None
                getexif = getattr(img, "getexif", None)
                if callable(getexif):
                    exif = getexif()
                if exif:
                    for tag in EXIF_DATE_TAGS:
                        value = exif.get(tag)
                        if value:
                            parsed = self._parse_exif_datetime(value)
                            if parsed:
                                return parsed
        except Exception:
            return None
        return None

    @staticmethod
    def _parse_exif_datetime(value: str) -> Optional[datetime]:
        try:
            return datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
        except Exception:
            return None
