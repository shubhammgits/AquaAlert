from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Report

SEVERITY_WEIGHT = {"Low": 1, "Medium": 3, "High": 5}


def compute_cluster_id(latitude: float, longitude: float) -> str:
    return f"{round(latitude, 3)}_{round(longitude, 3)}"


def _cluster_center(cluster_id: str) -> tuple[float, float]:
    lat_s, lon_s = cluster_id.split("_", 1)
    return float(lat_s), float(lon_s)


def get_clusters(db: Session):
    reports = db.execute(select(Report.cluster_id, Report.severity)).all()
    counts: dict[str, int] = defaultdict(int)
    max_weight: dict[str, int] = defaultdict(int)
    max_sev: dict[str, str] = defaultdict(lambda: "Low")

    for cluster_id, severity in reports:
        counts[cluster_id] += 1
        w = SEVERITY_WEIGHT.get(severity or "Low", 1)
        if w >= max_weight[cluster_id]:
            max_weight[cluster_id] = w
            max_sev[cluster_id] = severity or "Low"

    clusters = []
    for cluster_id, report_count in counts.items():
        lat, lon = _cluster_center(cluster_id)
        severity = max_sev[cluster_id]
        priority = report_count * SEVERITY_WEIGHT.get(severity, 1)
        clusters.append(
            {
                "cluster_id": cluster_id,
                "latitude": lat,
                "longitude": lon,
                "report_count": report_count,
                "severity": severity,
                "priority": int(priority),
            }
        )

    clusters.sort(key=lambda c: c["priority"], reverse=True)
    return clusters
