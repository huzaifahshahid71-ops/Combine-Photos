# Changelog

## v1.0.1

- Fixed Windows startup crash caused by `_apply_windows_identity` losing its `@staticmethod` decorator during the module refactor.
- Restored `@staticmethod` on `_parse_exif_datetime`, preventing captured-date sorting from passing an unintended `self` argument.
- Added regression tests for decorator-sensitive methods before producing Windows builds.

## v1.0

- Rebuilt the application UI with CustomTkinter.
- Added Composer, Compression, and Performance pages.
- Added dark / light / system appearance modes.
- Preserved EXIF / modified / filename sorting and chronological direction controls.
- Preserved automatic/manual grid layouts and common-width/original/custom-resolution scaling.
- Preserved PNG, JPEG, HEIC, TIFF and BigTIFF output paths.
- Preserved JPEG quality/optimization/subsampling, HEIC quality, and TIFF compression controls.
- Preserved multi-core image preparation and disk-backed large TIFF/BigTIFF generation.
- Added a custom Windows icon and version metadata.
- Added a verified one-click PyInstaller Windows builder.
- Added GitHub Actions Windows build workflow.
