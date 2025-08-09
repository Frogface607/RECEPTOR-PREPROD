from __future__ import annotations
from io import BytesIO
import zipfile

def make_zip(files: dict[str, bytes]) -> bytes:
    bio = BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return bio.getvalue()