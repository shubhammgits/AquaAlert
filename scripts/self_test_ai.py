from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="AquaAlert AI analysis self-test")
    parser.add_argument("--image", type=str, default="", help="Optional path to a JPG/PNG to analyze")
    parser.add_argument("--desc", type=str, default="dirty water", help="Optional description prompt")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.ai_service import _extract_json, _normalize, analyze_image

    raw = '{"problem": ["test"], "causes": [], "precautions": [], "prevention": [], "severity": "High"}'
    parsed = _extract_json(raw)
    print("normalized:", _normalize(parsed))

    if args.image:
        image_path = Path(args.image)
        image_bytes = image_path.read_bytes()
        res = analyze_image(image_bytes=image_bytes, description=args.desc)
        print("analysis:", res)
    else:
        # This intentionally isn't a real image. With GEMINI_API_KEY unset, the function must not crash.
        res = analyze_image(image_bytes=b"not-an-image", description=args.desc)
        print("fallback:", res)


if __name__ == "__main__":
    main()
