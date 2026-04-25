"""
NYU CAS Bulletin scraper.

Crawls https://bulletins.nyu.edu/undergraduate/arts-science/programs/,
discovers every undergraduate program (BA / BS / Minor / joint degrees),
extracts the Program Requirements (curriculum) for each track, and stores
the structured result into MongoDB.

Track detection handles two HTML patterns:
  - Between-table headings (h3/h4 between sc_courselist tables) — biology-ba style
  - In-table areaheader rows with concentration/track keywords — economics-ba style

MongoDB schema per document:
  program_slug, program_name, degree, url, track (null if none),
  track_index (null if none), common_sections, sections, raw_curriculum_text, scraped_at

Compound unique index: (program_slug, track)

Usage:
    cp .env.example .env
    pip install -r requirements.txt
    python scrape_cas.py
    python scrape_cas.py --dry-run
    python scrape_cas.py --slug mathematics-ba --json /tmp/out.json
    python scrape_cas.py --limit 10
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
from tqdm import tqdm

BASE_URL = "https://bulletins.nyu.edu"
INDEX_URL = f"{BASE_URL}/undergraduate/arts-science/programs/"
USER_AGENT = "Mozilla/5.0 (compatible; LLUS-Hackathon-Scraper/1.0)"
REQUEST_TIMEOUT = 30
SLEEP_BETWEEN = 0.4

TRACK_KW_RE = re.compile(r"\b(concentration|track|option|emphasis)\b", re.I)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class CourseRow:
    code: str | None
    title: str | None
    credits: str | None
    comment: str | None = None
    is_or_alternative: bool = False
    indent_level: int = 0


@dataclass
class RequirementSection:
    header: str | None
    courses: list[CourseRow] = field(default_factory=list)


@dataclass
class TrackDocument:
    program_slug: str
    program_name: str
    degree: str | None
    url: str
    track: str | None            # None = no tracks on this page
    track_index: int | None      # 0-based ordering; None if no tracks
    common_sections: list[RequirementSection]   # shared before first track
    sections: list[RequirementSection]          # this track's own sections
    raw_curriculum_text: str | None
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

_session: requests.Session | None = None


def session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        s.headers.update({"User-Agent": USER_AGENT})
        _session = s
    return _session


def fetch(url: str, retries: int = 3, backoff: float = 1.5) -> str:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = session().get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except (requests.RequestException, ConnectionError) as e:
            last_exc = e
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
    assert last_exc is not None
    raise last_exc


# ---------------------------------------------------------------------------
# Index discovery
# ---------------------------------------------------------------------------

PROGRAM_HREF_RE = re.compile(r"^/undergraduate/arts-science/programs/[a-z0-9\-]+/?$")


def discover_program_urls(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].split("#", 1)[0]
        if PROGRAM_HREF_RE.match(href):
            if href.rstrip("/") == "/undergraduate/arts-science/programs":
                continue
            urls.add(urljoin(BASE_URL, href if href.endswith("/") else href + "/"))
    return sorted(urls)


def slug_from_url(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def degree_from_slug(slug: str) -> str | None:
    parts = slug.split("-")
    if len(parts) >= 2 and parts[-2] in {"ba", "bs"} and parts[-1] in {"ba", "bs", "dds", "md"}:
        return f"{parts[-2].upper()}-{parts[-1].upper()}"
    last = parts[-1]
    if last in {"ba", "bs", "ma", "ms", "phd"}:
        return last.upper()
    if last == "minor":
        return "Minor"
    return None


# ---------------------------------------------------------------------------
# Curriculum parsing
# ---------------------------------------------------------------------------

def find_curriculum_container(soup: BeautifulSoup) -> Tag | None:
    for cid in (
        "curriculumtextcontainer",
        "requirementstextcontainer",
        "programrequirementstextcontainer",
    ):
        node = soup.find(id=cid)
        if node:
            return node
    table = soup.find("table", class_="sc_courselist")
    if table:
        return table.find_parent(["div", "section"]) or table
    return None


def extract_program_name(soup: BeautifulSoup) -> str:
    h1 = soup.find(["h1"], class_=re.compile(r"page-?title", re.I)) or soup.find("h1")
    return h1.get_text(strip=True) if h1 else ""


def _cell_text(td: Tag | None) -> str:
    if td is None:
        return ""
    return re.sub(r"\s+", " ", td.get_text(" ", strip=True)).strip()


def parse_courselist(table: Tag) -> list[RequirementSection]:
    sections: list[RequirementSection] = []
    current = RequirementSection(header=None)

    for tr in table.find_all("tr"):
        classes = set(tr.get("class") or [])

        if "areaheader" in classes or "plangridtotal" in classes:
            text = _cell_text(tr.find(["td", "th"]))
            if current.courses or current.header:
                sections.append(current)
            current = RequirementSection(header=text or None)
            continue

        comment_td = tr.find("td", class_=re.compile(r"courselistcomment"))
        if comment_td and not tr.find("td", class_=re.compile(r"codecol")):
            text = _cell_text(comment_td)
            if text:
                current.courses.append(CourseRow(code=None, title=None, credits=None, comment=text))
            continue

        code_td = tr.find("td", class_=re.compile(r"codecol"))
        title_td = None
        if code_td:
            sibling = code_td
            while True:
                sibling = sibling.find_next_sibling("td")
                if sibling is None:
                    break
                if "hourscol" in set(sibling.get("class") or []):
                    continue
                title_td = sibling
                break
        hours_td = tr.find("td", class_=re.compile(r"hourscol"))

        if not (code_td or title_td or hours_td):
            continue

        code = _cell_text(code_td) or None
        title = _cell_text(title_td) or None
        credits = _cell_text(hours_td) or None

        is_or = False
        if code and code.lower().startswith("or "):
            is_or = True
            code = code[3:].strip() or None

        indent = 0
        if code_td is not None:
            for cls in code_td.get("class") or []:
                m = re.match(r"codecol(\d+)", cls)
                if m:
                    indent = int(m.group(1))

        current.courses.append(CourseRow(
            code=code, title=title, credits=credits,
            is_or_alternative=is_or, indent_level=indent,
        ))

    if current.courses or current.header:
        sections.append(current)
    return sections


# ---------------------------------------------------------------------------
# Track detection
# ---------------------------------------------------------------------------

def clean_track_name(header: str) -> str:
    """'Policy Concentration Requirements' → 'Policy'"""
    cleaned = re.sub(
        r"[\s,]+(Concentration|Track|Minor|Requirements?)\b.*$",
        "", header.strip(), flags=re.I,
    ).strip()
    return cleaned or header.strip()


def get_ordered_blocks(container: Tag) -> list[tuple[str, Tag]]:
    """
    Walk the curriculum container and return (type, element) pairs in
    document order, where type is 'heading' or 'table'.
    Only h3/h4 elements NOT inside a table, and sc_courselist tables.
    """
    results: list[tuple[str, Tag]] = []
    seen: set[int] = set()
    for el in container.find_all(["h3", "h4", "table"], recursive=True):
        if id(el) in seen:
            continue
        seen.add(id(el))
        if el.name in ("h3", "h4"):
            if el.find_parent("table"):
                continue
            text = el.get_text(strip=True)
            if text:
                results.append(("heading", el))
        elif el.name == "table" and "sc_courselist" in (el.get("class") or []):
            results.append(("table", el))
    return results


def _filter_heading_tracks(
    blocks: list[tuple[str, Tag]],
    between_headings: list[tuple[int, Tag]],
) -> list[tuple[int, Tag]]:
    """Keep only headings that are immediately followed by at least one sc_courselist
    table before the next heading. This filters out 'Mathematics Requirement',
    'Prerequisites', etc. that are just section labels without their own tables."""
    n = len(blocks)
    positions = [idx for idx, _ in between_headings] + [n]
    valid = []
    for j, (h_idx, h_el) in enumerate(between_headings):
        next_h_idx = positions[j + 1]
        has_table = any(
            kind == "table" and h_idx < i < next_h_idx
            for i, (kind, _) in enumerate(blocks)
        )
        if has_table:
            valid.append((h_idx, h_el))
    return valid


def _split_by_heading_tracks(
    blocks: list[tuple[str, Tag]],
    between_headings: list[tuple[int, Tag]],
) -> tuple[list[RequirementSection], list[tuple[str, list[RequirementSection]]]]:
    """
    biology-ba / spanish-portuguese-ba style.
    Tables before the first between-heading → common_sections.
    Each (heading → tables until next heading) group → one track.
    """
    first_between_idx = between_headings[0][0]

    common_sections: list[RequirementSection] = []
    for i, (kind, el) in enumerate(blocks):
        if kind == "table" and i < first_between_idx:
            common_sections.extend(parse_courselist(el))

    heading_positions = [idx for idx, _ in between_headings] + [len(blocks)]
    tracks: list[tuple[str, list[RequirementSection]]] = []

    for j, (h_idx, h_el) in enumerate(between_headings):
        next_h_idx = heading_positions[j + 1]
        track_name = h_el.get_text(strip=True)
        track_sections: list[RequirementSection] = []
        for i, (kind, el) in enumerate(blocks):
            if kind == "table" and h_idx < i < next_h_idx:
                track_sections.extend(parse_courselist(el))
        tracks.append((track_name, track_sections))

    return common_sections, tracks


def _split_by_section_tracks(
    all_sections: list[RequirementSection],
) -> tuple[list[RequirementSection], list[tuple[str, list[RequirementSection]]]]:
    """
    economics-ba style: areaheader rows with track/concentration keywords split sections.
    Sections before first track header → common.
    Each track header + following non-track sections → one track.
    """
    first_track_idx: int | None = None
    for i, s in enumerate(all_sections):
        if s.header and TRACK_KW_RE.search(s.header):
            first_track_idx = i
            break

    if first_track_idx is None:
        return all_sections, []

    common = all_sections[:first_track_idx]
    tracks: list[tuple[str, list[RequirementSection]]] = []
    current_name: str | None = None
    current_secs: list[RequirementSection] = []

    for s in all_sections[first_track_idx:]:
        if s.header and TRACK_KW_RE.search(s.header):
            if current_name is not None:
                tracks.append((current_name, current_secs))
            current_name = clean_track_name(s.header)
            current_secs = []
        else:
            if current_name is not None:
                current_secs.append(s)

    if current_name is not None:
        tracks.append((current_name, current_secs))

    return common, tracks


def build_track_documents(
    program_slug: str,
    program_name: str,
    degree: str | None,
    url: str,
    container: Tag,
) -> list[TrackDocument]:
    raw_text = re.sub(r"\n{3,}", "\n\n", container.get_text("\n", strip=True))
    now = datetime.now(timezone.utc).isoformat()

    def make_doc(
        track: str | None,
        track_index: int | None,
        common: list[RequirementSection],
        sections: list[RequirementSection],
    ) -> TrackDocument:
        return TrackDocument(
            program_slug=program_slug, program_name=program_name,
            degree=degree, url=url,
            track=track, track_index=track_index,
            common_sections=common, sections=sections,
            raw_curriculum_text=raw_text, scraped_at=now,
        )

    # --- Step 1: ordered blocks (h3/h4 headings + tables) ---
    blocks = get_ordered_blocks(container)
    table_indices = [i for i, (t, _) in enumerate(blocks) if t == "table"]

    if not table_indices:
        return [make_doc(None, None, [], [])]

    first_table_idx = table_indices[0]

    # --- Step 2: check for between-table headings (biology-ba style) ---
    between_headings = [
        (i, el) for i, (kind, el) in enumerate(blocks)
        if kind == "heading" and i > first_table_idx
    ]

    between_headings = _filter_heading_tracks(blocks, between_headings)

    use_heading_tracks = len(between_headings) >= 2 or (
        len(between_headings) == 1
        and TRACK_KW_RE.search(between_headings[0][1].get_text(strip=True))
    )

    if use_heading_tracks:
        common, tracks = _split_by_heading_tracks(blocks, between_headings)
        if tracks:
            return [
                make_doc(name, i, common, secs)
                for i, (name, secs) in enumerate(tracks)
            ]

    # --- Step 3: parse all tables flat, then check for in-table tracks ---
    all_sections: list[RequirementSection] = []
    for _, el in [(k, e) for k, e in blocks if k == "table"]:
        all_sections.extend(parse_courselist(el))

    common, tracks = _split_by_section_tracks(all_sections)
    if tracks:
        return [
            make_doc(name, i, common, secs)
            for i, (name, secs) in enumerate(tracks)
        ]

    # --- No tracks detected ---
    return [make_doc(None, None, [], all_sections)]


def parse_program_page(url: str, html: str) -> list[TrackDocument]:
    soup = BeautifulSoup(html, "html.parser")
    slug = slug_from_url(url)
    name = extract_program_name(soup)
    degree = degree_from_slug(slug)
    container = find_curriculum_container(soup)

    if container is None:
        now = datetime.now(timezone.utc).isoformat()
        return [TrackDocument(
            program_slug=slug, program_name=name, degree=degree, url=url,
            track=None, track_index=None,
            common_sections=[], sections=[],
            raw_curriculum_text=None, scraped_at=now,
        )]

    return build_track_documents(slug, name, degree, url, container)


# ---------------------------------------------------------------------------
# Mongo
# ---------------------------------------------------------------------------

def get_collection():
    from pymongo import MongoClient

    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.environ.get("MONGO_DB", "nyu_bulletins")
    coll_name = os.environ.get("MONGO_COLLECTION", "cas_programs")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    coll = client[db_name][coll_name]
    coll.create_index([("program_slug", 1), ("track", 1)], unique=True)
    coll.create_index("degree")
    return coll


def upsert(coll, doc: TrackDocument) -> None:
    d = asdict(doc)
    coll.update_one(
        {"program_slug": doc.program_slug, "track": doc.track},
        {"$set": d},
        upsert=True,
    )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def iter_track_documents(urls: Iterable[str]) -> Iterable[TrackDocument]:
    for url in urls:
        try:
            html = fetch(url)
        except Exception as e:
            print(f"[warn] failed to fetch {url}: {e}", file=sys.stderr)
            continue
        try:
            yield from parse_program_page(url, html)
        except Exception as e:
            print(f"[warn] failed to parse {url}: {e}", file=sys.stderr)
        time.sleep(SLEEP_BETWEEN)


def main() -> int:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="do not write to MongoDB")
    ap.add_argument("--json", help="also dump scraped records to this JSON file")
    ap.add_argument("--slug", help="only scrape a single program by slug")
    ap.add_argument("--limit", type=int, help="limit number of programs (for testing)")
    args = ap.parse_args()

    print(f"[info] discovering programs from {INDEX_URL}")
    index_html = fetch(INDEX_URL)
    urls = discover_program_urls(index_html)
    print(f"[info] found {len(urls)} program URLs")

    if args.slug:
        urls = [u for u in urls if slug_from_url(u) == args.slug]
        if not urls:
            print(f"[err] no program with slug={args.slug}", file=sys.stderr)
            return 2
    if args.limit:
        urls = urls[: args.limit]

    coll = None
    if not args.dry_run:
        try:
            coll = get_collection()
            print(f"[info] connected to MongoDB → {coll.full_name}")
        except Exception as e:
            print(f"[err] MongoDB unavailable: {e}", file=sys.stderr)
            print("[info] continuing in dry-run mode", file=sys.stderr)
            coll = None

    docs: list[TrackDocument] = []
    for doc in tqdm(iter_track_documents(urls), total=len(urls), desc="scrape"):
        docs.append(doc)
        if coll is not None:
            try:
                upsert(coll, doc)
            except Exception as e:
                print(f"[warn] mongo upsert failed for {doc.program_slug}/{doc.track}: {e}", file=sys.stderr)

    n_programs = len({d.program_slug for d in docs})
    n_with_tracks = len({d.program_slug for d in docs if d.track is not None})
    n_total_docs = len(docs)
    print(f"[info] {n_programs} programs → {n_total_docs} track-documents")
    print(f"[info] programs with tracks: {n_with_tracks}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump([asdict(d) for d in docs], f, ensure_ascii=False, indent=2)
        print(f"[info] dumped JSON → {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
