from __future__ import annotations
import os
import threading
from pathlib import Path
from typing import List
from tkinter import filedialog, messagebox
from combine_photos_core import SUPPORTED_EXTENSIONS


class LibraryMixin:
    def _set_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for widget in [
            getattr(self, "add_images_btn", None),
            getattr(self, "add_folder_btn", None),
            getattr(self, "clear_btn", None),
            getattr(self, "remove_btn", None),
            getattr(self, "build_top_btn", None),
            getattr(self, "build_bottom_btn", None),
            getattr(self, "refresh_btn", None),
        ]:
            if widget is not None:
                try:
                    widget.configure(state=state)
                except Exception:
                    pass

    def _start_busy(self, message: str) -> None:
        self._is_busy = True
        self.status_text.set(message)
        self.status_badge_text.set("Working")
        try:
            self.status_badge.configure(text="Working", fg_color=("#4F46E5", "#4F46E5"))
        except Exception:
            pass
        self._set_controls_enabled(False)

    def _end_busy(self, message: str | None = None) -> None:
        self._is_busy = False
        self._set_controls_enabled(True)
        self.status_badge_text.set("Ready")
        try:
            self.status_badge.configure(text="Ready", fg_color=("#16A34A", "#15803D"))
        except Exception:
            pass
        if message is not None:
            self.status_text.set(message)

    def add_images(self) -> None:
        filetypes = [
            (
                "Image files",
                "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.gif *.heic *.heif",
            ),
            ("All files", "*.*"),
        ]
        paths = filedialog.askopenfilenames(title="Select images", filetypes=filetypes)
        if not paths:
            return
        self._append_paths([Path(p) for p in paths])

    def add_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select folder with images")
        if not folder:
            return
        self._folder_job_id += 1
        job_id = self._folder_job_id
        self.prepare_progress.set(0.0)
        self.prepare_percent_text.set("0.0%")
        self._canvas_target_progress = 0.0
        self.canvas_percent_text.set("0.0%")
        self.progress_detail.set("Scanning selected folder for supported images...")
        self._start_busy("Reading folder contents...")
        threading.Thread(
            target=self._scan_folder_worker,
            args=(job_id, Path(folder)),
            daemon=True,
        ).start()

    def _scan_folder_worker(self, job_id: int, folder: Path) -> None:
        try:
            entries: list[Path] = []
            all_items = list(os.scandir(folder))
            total = len(all_items)
            for idx, entry in enumerate(all_items, start=1):
                if entry.is_file():
                    p = Path(entry.path)
                    if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                        entries.append(p)
                if idx % 100 == 0 or idx == total:
                    pct = 100.0 if total <= 0 else (idx / total) * 100.0

                    def _update_scan_progress(p: float = pct, i: int = idx, t: int = total) -> None:
                        self._prep_target_progress = p
                        self.prepare_percent_text.set(f"{p:.1f}%")
                        self.progress_detail.set(f"Scanned {i}/{t} folder item(s)...")

                    self.root.after(0, _update_scan_progress)
            self.root.after(0, lambda jid=job_id, found=entries: self._finish_add_folder(jid, found))
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda jid=job_id, error_msg=msg: self._finish_add_folder_error(jid, error_msg))

    def _finish_add_folder(self, job_id: int, found: List[Path]) -> None:
        if job_id != self._folder_job_id:
            return
        self._end_busy()
        self._append_paths(found)

    def _finish_add_folder_error(self, job_id: int, error_msg: str) -> None:
        if job_id != self._folder_job_id:
            return
        self._end_busy("Failed to read folder.")
        self.progress_detail.set(error_msg)
        messagebox.showerror("Error", error_msg)

    def _append_paths(self, new_paths: List[Path]) -> None:
        existing = {p.resolve() for p in self.image_paths}
        added = 0
        for p in new_paths:
            try:
                rp = p.resolve()
            except Exception:
                rp = p
            if rp not in existing and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                self.image_paths.append(p)
                existing.add(rp)
                added += 1

        if added == 0:
            self.status_text.set("No new supported images were added.")
            return

        self.status_text.set(f"Added {added} image(s).")
        self.refresh_preview()

    def clear_images(self) -> None:
        self.image_paths.clear()
        self.current_items.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.count_label.configure(text="0")
        self.layout_preview.set("")
        self.quick_layout_label.configure(text="Auto")
        self.prepare_progress.set(0.0)
        self._canvas_target_progress = 0.0
        self.prepare_percent_text.set("0.0%")
        self.canvas_percent_text.set("0.0%")
        self.progress_detail.set("Waiting to start.")
        self.status_text.set("Cleared image list.")

    def remove_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        indices = sorted((int(self.tree.item(item, "values")[0]) - 1 for item in selected), reverse=True)
        if not self.current_items:
            return
        current_sorted_paths = [item.path for item in self.current_items]
        remove_paths = {current_sorted_paths[i] for i in indices if 0 <= i < len(current_sorted_paths)}
        self.image_paths = [p for p in self.image_paths if p not in remove_paths]
        self.refresh_preview()
        self.status_text.set(f"Removed {len(remove_paths)} image(s).")
