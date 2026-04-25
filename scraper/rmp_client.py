"""
Thin RateMyProfessors GraphQL client.

Why a custom client? The PyPI `ratemyprofessor` library returns empty results
for NYU as of 2025 (it relies on a deprecated endpoint). RMP's frontend uses
GraphQL with a public Basic auth token (`test:test`) — this client mirrors
that.

Includes a MongoDB-backed cache of professor lookups so repeated calls for
the same name are cheap.

Usage as a library:
    from rmp_client import RMPClient
    rmp = RMPClient()
    profs = rmp.search_professors("Marsha Berger")        # list[ProfessorRating]
    p = rmp.best_match("Marsha Berger")                   # ProfessorRating | None

Usage as CLI:
    python rmp_client.py "Marsha Berger"
    python rmp_client.py "Marsha Berger" --department "Computer Science"
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable

import requests
from dotenv import load_dotenv

GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"
NYU_LEGACY_ID = 675
NYU_NODE_ID = "U2Nob29sLTY3NQ=="   # base64("School-675")

_AUTH = base64.b64encode(b"test:test").decode()
HEADERS = {
    "Authorization": f"Basic {_AUTH}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (LLUS-Hackathon)",
    "Origin": "https://www.ratemyprofessors.com",
    "Referer": "https://www.ratemyprofessors.com/",
}


@dataclass
class ProfessorRating:
    name: str
    rmp_id: str                  # RMP node id (base64-encoded)
    legacy_id: int | None
    first_name: str | None
    last_name: str | None
    department: str | None
    school_name: str | None
    avg_rating: float | None     # 0.0 – 5.0
    avg_difficulty: float | None # 1.0 – 5.0
    num_ratings: int
    would_take_again_percent: float | None
    profile_url: str | None
    fetched_at: str


_SEARCH_QUERY = """
query TeacherSearch($query: TeacherSearchQuery!) {
  newSearch {
    teachers(query: $query) {
      edges {
        node {
          id
          legacyId
          firstName
          lastName
          avgRating
          avgDifficulty
          numRatings
          wouldTakeAgainPercent
          department
          school { name }
        }
      }
    }
  }
}
"""


def _node_to_rating(node: dict) -> ProfessorRating:
    legacy = node.get("legacyId")
    profile_url = (
        f"https://www.ratemyprofessors.com/professor/{legacy}" if legacy else None
    )
    fn = (node.get("firstName") or "").strip()
    ln = (node.get("lastName") or "").strip()
    return ProfessorRating(
        name=f"{fn} {ln}".strip(),
        rmp_id=node["id"],
        legacy_id=legacy,
        first_name=fn or None,
        last_name=ln or None,
        department=node.get("department"),
        school_name=(node.get("school") or {}).get("name"),
        avg_rating=node.get("avgRating"),
        avg_difficulty=node.get("avgDifficulty"),
        num_ratings=node.get("numRatings") or 0,
        would_take_again_percent=node.get("wouldTakeAgainPercent"),
        profile_url=profile_url,
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )


class RMPClient:
    def __init__(self, school_node_id: str = NYU_NODE_ID, use_cache: bool = True,
                 timeout: int = 15):
        self.school_node_id = school_node_id
        self.timeout = timeout
        self._cache_coll = None
        if use_cache:
            try:
                from pymongo import MongoClient
                uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
                db_name = os.environ.get("MONGO_DB", "nyu_bulletins")
                client = MongoClient(uri, serverSelectionTimeoutMS=2000)
                client.admin.command("ping")
                self._cache_coll = client[db_name]["rmp_cache"]
                self._cache_coll.create_index("name_key", unique=True)
            except Exception:
                self._cache_coll = None  # mongo not available; that's fine

    # ---- public API ----

    def search_professors(self, name: str) -> list[ProfessorRating]:
        cached = self._cache_get(name)
        if cached is not None:
            return cached
        results = self._search_remote(name)
        self._cache_put(name, results)
        return results

    def best_match(self, name: str, department: str | None = None) -> ProfessorRating | None:
        candidates = self.search_professors(name)
        # 1) exact name match
        nm = name.lower().strip()
        exact = [p for p in candidates if p.name.lower() == nm]
        pool = exact or candidates
        # 2) optional department filter
        if department:
            dpt = department.lower()
            pool = [p for p in pool if (p.department or "").lower().startswith(dpt)] or pool
        # 3) prefer professor with most ratings (stable signal)
        pool = sorted(pool, key=lambda p: (p.num_ratings or 0), reverse=True)
        return pool[0] if pool else None

    def rate_many(self, names: Iterable[str], department: str | None = None) -> dict[str, ProfessorRating | None]:
        out: dict[str, ProfessorRating | None] = {}
        for n in names:
            try:
                out[n] = self.best_match(n, department=department)
            except Exception as e:
                print(f"[warn] RMP lookup failed for {n!r}: {e}", file=sys.stderr)
                out[n] = None
            time.sleep(0.2)   # be polite
        return out

    # ---- internals ----

    def _search_remote(self, name: str) -> list[ProfessorRating]:
        payload = {
            "query": _SEARCH_QUERY,
            "variables": {"query": {"text": name, "schoolID": self.school_node_id}},
        }
        for attempt in range(3):
            try:
                r = requests.post(GRAPHQL_URL, json=payload, headers=HEADERS,
                                  timeout=self.timeout)
                r.raise_for_status()
                data = r.json()
                if "errors" in data:
                    raise RuntimeError(data["errors"])
                edges = (
                    data.get("data", {}).get("newSearch", {}).get("teachers", {}).get("edges")
                    or []
                )
                return [_node_to_rating(e["node"]) for e in edges]
            except (requests.RequestException, RuntimeError) as e:
                if attempt == 2:
                    raise
                time.sleep(1.5 * (attempt + 1))
        return []

    def _cache_key(self, name: str) -> str:
        return name.lower().strip()

    def _cache_get(self, name: str) -> list[ProfessorRating] | None:
        if self._cache_coll is None:
            return None
        doc = self._cache_coll.find_one({"name_key": self._cache_key(name)})
        if doc and "results" in doc:
            return [ProfessorRating(**r) for r in doc["results"]]
        return None

    def _cache_put(self, name: str, results: list[ProfessorRating]) -> None:
        if self._cache_coll is None:
            return
        self._cache_coll.update_one(
            {"name_key": self._cache_key(name)},
            {"$set": {
                "name_key": self._cache_key(name),
                "query_name": name,
                "results": [asdict(r) for r in results],
                "cached_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True,
        )


def render(profs: list[ProfessorRating]) -> None:
    if not profs:
        print("(no matches)")
        return
    print(f"{'Name':<28} {'Dept':<28} {'Rating':>6} {'Diff':>5} {'#':>4}  Profile")
    print("-" * 100)
    for p in profs:
        rating = f"{p.avg_rating:.2f}" if p.avg_rating else "—"
        diff = f"{p.avg_difficulty:.2f}" if p.avg_difficulty else "—"
        print(f"{p.name[:27]:<28} {(p.department or '')[:27]:<28} "
              f"{rating:>6} {diff:>5} {p.num_ratings:>4}  {p.profile_url or ''}")


def main() -> int:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="professor name to search")
    ap.add_argument("--department", default=None)
    ap.add_argument("--best", action="store_true", help="only print best match")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    rmp = RMPClient(use_cache=not args.no_cache)
    if args.best:
        p = rmp.best_match(args.name, department=args.department)
        if p is None:
            print("(no match)")
            return 1
        print(json.dumps(asdict(p), indent=2))
    else:
        profs = rmp.search_professors(args.name)
        render(profs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
