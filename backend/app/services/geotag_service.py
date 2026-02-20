from __future__ import annotations

import datetime as dt
import json
from functools import lru_cache
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont


def _parse_reported_at(ts: Optional[int], created_at: dt.datetime) -> dt.datetime:
    if not ts:
        return created_at
    try:
        if ts > 10**12:
            return dt.datetime.utcfromtimestamp(ts / 1000.0)
        return dt.datetime.utcfromtimestamp(ts)
    except Exception:
        return created_at


@lru_cache(maxsize=512)
def reverse_geocode_address(latitude: float, longitude: float) -> str:
    """Best-effort reverse geocode using OpenStreetMap Nominatim.

    If the request fails (offline/throttled), returns an empty string.
    """

    try:
        url = (
            "https://nominatim.openstreetmap.org/reverse?format=jsonv2"
            f"&lat={latitude:.6f}&lon={longitude:.6f}"
        )
        req = Request(
            url,
            headers={
                "User-Agent": "AquaAlert/0.1 (demo; contact: local)",
                "Accept": "application/json",
            },
            method="GET",
        )
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        addr = str(data.get("display_name") or "").strip()
        return addr
    except Exception:
        return ""


def annotate_report_image(
    *,
    image_file: Path,
    qr_file: Path,
    latitude: float,
    longitude: float,
    accuracy_m: float,
    created_at: dt.datetime,
    reported_timestamp: Optional[int],
) -> None:
    """Draw a geotag footer onto the image (QR + address + coords + timestamp).

    Writes the annotated image back to the same file.
    """

    base = Image.open(image_file).convert("RGB")
    width, height = base.size

    panel_h = int(max(150, min(240, height * 0.22)))
    out = Image.new("RGB", (width, height + panel_h), (0, 0, 0))
    out.paste(base, (0, 0))

    draw = ImageDraw.Draw(out)
    font = ImageFont.load_default()

    # QR on the left
    qr_img = Image.open(qr_file).convert("RGB")
    qr_size = max(80, panel_h - 24)
    qr_img = qr_img.resize((qr_size, qr_size))
    qr_x = 12
    qr_y = height + (panel_h - qr_size) // 2
    out.paste(qr_img, (qr_x, qr_y))

    # Text on the right
    addr = reverse_geocode_address(latitude, longitude)
    reported_at = _parse_reported_at(reported_timestamp, created_at)

    lines = []
    if addr:
        lines.append(f"Address: {addr}")
    else:
        lines.append("Address: (unavailable)")

    lines.append(f"Lat: {latitude:.6f}   Lon: {longitude:.6f}")
    lines.append(f"Accuracy: {accuracy_m:.0f}m")
    lines.append(f"Timestamp (UTC): {reported_at.replace(microsecond=0).isoformat()}Z")

    text_x = qr_x + qr_size + 14
    text_y = height + 12

    # Clip overly-long address visually by wrapping.
    max_w = width - text_x - 12
    wrapped: list[str] = []
    for line in lines:
        if not line.startswith("Address:"):
            wrapped.append(line)
            continue

        prefix = "Address: "
        rest = line[len(prefix) :]
        if not rest:
            wrapped.append(line)
            continue

        # Simple word wrap.
        current = prefix
        for word in rest.split():
            candidate = (current + word + " ").rstrip()
            if draw.textlength(candidate, font=font) <= max_w:
                current = candidate + " "
            else:
                wrapped.append(current.rstrip())
                current = prefix + word + " "
        wrapped.append(current.rstrip())

    y = text_y
    for line in wrapped:
        draw.text((text_x, y), line, fill=(255, 255, 255), font=font)
        y += 16

    out.save(image_file, format="JPEG", quality=85, optimize=True)
