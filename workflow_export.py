from __future__ import annotations
import threading
from pathlib import Path
from typing import List
from tkinter import filedialog, messagebox
from combine_photos_core import ImageItem


class ExportWorkflowMixin:
    def combine_and_save(self) -> None:
        if not self.image_paths:
            messagebox.showwarning("No images", "Please add images first.")
            return

        basis = self.sort_basis.get()
        reverse = self.sort_direction.get() == "reverse chronological"
        items = self.current_items if self.current_items else self._build_sorted_items(list(self.image_paths), basis, reverse)
        if not items:
            messagebox.showwarning("No images", "No valid images are available to combine.")
            return

        selected_format = self.output_format.get()
        if selected_format == "PNG":
            output_ext = ".png"
            filetypes = [("PNG image", "*.png")]
        elif selected_format == "JPEG":
            output_ext = ".jpg"
            filetypes = [("JPEG image", "*.jpg;*.jpeg")]
        elif selected_format == "HEIC":
            output_ext = ".heic"
            filetypes = [("HEIC image", "*.heic")]
        elif selected_format in ("TIFF", "BIGTIFF"):
            output_ext = ".tif"
            filetypes = [("TIFF image", "*.tif;*.tiff")]
        else:
            output_ext = ".png"
            filetypes = [("Image file", "*.*")]

        output_path = filedialog.asksaveasfilename(
            title="Save combined image",
            defaultextension=output_ext,
            filetypes=filetypes,
            initialfile=f"combined_grid{output_ext}",
        )
        if not output_path:
            return

        self._reset_progress()
        self._start_busy("Preparing images...")
        threading.Thread(target=self._combine_worker, args=(items, Path(output_path)), daemon=True).start()

    def _combine_worker(self, items: List[ImageItem], output_path: Path) -> None:
        try:
            core_count = self._effective_worker_count(len(items))
            self._set_status(f"Preparing images using {core_count} core{'s' if core_count != 1 else ''}...")
            self._prepare_and_save([item.path for item in items], output_path)
            self.root.after(0, lambda p=str(output_path): (self._end_busy(f"Saved: {p}"), messagebox.showinfo("Done", f"Combined image saved to:\n{p}")))
        except Exception as exc:
            error_msg = str(exc)
            self.root.after(0, lambda msg=error_msg: (self._end_busy("Failed to combine images."), messagebox.showerror("Error", msg)))

    def _set_status(self, text: str) -> None:
        self.root.after(0, lambda: self.status_text.set(text))

    def _reset_progress(self) -> None:
        def _update() -> None:
            self._prep_target_progress = 0.0
            self._canvas_target_progress = 0.0
            self.prepare_progress.set(0.0)
            self._canvas_target_progress = 0.0
            self.prepare_percent_text.set("0.0%")
            self.canvas_percent_text.set("0.0%")
            self.progress_detail.set("Waiting to start.")
            self.layout_preview.set("")

        self.root.after(0, _update)

    def _set_prepare_progress(self, completed: int, total: int, workers: int) -> None:
        pct = 100.0 if total <= 0 else (completed / total) * 100.0
        detail = f"Prepared {completed}/{total} image(s) on {workers} core{'s' if workers != 1 else ''}."
        percent_text = f"{pct:.1f}%"

        def _update() -> None:
            self._prep_target_progress = pct
            self.prepare_percent_text.set(percent_text)
            self.progress_detail.set(detail)

        self.root.after(0, _update)

    def _set_canvas_progress(self, placed: int, total: int, width: int | None = None, height: int | None = None) -> None:
        pct = 100.0 if total <= 0 else (placed / total) * 100.0
        size_text = f" | canvas {width}x{height}" if width and height else ""
        detail = f"Added {placed}/{total} picture(s) to the giant canvas ({pct:.1f}%).{size_text}"
        percent_text = f"{pct:.1f}%"

        def _update() -> None:
            self._canvas_target_progress = pct
            self.canvas_percent_text.set(percent_text)
            self.progress_detail.set(detail)

        self.root.after(0, _update)
