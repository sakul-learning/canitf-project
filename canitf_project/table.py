from __future__ import annotations

import json
import urllib.request
from dataclasses import asdict
from typing import Iterable

from .parser import CandidateFeature, feature_key, merge_candidates

CANITF_TOOLS_JSON = "https://cani.tf/tools.json"


def load_canitf_features(url: str = CANITF_TOOLS_JSON) -> list[CandidateFeature]:
    """Load the curated cani.tf public JSON API as seed rows."""
    req = urllib.request.Request(url, headers={"User-Agent": "canitf-project/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    rows: dict[str, CandidateFeature] = {}
    for tool in ("terraform", "opentofu"):
        for item in payload.get(tool, {}).get("features", []):
            title = item["name"]
            key = feature_key(title)
            row = rows.setdefault(key, CandidateFeature(key=key, title=title, tools={}, sources=[]))
            data = {k: v for k, v in item.items() if k in {"version", "url", "featureRequestURL"} and v}
            data["curated"] = True
            row.tools[tool] = data
            if data.get("url"):
                row.sources.append(data["url"])
            if data.get("featureRequestURL"):
                row.sources.append(data["featureRequestURL"])
    return merge_candidates(rows.values())


def rows_to_json(rows: Iterable[CandidateFeature]) -> str:
    return json.dumps([asdict(row) for row in rows], indent=2, sort_keys=True)


def rows_to_markdown(rows: Iterable[CandidateFeature]) -> str:
    lines = [
        "# Terraform / OpenTofu feature tracking table",
        "",
        "| Feature | OpenTofu | Terraform | Sources |",
        "|---|---:|---:|---|",
    ]
    for row in rows:
        tofu = _cell(row.tools.get("opentofu"))
        terraform = _cell(row.tools.get("terraform"))
        sources = "<br>".join(f"[source]({s})" for s in row.sources[:4])
        lines.append(f"| {row.title} | {tofu} | {terraform} | {sources} |")
    lines.append("")
    return "\n".join(lines)


def _cell(data: dict | None) -> str:
    if not data:
        return "—"
    label = data.get("version") or "?"
    if data.get("curated") and label != "?":
        label = f"{label}*"
    url = data.get("url") or data.get("featureRequestURL")
    return f"[{label}]({url})" if url else label
