"""
NYU CAS course catalog + prerequisite scraper.

Crawls https://bulletins.nyu.edu/courses/<subject>/ for each undergrad subject
and stores per-course catalog data into MongoDB collection `course_catalog`.

Schema:
    {
      _id: "CSCI-UA 102",
      code: "CSCI-UA 102",
      subject: "CSCI-UA",
      number: "102",
      title: "Data Structures",
      credits: "4",
      typically_offered: "Fall, Spring, and Summer terms",
      grading: "CAS Graded",
      description: "...",
      prereq_text: "Prerequisites: CSCI-UA 101 with a Minimum Grade of C ...",
      prereq_codes: ["CSCI-UA 101"],   # logical structure flattened to a list
      url: "https://bulletins.nyu.edu/courses/csci_ua/",
      scraped_at: "..."
    }

Usage:
    python scrape_prereqs.py                # all CAS undergrad subjects
    python scrape_prereqs.py --subject csci_ua
    python scrape_prereqs.py --dry-run --json /tmp/csci.json
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

import requests
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
from tqdm import tqdm

BASE_URL = "https://bulletins.nyu.edu"
COURSES_INDEX = f"{BASE_URL}/courses/"
USER_AGENT = "Mozilla/5.0 (compatible; LLUS-Hackathon-Scraper/1.0)"
TIMEOUT = 30
SLEEP_BETWEEN = 0.3

# Match e.g. "/courses/csci_ua/" (CAS undergrad)
CAS_UA_HREF_RE = re.compile(r"^/courses/[a-z]+_ua/?$")


@dataclass
class Course:
    code: str
    subject: str
    number: str
    title: str | None
    credits: str | None
    typically_offered: str | None
    grading: str | None
    description: str | None
    prereq_text: str | None
    prereq_codes: list[str] = field(default_factory=list)
    url: str = ""
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


_session: requests.Session | None = None


def session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        s.headers.update({"User-Agent": USER_AGENT})
        _session = s
    return _session


def fetch(url: str, retries: int = 3) -> str:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            r = session().get(url, timeout=TIMEOUT)
            r.raise_for_status()
            return r.text
        except (requests.RequestException, ConnectionError) as e:
            last = e
            time.sleep(1.0 * (attempt + 1))
    assert last is not None
    raise last


def discover_subjects() -> list[str]:
    """Find all CAS undergrad subject paths (ending in _ua/)."""
    html = fetch(COURSES_INDEX)
    soup = BeautifulSoup(html, "html.parser")
    paths: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].split("#", 1)[0]
        if CAS_UA_HREF_RE.match(href):
            slug = href.strip("/").rsplit("/", 1)[-1]
            paths.add(slug)
    return sorted(paths)


def _text(el: Tag | None) -> str | None:
    if el is None:
        return None
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() or None


_PREREQ_PREFIX_RE = re.compile(r"^(Prerequisites?|Pre-?req(uisite)?s?)\s*:\s*",
                                re.IGNORECASE)


def _parse_prereq(extra_text: str) -> tuple[str | None, str | None]:
    """Return (prereq_text, remaining_description).

    The bulletin packs prereq + description into one .courseblockextra div.
    Format: 'Prerequisite(s): <expr>. <description>...' — split at the first
    sentence-ending period that closes the prereq expression.
    """
    if not extra_text:
        return None, extra_text or None
    m = _PREREQ_PREFIX_RE.match(extra_text)
    if not m:
        return None, extra_text

    rest = extra_text[m.end():]
    # Find the end of the prereq expression: typically ends with a period
    # followed by a capitalized word (start of description). Use a heuristic.
    # Try: split at the first ". " whose next non-space char is uppercase.
    end_idx: int | None = None
    for match in re.finditer(r"\.\s+(?=[A-Z])", rest):
        # Skip "etc." or single-letter abbreviations
        prev = rest[max(0, match.start() - 4): match.start()]
        if prev.lower().endswith(("etc", " e.g", " i.e", " ph.d", " m.s", " b.s")):
            continue
        end_idx = match.end()
        break

    if end_idx is None:
        return rest.strip().rstrip(".") + ".", None
    prereq = rest[:end_idx].strip()
    desc = rest[end_idx:].strip() or None
    return prereq, desc


def parse_subject_page(subject_slug: str, html: str) -> list[Course]:
    soup = BeautifulSoup(html, "html.parser")
    url = f"{BASE_URL}/courses/{subject_slug}/"
    courses: list[Course] = []

    for block in soup.select("div.courseblock"):
        code_el = block.select_one(".detail-code")
        title_el = block.select_one(".detail-title")
        hours_el = block.select_one(".detail-hours_html")
        offered_el = block.select_one(".detail-typically_offered")
        grading_el = block.select_one(".detail-grading")
        extra_el = block.select_one(".courseblockextra")

        code = _text(code_el)
        if not code:
            continue
        # Normalize: "CSCI-UA 102" — replace nbsp etc.
        code_norm = re.sub(r"\s+", " ", code).strip()
        m_code = re.match(r"([A-Z]{2,5}-[A-Z]{2})\s+(\d+[A-Z]?)", code_norm)
        if not m_code:
            continue
        subject_code = m_code.group(1)
        number = m_code.group(2)

        title = _text(title_el)

        credits_raw = _text(hours_el) or ""
        m_cred = re.search(r"(\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)\s*Credits?",
                            credits_raw, re.IGNORECASE)
        credits = m_cred.group(1) if m_cred else None

        offered_raw = _text(offered_el) or ""
        offered = re.sub(r"^Typically offered\s*", "", offered_raw, flags=re.I) or None

        grading_raw = _text(grading_el) or ""
        grading = re.sub(r"^Grading:\s*", "", grading_raw, flags=re.I) or None

        # Prereq can live in either:
        #   (a) a dedicated <span class="detail-prerequisites"> element  (newer format)
        #   (b) inline at the start of .courseblockextra                 (older format)
        prereq_text: str | None = None
        prereq_codes: list[str] = []
        description: str | None = None
        prereq_el = block.select_one(".detail-prerequisites")
        if prereq_el:
            raw = _text(prereq_el) or ""
            prereq_text = _PREREQ_PREFIX_RE.sub("", raw).strip() or None
            for a in prereq_el.select("a"):
                ref = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
                if ref and re.match(r"^[A-Z]{2,5}-[A-Z]{2}\s+\d+", ref):
                    if ref not in prereq_codes:
                        prereq_codes.append(ref)
            if extra_el:
                description = _text(extra_el)
        elif extra_el:
            extra_text = _text(extra_el) or ""
            prereq_text, description = _parse_prereq(extra_text)
            if prereq_text:
                for a in extra_el.select("a"):
                    ref = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
                    if (ref and re.match(r"^[A-Z]{2,5}-[A-Z]{2}\s+\d+", ref)
                            and ref in prereq_text and ref not in prereq_codes):
                        prereq_codes.append(ref)

        courses.append(Course(
            code=code_norm,
            subject=subject_code,
            number=number,
            title=title,
            credits=credits,
            typically_offered=offered,
            grading=grading,
            description=description,
            prereq_text=prereq_text,
            prereq_codes=prereq_codes,
            url=url,
        ))

    return courses


def get_collection():
    from pymongo import MongoClient

    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.environ.get("MONGO_DB", "nyu_bulletins")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    coll = client[db_name]["course_catalog"]
    coll.create_index("code", unique=True)
    coll.create_index("subject")
    return coll


def upsert(coll, course: Course) -> None:
    d = asdict(course)
    d["_id"] = course.code
    coll.update_one({"_id": course.code}, {"$set": d}, upsert=True)


def main() -> int:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", help="single subject slug e.g. csci_ua")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", help="dump to JSON")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    if args.subject:
        subjects = [args.subject]
    else:
        print(f"[info] discovering CAS undergrad subjects from {COURSES_INDEX}")
        subjects = discover_subjects()
        print(f"[info] found {len(subjects)} subjects")
    if args.limit:
        subjects = subjects[: args.limit]

    coll = None
    if not args.dry_run:
        try:
            coll = get_collection()
            print(f"[info] connected to MongoDB → {coll.full_name}")
        except Exception as e:
            print(f"[err] mongo unavailable: {e}", file=sys.stderr)
            print("[info] continuing in dry-run mode")

    all_courses: list[Course] = []
    for slug in tqdm(subjects, desc="subjects"):
        url = f"{BASE_URL}/courses/{slug}/"
        try:
            html = fetch(url)
        except Exception as e:
            print(f"[warn] {slug}: {e}", file=sys.stderr)
            continue
        try:
            courses = parse_subject_page(slug, html)
        except Exception as e:
            print(f"[warn] parse {slug}: {e}", file=sys.stderr)
            continue
        for c in courses:
            all_courses.append(c)
            if coll is not None:
                try:
                    upsert(coll, c)
                except Exception as e:
                    print(f"[warn] upsert {c.code}: {e}", file=sys.stderr)
        time.sleep(SLEEP_BETWEEN)

    n_with_prereq = sum(1 for c in all_courses if c.prereq_text)
    print(f"[info] {len(all_courses)} courses scraped, {n_with_prereq} have prereqs")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in all_courses], f, ensure_ascii=False, indent=2)
        print(f"[info] dumped → {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
