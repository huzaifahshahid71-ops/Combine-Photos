from __future__ import annotations
import sys
from pathlib import Path
from typing import List
import tkinter as tk
from tkinter import ttk

try:
    import customtkinter as ctk
except ImportError as exc:
    raise SystemExit("customtkinter is required. Run BUILD_APP.bat or: pip install customtkinter") from exc

from combine_photos_backend import BackendMixin
from combine_photos_core import HEIF_AVAILABLE, TIFFFILE_AVAILABLE, ImageItem
from ui_composer import ComposerMixin
from ui_secondary import SecondaryPagesMixin

APP_TITLE = "Combine Photos Studio"
APP_VERSION = "1.0"
APP_USER_MODEL_ID = "CombinePhotosStudio.Windows.1.0"


def safe_resource_path(name: str) -> Path | None:
    try:
        root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        p = root / name
        return p if p.exists() else None
    except Exception:
        return None


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")


class ImageCombinerApp(ctk.CTk, ComposerMixin, SecondaryPagesMixin, BackendMixin):
    def __init__(self) -> None:
        super().__init__()
        self.root = self
        self.title(APP_TITLE)
        self.geometry("1480x920")
        self.minsize(1180, 760)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._apply_windows_identity()
        self._apply_icon()
        self.after(300, self._apply_icon)

        self.image_paths: List[Path] = []
        self.current_items: List[ImageItem] = []
        self._preview_job_id = 0
        self._folder_job_id = 0
        self._tree_insert_job_id = 0
        self._is_busy = False

        self.sort_basis = tk.StringVar(value="filename")
        self.sort_direction = tk.StringVar(value="chronological")
        self.columns_mode = tk.StringVar(value="auto")
        self.columns_value = tk.IntVar(value=3)
        self.resize_mode = tk.StringVar(value="common_width")
        self.common_width = tk.IntVar(value=430)
        self.bg_color = tk.StringVar(value="white")
        self.output_format = tk.StringVar(value="PNG")
        self.jpeg_quality = tk.IntVar(value=92)
        self.jpeg_optimize = tk.BooleanVar(value=True)
        self.jpeg_subsampling = tk.StringVar(value="4:2:0")
        self.tiff_compression = tk.StringVar(value="none")
        self.heic_quality = tk.IntVar(value=90)
        self.scale_preset = tk.StringVar(value="None")
        self.custom_width = tk.IntVar(value=1280)
        self.custom_height = tk.IntVar(value=720)
        self.use_multicore = tk.BooleanVar(value=True)
        self.auto_limit_output = tk.BooleanVar(value=True)
        self.allow_large_standard = tk.BooleanVar(value=True)
        self.max_output_dimension = tk.IntVar(value=65000)

        self.status_text = tk.StringVar(value="Add images or a folder to begin.")
        self.prepare_progress = tk.DoubleVar(value=0.0)
        self.canvas_progress = tk.DoubleVar(value=0.0)
        self.prepare_percent_text = tk.StringVar(value="0.0%")
        self.canvas_percent_text = tk.StringVar(value="0.0%")
        self.progress_detail = tk.StringVar(value="Waiting to start.")
        self.layout_preview = tk.StringVar(value="")
        self.status_badge_text = tk.StringVar(value="Ready")
        self.status_badge_color = "#16A34A"
        self._prep_target_progress = 0.0
        self._canvas_target_progress = 0.0

        self._configure_tree_style()
        self._build_ui()
        self._toggle_controls()
        self._animate_progress_bars()
        self.bind("<Control-s>", lambda _e: self.combine_and_save())

    def _apply_windows_identity() -> None:
        if not sys.platform.startswith("win"):
            return
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
        except Exception:
            pass

    def _apply_icon(self) -> None:
        ico = safe_resource_path("combine_photos_studio.ico")
        png = safe_resource_path("combine_photos_studio_icon.png")
        if ico:
            try:
                self.iconbitmap(default=str(ico))
            except Exception:
                try:
                    self.iconbitmap(str(ico))
                except Exception:
                    pass
        if png:
            try:
                if not hasattr(self, "_icon_photo") or self._icon_photo is None:
                    self._icon_photo = tk.PhotoImage(file=str(png))
                self.iconphoto(True, self._icon_photo)
            except Exception:
                pass

    def _configure_tree_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Modern.Treeview",
            background="#1F1F1F",
            fieldbackground="#1F1F1F",
            foreground="#E5E7EB",
            borderwidth=0,
            rowheight=34,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Modern.Treeview.Heading",
            background="#292929",
            foreground="#F3F4F6",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI Semibold", 10),
            padding=(10, 8),
        )
        style.map(
            "Modern.Treeview",
            background=[("selected", "#1F6AA5")],
            foreground=[("selected", "#FFFFFF")],
        )

    def _section_title(self, parent, text: str, subtitle: str | None = None):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(
                parent, text=subtitle, text_color=("gray38", "gray65"),
                font=ctk.CTkFont(size=12), wraplength=330, justify="left"
            ).pack(anchor="w", pady=(2, 10))

    def _field(self, parent, label: str, widget, pady=(0, 10)):
        ctk.CTkLabel(parent, text=label, text_color=("gray32", "gray72"),
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        widget.pack(fill="x", pady=(4, pady[1]))
        return widget

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(
            sidebar, text="Combine\nPhotos Studio",
            font=ctk.CTkFont(size=28, weight="bold"), justify="left"
        ).grid(row=0, column=0, padx=22, pady=(28, 2), sticky="w")
        ctk.CTkLabel(
            sidebar, text=f"Giant image compiler  •  v{APP_VERSION}",
            text_color=("gray40", "gray68"), font=ctk.CTkFont(size=11)
        ).grid(row=1, column=0, padx=22, pady=(0, 22), sticky="w")

        self.pages = {}
        self.nav_buttons = {}
        for row, name in enumerate(["Composer", "Compression", "Performance"], start=2):
            btn = ctk.CTkButton(
                sidebar, text=name, anchor="w", height=42, corner_radius=9,
                fg_color="transparent", command=lambda n=name: self.show_page(n)
            )
            btn.grid(row=row, column=0, padx=14, pady=5, sticky="ew")
            self.nav_buttons[name] = btn

        capability = []
        capability.append("HEIC ✓" if HEIF_AVAILABLE else "HEIC —")
        capability.append("BigTIFF ✓" if TIFFFILE_AVAILABLE else "BigTIFF —")
        ctk.CTkLabel(
            sidebar, text="   ".join(capability), text_color=("gray42", "gray62"),
            font=ctk.CTkFont(size=10)
        ).grid(row=6, column=0, padx=18, pady=6, sticky="sw")

        self.appearance = ctk.CTkOptionMenu(
            sidebar, values=["System", "Dark", "Light"],
            command=self._change_appearance, height=34
        )
        self.appearance.set("System")
        self.appearance.grid(row=8, column=0, padx=14, pady=(8, 18), sticky="ew")

        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.pages["Composer"] = self._build_composer_page()
        self.pages["Compression"] = self._build_compression_page()
        self.pages["Performance"] = self._build_performance_page()
        self.show_page("Composer")

        for variable in [
            self.columns_value, self.common_width, self.max_output_dimension,
            self.jpeg_quality, self.heic_quality, self.custom_width, self.custom_height
        ]:
            variable.trace_add("write", lambda *_args: self._on_layout_control_changed())
        self.output_format.trace_add("write", lambda *_args: self._update_layout_summary())

    def _change_appearance(self, value: str) -> None:
        ctk.set_appearance_mode(value)
        style = ttk.Style(self)
        if value == "Light":
            style.configure("Modern.Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", foreground="#111827")
            style.configure("Modern.Treeview.Heading", background="#EEF2F7", foreground="#111827")
        else:
            style.configure("Modern.Treeview", background="#1F1F1F", fieldbackground="#1F1F1F", foreground="#E5E7EB")
            style.configure("Modern.Treeview.Heading", background="#292929", foreground="#F3F4F6")

    def show_page(self, name: str) -> None:
        for page in self.pages.values():
            page.grid_remove()
        self.pages[name].grid(row=0, column=0, sticky="nsew")
        for n, b in self.nav_buttons.items():
            b.configure(fg_color=("#3B8ED0", "#1F6AA5") if n == name else "transparent")

    def _build_header(self, page, title: str, subtitle: str):
        head = ctk.CTkFrame(page, fg_color="transparent")
        head.grid(row=0, column=0, padx=26, pady=(22, 12), sticky="ew")
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text=title, font=ctk.CTkFont(size=30, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            head, text=subtitle, text_color=("gray40", "gray66"), font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, pady=(4, 0), sticky="w")
        return head


def main() -> None:
    import multiprocessing
    multiprocessing.freeze_support()
    app = ImageCombinerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
