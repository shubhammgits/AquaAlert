from __future__ import annotations

import json
import os
from io import BytesIO
from typing import Any, Literal, TypedDict

from PIL import Image

Severity = Literal["Low", "Medium", "High"]


class AnalysisResult(TypedDict):
    problem: list[str]
    causes: list[str]
    precautions: list[str]
    prevention: list[str]
    severity: Severity


PROMPT = (
    "Analyze this image of a water-related issue. "
    "Return ONLY valid JSON with this schema:\n"
    "{\n"
    "  \"problem\": [],\n"
    "  \"causes\": [],\n"
    "  \"precautions\": [],\n"
    "  \"prevention\": [],\n"
    "  \"severity\": \"Low\"|\"Medium\"|\"High\"\n"
    "}\n"
)


def _normalize(result: dict[str, Any]) -> AnalysisResult:
    def _as_list(key: str) -> list[str]:
        val = result.get(key, [])
        if isinstance(val, list):
            return [str(x) for x in val][:10]
        if isinstance(val, str) and val.strip():
            return [val.strip()]
        return []

    sev = str(result.get("severity", "Low")).strip().title()
    if sev not in {"Low", "Medium", "High"}:
        sev = "Low"

    return {
        "problem": _as_list("problem"),
        "causes": _as_list("causes"),
        "precautions": _as_list("precautions"),
        "prevention": _as_list("prevention"),
        "severity": sev,  # type: ignore[return-value]
    }


def _extract_json(text: str) -> dict[str, Any]:
    s = text.strip()
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found")
    return json.loads(s[start : end + 1])


def analyze_image(*, image_bytes: bytes, description: str) -> AnalysisResult:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Development fallback so the app remains usable without external credentials.
        return {
            "problem": ["Unconfigured AI analysis (missing GEMINI_API_KEY)"] if description else [],
            "causes": [],
            "precautions": ["Provide clean water and avoid contact with suspected sources."],
            "prevention": ["Report and monitor the area; ensure proper sanitation."],
            "severity": "Low",
        }

    try:
        import google.generativeai as genai
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Missing dependency: google-generativeai") from exc

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    response = model.generate_content([PROMPT + f"\nUser description: {description}", image])
    text = getattr(response, "text", None) or ""
    parsed = _extract_json(text)
    return _normalize(parsed)
