from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


def _env(name: str) -> str:
    return str(os.getenv(name, "")).strip()


def is_configured() -> bool:
    return bool(_env("SUPABASE_URL") and _env("SUPABASE_SERVICE_ROLE_KEY") and _env("SUPABASE_BUCKET"))


def bucket_name() -> str:
    return _env("SUPABASE_BUCKET")


def supabase_url() -> str:
    return _env("SUPABASE_URL").rstrip("/")


def service_role_key() -> str:
    return _env("SUPABASE_SERVICE_ROLE_KEY")


def public_object_url(object_path: str) -> str:
    path = quote(str(object_path).lstrip("/"), safe="/")
    return f"{supabase_url()}/storage/v1/object/public/{bucket_name()}/{path}"


def upload_bytes(*, object_path: str, data: bytes, content_type: str) -> str | None:
    if not is_configured():
        return None

    path = quote(str(object_path).lstrip("/"), safe="/")
    endpoint = f"{supabase_url()}/storage/v1/object/{bucket_name()}/{path}"
    request_obj = Request(endpoint, data=data, method="POST")
    request_obj.add_header("Authorization", f"Bearer {service_role_key()}")
    request_obj.add_header("apikey", service_role_key())
    request_obj.add_header("x-upsert", "true")
    request_obj.add_header("Content-Type", content_type or "application/octet-stream")

    with urlopen(request_obj, timeout=30) as response:
        response.read()

    return public_object_url(object_path)


def upload_file(*, file_path: Path, object_path: str, content_type: str) -> str | None:
    return upload_bytes(object_path=object_path, data=file_path.read_bytes(), content_type=content_type)
