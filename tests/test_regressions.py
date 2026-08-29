import ast
from datetime import datetime
from pathlib import Path

from workflow_preview import PreviewMixin

ROOT = Path(__file__).resolve().parents[1]


def _decorators_for_method(path: Path, class_name: str, method_name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method_name)
    names = []
    for dec in method.decorator_list:
        if isinstance(dec, ast.Name):
            names.append(dec.id)
        elif isinstance(dec, ast.Attribute):
            names.append(dec.attr)
    return names


def test_windows_identity_keeps_staticmethod_decorator():
    decorators = _decorators_for_method(
        ROOT / "combine_photos_studio.py", "ImageCombinerApp", "_apply_windows_identity"
    )
    assert "staticmethod" in decorators


def test_parse_exif_datetime_is_staticmethod_and_callable():
    raw = __import__("inspect").getattr_static(PreviewMixin, "_parse_exif_datetime")
    assert isinstance(raw, staticmethod)
    assert PreviewMixin._parse_exif_datetime("2026:08:29 22:00:01") == datetime(2026, 8, 29, 22, 0, 1)
