import email.utils
import os
import urllib.parse
from typing import Tuple, Optional

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".htm": "text/html; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".pdf": "application/pdf",
}

def http_date() -> str:
    return email.utils.formatdate(usegmt=True)

def parse_request_line(line: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    parts = line.strip().split()
    if len(parts) != 3:
        return None, None, None
    return parts[0], parts[1], parts[2]

def split_http_message(data: bytes) -> Tuple[bytes, bytes]:
    separator = b"\r\n\r\n"
    idx = data.find(separator)
    if idx == -1:
        return data, b""
    return data[:idx], data[idx + 4:]

def resolve_path(root: str, url_path: str) -> Tuple[Optional[str], bool]:
    if not url_path:
        return None, False
    
    parsed = urllib.parse.urlsplit(url_path)
    decoded = urllib.parse.unquote(parsed.path)
    
    full_path = os.path.normpath(os.path.join(root, decoded.lstrip("/")))
    
    root_real = os.path.realpath(root)
    full_real = os.path.realpath(full_path)
    
    if not full_real.startswith(root_real):
        return None, False
    
    if not os.path.exists(full_real):
        return None, False
    
    return full_real, os.path.isdir(full_real)

def guess_content_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return MIME_TYPES.get(ext, "application/octet-stream")
