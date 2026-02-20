from __future__ import annotations

import json
import os
import re
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

    # Common Gemini formatting: markdown fenced code block.
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\\s*```$", "", s)
        s = s.strip()

    # If the whole response is JSON, parse directly.
    try:
        parsed = json.loads(s)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found")
    return json.loads(s[start : end + 1])


def _fallback(*, description: str, reason: str | None = None) -> AnalysisResult:
    msg = "AI analysis unavailable"
    if reason:
        msg = f"{msg} ({reason})"
    return {
        "problem": [msg] if description else [],
        "causes": [],
        "precautions": ["Provide clean water and avoid contact with suspected sources."],
        "prevention": ["Report and monitor the area; ensure proper sanitation."],
        "severity": "Low",
    }


def analyze_image(*, image_bytes: bytes, description: str) -> AnalysisResult:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _fallback(description=description, reason="missing GEMINI_API_KEY")

    try:
        import google.generativeai as genai
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Missing dependency: google-generativeai") from exc

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        image = Image.open(BytesIO(image_bytes)).convert("RGB")

        response = model.generate_content([PROMPT + f"\nUser description: {description}", image])
        text = getattr(response, "text", None) or ""
        parsed = _extract_json(text)
        return _normalize(parsed)
    except Exception as exc:
        # Best-effort: never break report creation just because AI returned non-JSON or the API failed.
        return _fallback(description=description, reason=type(exc).__name__)
