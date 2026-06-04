from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass(frozen=True)
class Release:
    tool: str
    repo: str
    tag: str
    name: str
    published_at: str
    html_url: str
    body: str


DEFAULT_REPOS = {
    "terraform": "hashicorp/terraform",
    "opentofu": "opentofu/opentofu",
}


def _request_json(url: str, token: str | None = None, attempts: int = 4):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "canitf-project/0.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == attempts:
                raise
        except TimeoutError as exc:
            last_error = exc
            if attempt == attempts:
                raise
        time.sleep(min(2 ** attempt, 10))
    raise RuntimeError(f"request failed after {attempts} attempts: {last_error}")


def fetch_releases(repos: dict[str, str] | None = None, per_page: int = 100, max_pages: int = 3, token: str | None = None) -> list[Release]:
    """Fetch release notes from the official GitHub releases API."""
    token = token or os.environ.get("GITHUB_TOKEN")
    repos = repos or DEFAULT_REPOS
    releases: list[Release] = []
    for tool, repo in repos.items():
        for page in range(1, max_pages + 1):
            params = urllib.parse.urlencode({"per_page": per_page, "page": page})
            url = f"https://api.github.com/repos/{repo}/releases?{params}"
            try:
                data = _request_json(url, token=token)
            except urllib.error.HTTPError as exc:
                raise RuntimeError(f"GitHub API failed for {repo} page {page}: HTTP {exc.code} {exc.reason}") from exc
            if not data:
                break
            for item in data:
                releases.append(Release(
                    tool=tool,
                    repo=repo,
                    tag=item.get("tag_name", ""),
                    name=item.get("name") or item.get("tag_name", ""),
                    published_at=item.get("published_at") or item.get("created_at") or "",
                    html_url=item.get("html_url", ""),
                    body=item.get("body") or "",
                ))
            time.sleep(0.1)
    return releases


def releases_to_json(releases: Iterable[Release]) -> str:
    return json.dumps([asdict(r) for r in releases], indent=2, sort_keys=True)


def releases_from_json(text: str) -> list[Release]:
    return [Release(**item) for item in json.loads(text)]
