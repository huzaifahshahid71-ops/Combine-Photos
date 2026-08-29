# Combine Photos Studio

A modern Windows desktop app for combining a handful of photos — or thousands — into one tightly packed giant image.

Built around the original **Combine Photos Grid** engine, with a new CustomTkinter interface and the same large-image workflow.

## Highlights

- Modern dark / light / system UI
- Add individual images or scan an entire folder
- Sort by filename, captured date (EXIF), or modified date
- Chronological and reverse-chronological ordering
- Automatic square-ish grid or exact manual column count
- Input sizing:
  - common width
  - original size
  - custom resolution
  - 1920×1080 / 1280×720 presets
- PNG, JPEG, TIFF, BigTIFF and HEIC output
- JPEG quality, optimize and chroma-subsampling controls
- HEIC quality controls
- TIFF/BigTIFF compression controls
- Multi-core preprocessing
- Progress tracking for image preparation and final canvas assembly
- Disk-backed TIFF / BigTIFF path for enormous images
- PNG/JPEG dimension safeguards and optional auto-fit
- `Ctrl+S` build shortcut

## Build the Windows EXE

1. Install Python 3.10+.
2. Clone or download the repository.
3. Double-click `BUILD_APP.bat`.
4. The verified executable will be created at:

```text
dist\CombinePhotosStudio.exe
```

The builder installs required dependencies, generates the application icon, creates a one-file GUI executable, and verifies the embedded PyInstaller archive.

## Run from source

```powershell
py -m pip install -r requirements.txt
py generate_icon.py
py combine_photos_studio.py
```

## Large-output notes

PNG/JPEG are assembled in memory and must also respect common encoder side-length limits. For truly extreme grids, TIFF or BigTIFF are safer because the app can build the RGB canvas through a disk-backed memory map.

## License

MIT
