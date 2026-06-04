from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

FEATURE_HEADING_RE = re.compile(r"^#{1,6}\s*(.+?)\s*$")
BULLET_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+?)\s*$")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
MARKDOWN_NOISE_RE = re.compile(r"[`*~>#]")
ISSUE_REF_RE = re.compile(r"\s*\(?#\d+\)?")

FEATURE_SECTION_WORDS = {
    "new", "feature", "features", "enhancement", "enhancements", "language",
    "functions", "provider", "providers", "backend", "backends", "state", "cli",
    "command", "commands", "module", "modules", "terraform", "opentofu", "notable",
    "improvements", "experimental",
}
SKIP_SECTION_WORDS = {"bug", "bugs", "fix", "fixed", "security", "upgrade", "dependency", "dependencies", "breaking"}


@dataclass
class CandidateFeature:
    key: str
    title: str
    tools: dict[str, dict] = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)


def normalize_title(text: str) -> str:
    text = LINK_RE.sub(r"\1", text)
    text = ISSUE_REF_RE.sub("", text)
    text = MARKDOWN_NOISE_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip(" .;:-")
    return text


def feature_key(title: str) -> str:
    title = normalize_title(title).lower()
    title = re.sub(r"\b(terraform|opentofu)\b", "", title)
    title = re.sub(r"\b(now|new|adds?|added|supports?|support|allows?|allow|can|will)\b", "", title)
    title = re.sub(r"[^a-z0-9]+", "-", title).strip("-")
    return title[:120] or "untitled"


def _section_score(heading: str) -> int:
    words = set(re.findall(r"[a-z]+", heading.lower()))
    if words & SKIP_SECTION_WORDS:
        return -1
    if words & FEATURE_SECTION_WORDS:
        return 1
    return 0


def extract_candidates_from_release(tool: str, tag: str, url: str, body: str) -> list[CandidateFeature]:
    candidates: list[CandidateFeature] = []
    current_score = 0
    for raw in body.splitlines():
        heading = FEATURE_HEADING_RE.match(raw)
        if heading:
            current_score = _section_score(heading.group(1))
            continue
        bullet = BULLET_RE.match(raw)
        if not bullet or current_score < 0:
            continue
        title = normalize_title(bullet.group(1))
        if not title or len(title) < 8:
            continue
        if current_score == 0 and not re.search(r"\b(adds?|added|new|supports?|support for|allows?|introduces?)\b", title, re.I):
            continue
        key = feature_key(title)
        candidates.append(CandidateFeature(
            key=key,
            title=title,
            tools={tool: {"version": tag.lstrip("v"), "url": url}},
            sources=[url],
        ))
    return candidates


def merge_candidates(candidates: Iterable[CandidateFeature]) -> list[CandidateFeature]:
    merged: dict[str, CandidateFeature] = {}
    for cand in candidates:
        existing = merged.get(cand.key)
        if existing is None:
            merged[cand.key] = CandidateFeature(cand.key, cand.title, dict(cand.tools), list(cand.sources))
            continue
        if len(cand.title) < len(existing.title):
            existing.title = cand.title
        existing.sources.extend(src for src in cand.sources if src not in existing.sources)
        for tool, data in cand.tools.items():
            existing.tools.setdefault(tool, data)
    return sorted(merged.values(), key=lambda c: c.title.lower())
