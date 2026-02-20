from __future__ import annotations

from pathlib import Path

import qrcode


def generate_qr_for_report(*, report_id: int, latitude: float, longitude: float) -> str:
    static_dir = Path(__file__).resolve().parents[2] / "static"
    qr_dir = static_dir / "qr"
    qr_dir.mkdir(parents=True, exist_ok=True)

    url = f"https://www.google.com/maps?q={latitude},{longitude}"
    img = qrcode.make(url)
    filename = f"report_{report_id}.png"
    out_path = qr_dir / filename
    img.save(out_path)
    return f"qr/{filename}"
