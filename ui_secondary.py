try:
    import customtkinter as ctk
except ImportError:
    ctk = None
from combine_photos_core import HEIF_AVAILABLE, TIFFFILE_AVAILABLE

class SecondaryPagesMixin:
    def _build_compression_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid_columnconfigure((0, 1), weight=1)
        self._build_header(
            page, "Compression",
            "Fine-tune JPEG, HEIC, TIFF and BigTIFF output without changing the composition workflow."
        )

        left = ctk.CTkFrame(page, corner_radius=14)
        left.grid(row=1, column=0, padx=(26, 7), pady=(5, 22), sticky="nsew")
        right = ctk.CTkFrame(page, corner_radius=14)
        right.grid(row=1, column=1, padx=(7, 26), pady=(5, 22), sticky="nsew")

        self._section_title(left, "File type", "Choose the container format for the final giant image.")
        format_values = ["PNG", "JPEG", "TIFF"]
        if HEIF_AVAILABLE:
            format_values.append("HEIC")
        if TIFFFILE_AVAILABLE:
            format_values.append("BIGTIFF")
        self.compression_format_menu = ctk.CTkOptionMenu(
            left, values=format_values, variable=self.output_format, command=self._on_control_changed
        )
        self.compression_format_menu.pack(fill="x", padx=16, pady=(4, 16))

        ctk.CTkFrame(left, height=1, fg_color=("gray82", "gray25")).pack(fill="x", padx=16, pady=(0, 14))
        self._section_title(left, "JPEG", "Quality 90–95 is usually visually excellent with much smaller files.")
        q = ctk.CTkFrame(left, fg_color="transparent")
        q.pack(fill="x", padx=16, pady=(0, 8))
        q.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(q, text="Quality").grid(row=0, column=0, sticky="w")
        ctk.CTkEntry(q, width=90, textvariable=self.jpeg_quality).grid(row=0, column=1, sticky="e")
        ctk.CTkSwitch(left, text="Optimize JPEG", variable=self.jpeg_optimize).pack(anchor="w", padx=16, pady=(4, 10))
        self.jpeg_subsampling_combo = ctk.CTkOptionMenu(
            left, values=["4:4:4", "4:2:2", "4:2:0"], variable=self.jpeg_subsampling,
            command=self._on_control_changed
        )
        self.jpeg_subsampling_combo.pack(fill="x", padx=16, pady=(0, 16))

        self._section_title(right, "HEIC", "High-efficiency output is available when pillow-heif is installed.")
        hq = ctk.CTkFrame(right, fg_color="transparent")
        hq.pack(fill="x", padx=16, pady=(0, 10))
        hq.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hq, text="Quality").grid(row=0, column=0, sticky="w")
        ctk.CTkEntry(hq, width=90, textvariable=self.heic_quality).grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(
            right, text=("HEIC encoder ready" if HEIF_AVAILABLE else "Install pillow-heif to enable HEIC output"),
            text_color=("#15803D", "#4ADE80") if HEIF_AVAILABLE else ("#B45309", "#FBBF24")
        ).pack(anchor="w", padx=16, pady=(0, 18))

        ctk.CTkFrame(right, height=1, fg_color=("gray82", "gray25")).pack(fill="x", padx=16, pady=(0, 14))
        self._section_title(right, "TIFF / BigTIFF", "Disk-backed BigTIFF is the safest choice for truly enormous grids.")
        self.tiff_compression_combo = ctk.CTkOptionMenu(
            right, values=["none", "deflate", "lzw"], variable=self.tiff_compression,
            command=self._on_control_changed
        )
        self.tiff_compression_combo.pack(fill="x", padx=16, pady=(0, 10))
        ctk.CTkLabel(
            right, text=("TIFF / BigTIFF engine ready" if TIFFFILE_AVAILABLE else "Install tifffile for TIFF / BigTIFF"),
            text_color=("#15803D", "#4ADE80") if TIFFFILE_AVAILABLE else ("#B45309", "#FBBF24")
        ).pack(anchor="w", padx=16)
        return page

    def _build_performance_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid_columnconfigure((0, 1), weight=1)
        self._build_header(
            page, "Performance & Large Files",
            "Control CPU usage and the safety limits used for extremely large final canvases."
        )

        left = ctk.CTkFrame(page, corner_radius=14)
        left.grid(row=1, column=0, padx=(26, 7), pady=(5, 22), sticky="nsew")
        right = ctk.CTkFrame(page, corner_radius=14)
        right.grid(row=1, column=1, padx=(7, 26), pady=(5, 22), sticky="nsew")

        self._section_title(left, "Processing", "Preparation can use every available CPU core for large folders.")
        ctk.CTkSwitch(left, text="Use multi-core processing", variable=self.use_multicore).pack(anchor="w", padx=16, pady=(0, 14))
        ctk.CTkSwitch(left, text="Allow very large PNG/JPEG in-memory builds", variable=self.allow_large_standard).pack(anchor="w", padx=16, pady=(0, 14))
        ctk.CTkSwitch(left, text="Auto-fit oversized PNG/JPEG output", variable=self.auto_limit_output).pack(anchor="w", padx=16, pady=(0, 14))
        limit = ctk.CTkFrame(left, fg_color="transparent")
        limit.pack(fill="x", padx=16, pady=(0, 16))
        limit.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(limit, text="Maximum output side").grid(row=0, column=0, sticky="w")
        ctk.CTkEntry(limit, width=110, textvariable=self.max_output_dimension).grid(row=0, column=1, sticky="e")

        self._section_title(right, "Large-grid guidance")
        tips = (
            "• Filename sorting is fastest for folders with thousands of images.\n\n"
            "• Common-width mode keeps rows predictable and usually saves RAM.\n\n"
            "• PNG/JPEG are assembled in memory; the app warns around 1.6 billion pixels.\n\n"
            "• TIFF / BigTIFF use a disk-backed canvas and are much safer for extreme outputs.\n\n"
            "• If one source image is damaged, disable multi-core to identify it more easily."
        )
        ctk.CTkLabel(
            right, text=tips, justify="left", anchor="nw", wraplength=470,
            text_color=("gray32", "gray72"), font=ctk.CTkFont(size=13)
        ).pack(fill="both", expand=True, padx=16, pady=(0, 16))
        return page
