from __future__ import annotations

from collections import defaultdict

from pymongo.database import Database

SEVERITY_WEIGHT = {"Low": 1, "Medium": 3, "High": 5}


def compute_cluster_id(latitude: float, longitude: float) -> str:
    return f"{round(latitude, 3)}_{round(longitude, 3)}"


def _cluster_center(cluster_id: str) -> tuple[float, float]:
    lat_s, lon_s = cluster_id.split("_", 1)
    return float(lat_s), float(lon_s)


def get_clusters(db: Database, *, district: str | None = None):
    query: dict = {}
    if district:
        query["district"] = district
    reports = list(db["reports"].find(query, {"id": 1, "cluster_id": 1, "severity": 1}))
    counts: dict[str, int] = defaultdict(int)
    max_weight: dict[str, int] = defaultdict(int)
    max_sev: dict[str, str] = defaultdict(lambda: "Low")

    report_ids_by_cluster: dict[str, list[int]] = defaultdict(list)

    for r in reports:
        report_id = int(r.get("id", 0))
        cluster_id = str(r.get("cluster_id") or "")
        severity = str(r.get("severity") or "Low")
        if not cluster_id:
            continue
        counts[cluster_id] += 1
        report_ids_by_cluster[cluster_id].append(int(report_id))
        w = SEVERITY_WEIGHT.get(severity or "Low", 1)
        if w >= max_weight[cluster_id]:
            max_weight[cluster_id] = w
            max_sev[cluster_id] = severity or "Low"

    votes = list(db["validations"].find({}, {"report_id": 1, "vote": 1}))
    agree_by_report: dict[int, int] = defaultdict(int)
    disagree_by_report: dict[int, int] = defaultdict(int)
    for v in votes:
        rid = int(v.get("report_id", 0))
        vote = int(v.get("vote", 0))
        if vote == 1:
            agree_by_report[rid] += 1
        else:
            disagree_by_report[rid] += 1

    agree_by_cluster: dict[str, int] = defaultdict(int)
    disagree_by_cluster: dict[str, int] = defaultdict(int)
    for cluster_id, rids in report_ids_by_cluster.items():
        for rid in rids:
            agree_by_cluster[cluster_id] += agree_by_report.get(rid, 0)
            disagree_by_cluster[cluster_id] += disagree_by_report.get(rid, 0)

    def _escalate(base: str, agree: int, disagree: int) -> str:
        total = agree + disagree
        if total == 0:
            return base
        ratio = agree / total
        # Escalation rules to make clusters "more reddish" as more people agree.
        if agree >= 4 and ratio >= 0.7:
            return "High"
        if agree >= 2 and ratio >= 0.6:
            return "Medium" if base == "Low" else base
        return base

    clusters = []
    for cluster_id, report_count in counts.items():
        lat, lon = _cluster_center(cluster_id)
        severity = _escalate(max_sev[cluster_id], agree_by_cluster[cluster_id], disagree_by_cluster[cluster_id])
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
