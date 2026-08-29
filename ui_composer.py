from tkinter import ttk
try:
    import customtkinter as ctk
except ImportError:
    ctk = None
from combine_photos_core import HEIF_AVAILABLE, TIFFFILE_AVAILABLE

class ComposerMixin:
    def _build_composer_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(3, weight=1)

        head = self._build_header(
            page, "Composer",
            "Combine a handful of photos or thousands into one ordered, tightly packed giant image."
        )
        self.build_top_btn = ctk.CTkButton(
            head, text="Build Image", width=150, height=40,
            font=ctk.CTkFont(weight="bold"), command=self.combine_and_save
        )
        self.build_top_btn.grid(row=0, column=1, rowspan=2, padx=(12, 0), sticky="e")

        toolbar = ctk.CTkFrame(page, corner_radius=14)
        toolbar.grid(row=1, column=0, padx=26, pady=(0, 10), sticky="ew")
        self.add_images_btn = ctk.CTkButton(toolbar, text="Add Images", command=self.add_images)
        self.add_images_btn.pack(side="left", padx=(12, 5), pady=11)
        self.add_folder_btn = ctk.CTkButton(
            toolbar, text="Add Folder", fg_color="transparent", border_width=1, command=self.add_folder
        )
        self.add_folder_btn.pack(side="left", padx=5, pady=11)
        self.remove_btn = ctk.CTkButton(
            toolbar, text="Remove Selected", fg_color="transparent", border_width=1, command=self.remove_selected
        )
        self.remove_btn.pack(side="left", padx=5, pady=11)
        self.clear_btn = ctk.CTkButton(
            toolbar, text="Clear", fg_color="transparent", border_width=1, command=self.clear_images
        )
        self.clear_btn.pack(side="left", padx=5, pady=11)
        self.refresh_btn = ctk.CTkButton(
            toolbar, text="Refresh Preview", fg_color="transparent", border_width=1, command=self.refresh_preview
        )
        self.refresh_btn.pack(side="left", padx=5, pady=11)

        self.status_badge = ctk.CTkLabel(
            toolbar, text="Ready", width=72, height=28, corner_radius=14,
            fg_color=("#16A34A", "#15803D"), text_color="white",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.status_badge.pack(side="right", padx=12)

        summary = ctk.CTkFrame(page, fg_color="transparent")
        summary.grid(row=2, column=0, padx=26, pady=(0, 10), sticky="ew")
        summary.grid_columnconfigure((0, 1, 2), weight=1)

        card1 = ctk.CTkFrame(summary, corner_radius=14)
        card1.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkLabel(card1, text="Images", text_color=("gray38", "gray67")).pack(anchor="w", padx=15, pady=(12, 0))
        self.count_label = ctk.CTkLabel(card1, text="0", font=ctk.CTkFont(size=26, weight="bold"))
        self.count_label.pack(anchor="w", padx=15, pady=(0, 12))

        card2 = ctk.CTkFrame(summary, corner_radius=14)
        card2.grid(row=0, column=1, padx=6, sticky="ew")
        ctk.CTkLabel(card2, text="Planned grid", text_color=("gray38", "gray67")).pack(anchor="w", padx=15, pady=(12, 0))
        self.quick_layout_label = ctk.CTkLabel(card2, text="Auto", font=ctk.CTkFont(size=26, weight="bold"))
        self.quick_layout_label.pack(anchor="w", padx=15, pady=(0, 12))

        card3 = ctk.CTkFrame(summary, corner_radius=14)
        card3.grid(row=0, column=2, padx=(6, 0), sticky="ew")
        ctk.CTkLabel(card3, text="Output", text_color=("gray38", "gray67")).pack(anchor="w", padx=15, pady=(12, 0))
        self.output_summary_label = ctk.CTkLabel(card3, textvariable=self.output_format, font=ctk.CTkFont(size=26, weight="bold"))
        self.output_summary_label.pack(anchor="w", padx=15, pady=(0, 12))

        body = ctk.CTkFrame(page, fg_color="transparent")
        body.grid(row=3, column=0, padx=26, pady=(0, 10), sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)

        lib = ctk.CTkFrame(body, corner_radius=14)
        lib.grid(row=0, column=0, padx=(0, 7), sticky="nsew")
        lib.grid_rowconfigure(1, weight=1)
        lib.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(lib, text="Image order preview", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=15, pady=(13, 8), sticky="w"
        )

        tree_wrap = ctk.CTkFrame(lib, fg_color="transparent")
        tree_wrap.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        tree_wrap.grid_rowconfigure(0, weight=1)
        tree_wrap.grid_columnconfigure(0, weight=1)
        columns = ("index", "name", "date")
        self.tree = ttk.Treeview(tree_wrap, columns=columns, show="headings", style="Modern.Treeview")
        self.tree.heading("index", text="#")
        self.tree.heading("name", text="File")
        self.tree.heading("date", text="Sort time")
        self.tree.column("index", width=60, anchor="center", stretch=False)
        self.tree.column("name", width=420, anchor="w")
        self.tree.column("date", width=175, anchor="w", stretch=False)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ctk.CTkScrollbar(tree_wrap, command=self.tree.yview)
        scroll.grid(row=0, column=1, padx=(5, 0), sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)

        settings = ctk.CTkScrollableFrame(body, corner_radius=14, label_text="Composition & Export")
        settings.grid(row=0, column=1, padx=(7, 0), sticky="nsew")

        self._section_title(settings, "Ordering", "Choose the metadata used to order the final grid.")
        self.sort_basis_combo = ctk.CTkOptionMenu(
            settings, values=["filename", "captured", "modified"], variable=self.sort_basis,
            command=self._on_control_changed
        )
        self._field(settings, "Sort by", self.sort_basis_combo)
        self.sort_direction_combo = ctk.CTkOptionMenu(
            settings, values=["chronological", "reverse chronological"], variable=self.sort_direction,
            command=self._on_control_changed
        )
        self._field(settings, "Order", self.sort_direction_combo)

        ctk.CTkFrame(settings, height=1, fg_color=("gray82", "gray25")).pack(fill="x", pady=(2, 13))

        self._section_title(settings, "Grid", "Auto makes a square-ish grid; Manual gives exact column control.")
        self.columns_combo = ctk.CTkOptionMenu(
            settings, values=["auto", "manual"], variable=self.columns_mode, command=self._on_control_changed
        )
        self._field(settings, "Columns mode", self.columns_combo)
        self.columns_spin = ctk.CTkEntry(settings, textvariable=self.columns_value)
        self._field(settings, "Manual columns", self.columns_spin)

        ctk.CTkFrame(settings, height=1, fg_color=("gray82", "gray25")).pack(fill="x", pady=(2, 13))

        self._section_title(settings, "Input sizing", "Resize before combining to control final dimensions and memory.")
        self.resize_combo = ctk.CTkOptionMenu(
            settings, values=["common_width", "original_size", "custom_resolution"],
            variable=self.resize_mode, command=self._on_control_changed
        )
        self._field(settings, "Mode", self.resize_combo)
        self.width_spin = ctk.CTkEntry(settings, textvariable=self.common_width)
        self._field(settings, "Common width (px)", self.width_spin)

        self.scale_preset_combo = ctk.CTkOptionMenu(
            settings, values=["None", "1920x1080", "1280x720"],
            variable=self.scale_preset, command=self._on_control_changed
        )
        self._field(settings, "Custom preset", self.scale_preset_combo)
        wh = ctk.CTkFrame(settings, fg_color="transparent")
        wh.pack(fill="x", pady=(0, 10))
        wh.grid_columnconfigure((0, 1), weight=1)
        self.custom_width_spin = ctk.CTkEntry(wh, textvariable=self.custom_width)
        self.custom_width_spin.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.custom_height_spin = ctk.CTkEntry(wh, textvariable=self.custom_height)
        self.custom_height_spin.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        ctk.CTkLabel(settings, text="Custom width × height", text_color=("gray40", "gray65"), font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(0, 10))

        self.bg_combo = ctk.CTkOptionMenu(
            settings, values=["black", "white"], variable=self.bg_color, command=self._on_control_changed
        )
        self._field(settings, "Background", self.bg_combo)

        format_values = ["PNG", "JPEG", "TIFF"]
        if HEIF_AVAILABLE:
            format_values.append("HEIC")
        if TIFFFILE_AVAILABLE:
            format_values.append("BIGTIFF")
        self.output_combo = ctk.CTkOptionMenu(
            settings, values=format_values, variable=self.output_format, command=self._on_control_changed
        )
        self._field(settings, "Output format", self.output_combo)

        self.build_bottom_btn = ctk.CTkButton(
            settings, text="Build Image", height=44,
            font=ctk.CTkFont(size=14, weight="bold"), command=self.combine_and_save
        )
        self.build_bottom_btn.pack(fill="x", pady=(5, 14))

        prog = ctk.CTkFrame(page, corner_radius=14)
        prog.grid(row=4, column=0, padx=26, pady=(0, 20), sticky="ew")
        prog.grid_columnconfigure(0, weight=1)

        status_row = ctk.CTkFrame(prog, fg_color="transparent")
        status_row.grid(row=0, column=0, padx=14, pady=(10, 4), sticky="ew")
        status_row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(status_row, textvariable=self.status_text, anchor="w").grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(status_row, text="Ctrl+S", text_color=("gray45", "gray58"), font=ctk.CTkFont(size=10)).grid(row=0, column=1, sticky="e")

        p1row = ctk.CTkFrame(prog, fg_color="transparent")
        p1row.grid(row=1, column=0, padx=14, sticky="ew")
        p1row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(p1row, text="Prepare images", text_color=("gray38", "gray70")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(p1row, textvariable=self.prepare_percent_text).grid(row=0, column=1, sticky="e")
        self.prepare_bar = ctk.CTkProgressBar(prog)
        self.prepare_bar.set(0)
        self.prepare_bar.grid(row=2, column=0, padx=14, pady=(3, 7), sticky="ew")

        p2row = ctk.CTkFrame(prog, fg_color="transparent")
        p2row.grid(row=3, column=0, padx=14, sticky="ew")
        p2row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(p2row, text="Final canvas", text_color=("gray38", "gray70")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(p2row, textvariable=self.canvas_percent_text).grid(row=0, column=1, sticky="e")
        self.canvas_bar = ctk.CTkProgressBar(prog)
        self.canvas_bar.set(0)
        self.canvas_bar.grid(row=4, column=0, padx=14, pady=(3, 7), sticky="ew")
        ctk.CTkLabel(prog, textvariable=self.progress_detail, text_color=("gray42", "gray62"), anchor="w").grid(
            row=5, column=0, padx=14, sticky="ew"
        )
        ctk.CTkLabel(prog, textvariable=self.layout_preview, text_color=("gray42", "gray62"), anchor="w").grid(
            row=6, column=0, padx=14, pady=(1, 10), sticky="ew"
        )
        return page

    def _animate_progress_bars(self) -> None:
        current_prep = float(self.prepare_progress.get())
        current_canvas = float(self.canvas_progress.get())
        current_prep += (self._prep_target_progress - current_prep) * 0.22
        current_canvas += (self._canvas_target_progress - current_canvas) * 0.22
        if abs(current_prep - self._prep_target_progress) < 0.15:
            current_prep = self._prep_target_progress
        if abs(current_canvas - self._canvas_target_progress) < 0.15:
            current_canvas = self._canvas_target_progress
        self.prepare_progress.set(max(0.0, min(100.0, current_prep)))
        self.canvas_progress.set(max(0.0, min(100.0, current_canvas)))
        try:
            self.prepare_bar.set(self.prepare_progress.get() / 100.0)
            self.canvas_bar.set(self.canvas_progress.get() / 100.0)
        except Exception:
            pass
        self.after(24, self._animate_progress_bars)
