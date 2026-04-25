"""
NYU CAS College Core Curriculum scraper.

Fetches https://bulletins.nyu.edu/undergraduate/arts-science/college-core-curriculum/
and stores its components into the `cas_core` collection in MongoDB.

These are the requirements EVERY CAS undergraduate must complete in addition
to their major-specific requirements.

Schema:
    {
      _id: "cas_core",
      name: "CAS College Core Curriculum",
      url: "...",
      components: [
        { category, parent, credits, description, course_codes, code_pattern },
        ...
      ],
      raw_text: "...",
      scraped_at: "..."
    }

Usage:
    python scrape_core.py
    python scrape_core.py --dry-run --json /tmp/core.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv

CORE_URL = "https://bulletins.nyu.edu/undergraduate/arts-science/college-core-curriculum/"
USER_AGENT = "Mozilla/5.0 (compatible; LLUS-Hackathon-Scraper/1.0)"


@dataclass
class CoreComponent:
    category: str                # e.g. "Texts and Ideas"
    parent: str | None           # e.g. "Foundations of Contemporary Culture"
    credits: str | None          # e.g. "4" or "varies"
    description: str             # prose describing the requirement
    course_codes: list[str]      # specific courses listed in tables (if any)
    code_pattern: str | None     # e.g. "CORE-UA 4XX" hint, if hardcoded


@dataclass
class CoreCurriculumDoc:
    name: str
    url: str
    components: list[CoreComponent]
    raw_text: str
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Hint mapping for FCC / FSI sub-components — derived from the bulletin prose.
# We keep this structured because the page itself doesn't list explicit course
# codes for each category; students pick any course matching the code prefix.
CODE_PATTERN_HINTS: dict[str, str] = {
    "Texts and Ideas": "CORE-UA 4XX",
    "Cultures and Contexts": "CORE-UA 5XX",
    "Societies and the Social Sciences": "CORE-UA 6XX",
    "Expressive Culture": "CORE-UA 7XX",
    "Quantitative Reasoning": "CORE-UA 1XX",
    "Physical Science": "CORE-UA 2XX",
    "Life Science": "CORE-UA 3XX",
    "The First-Year Seminar": "FYSEM-UA",
    "Expository Writing": "EXPOS-UA 1",
}


def fetch(url: str) -> str:
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    return r.text


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _collect_text_until_next_heading(start: Tag) -> str:
    """Concatenate sibling text content until the next h2/h3/h4."""
    parts: list[str] = []
    sib = start.next_sibling
    while sib is not None:
        if isinstance(sib, Tag):
            if sib.name in ("h2", "h3", "h4"):
                break
            parts.append(sib.get_text(" ", strip=True))
        else:
            t = str(sib).strip()
            if t:
                parts.append(t)
        sib = sib.next_sibling
    return _clean(" ".join(p for p in parts if p))


def _extract_table_codes(start: Tag) -> list[str]:
    """If the next sc_courselist table appears before the next heading,
    extract its course codes."""
    sib = start.next_sibling
    while sib is not None:
        if isinstance(sib, Tag):
            if sib.name in ("h2", "h3", "h4"):
                return []
            if sib.name == "table" and "sc_courselist" in (sib.get("class") or []):
                codes = []
                for tr in sib.find_all("tr"):
                    code_td = tr.find("td", class_=re.compile(r"codecol"))
                    if code_td:
                        c = _clean(code_td.get_text(" ", strip=True))
                        if c:
                            codes.append(c.lstrip("or ").strip())
                return codes
            # also look for tables nested inside divs
            t = sib.find("table", class_="sc_courselist") if hasattr(sib, "find") else None
            if t:
                codes = []
                for tr in t.find_all("tr"):
                    code_td = tr.find("td", class_=re.compile(r"codecol"))
                    if code_td:
                        c = _clean(code_td.get_text(" ", strip=True))
                        if c:
                            codes.append(c.lstrip("or ").strip())
                return codes
        sib = sib.next_sibling
    return []


def parse_core_page(html: str) -> CoreCurriculumDoc:
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find(id="textcontainer") or soup
    raw_text = re.sub(r"\n{3,}", "\n\n", container.get_text("\n", strip=True))

    # Pre-scan: find FYSEM-UA course list (under second h2 "First-Year Seminar Program")
    fysem_codes: list[str] = []
    for table in container.find_all("table", class_="sc_courselist"):
        for tr in table.find_all("tr"):
            code_td = tr.find("td", class_=re.compile(r"codecol"))
            if code_td:
                c = _clean(code_td.get_text(" ", strip=True))
                if c.startswith("FYSEM-UA"):
                    fysem_codes.append(c.lstrip("or ").strip())

    components: list[CoreComponent] = []
    current_parent: str | None = None
    in_components_section = False

    for el in container.find_all(["h2", "h3", "h4"], recursive=True):
        if el.find_parent("table"):
            continue
        text = _clean(el.get_text(strip=True))
        if not text:
            continue

        if el.name == "h2":
            # Only collect components within the "Components" h2 section
            in_components_section = (text.lower() == "components")
            current_parent = None
            continue

        if not in_components_section:
            continue

        if el.name == "h3":
            description = _collect_text_until_next_heading(el)
            codes = _extract_table_codes(el)
            pattern = CODE_PATTERN_HINTS.get(text)
            # Attach pre-scanned FYSEM codes to the First-Year Seminar component
            if text == "The First-Year Seminar" and not codes:
                codes = fysem_codes
            components.append(CoreComponent(
                category=text, parent=None,
                credits="4" if text in ("The First-Year Seminar", "Expository Writing") else None,
                description=description,
                course_codes=codes,
                code_pattern=pattern,
            ))
            current_parent = text
            continue

        if el.name == "h4":
            # Skip non-category h4 labels
            if text.lower() in {"more information", "requirement", "exemptions", "courses",
                                 "general information", "policies"}:
                continue
            description = _collect_text_until_next_heading(el)
            codes = _extract_table_codes(el)
            pattern = CODE_PATTERN_HINTS.get(text)
            components.append(CoreComponent(
                category=text,
                parent=current_parent,
                credits="4",
                description=description,
                course_codes=codes,
                code_pattern=pattern,
            ))

    return CoreCurriculumDoc(
        name="CAS College Core Curriculum",
        url=CORE_URL,
        components=components,
        raw_text=raw_text,
    )


def upsert_to_mongo(doc: CoreCurriculumDoc) -> str:
    from pymongo import MongoClient

    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.environ.get("MONGO_DB", "nyu_bulletins")
    coll_name = "cas_core"
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    coll = client[db_name][coll_name]
    coll.update_one(
        {"_id": "cas_core"},
        {"$set": {**asdict(doc), "_id": "cas_core"}},
        upsert=True,
    )
    return f"{db_name}.{coll_name}"


def main() -> int:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", help="dump to JSON file")
    args = ap.parse_args()

    print(f"[info] fetching {CORE_URL}")
    html = fetch(CORE_URL)
    doc = parse_core_page(html)
    print(f"[info] parsed {len(doc.components)} components")
    for c in doc.components:
        prefix = f"  ({c.parent}) " if c.parent else "  "
        codes = f"  codes={len(c.course_codes)}" if c.course_codes else ""
        pat = f"  pattern={c.code_pattern}" if c.code_pattern else ""
        print(f"{prefix}{c.category}  credits={c.credits}{pat}{codes}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(asdict(doc), f, ensure_ascii=False, indent=2)
        print(f"[info] dumped JSON → {args.json}")

    if not args.dry_run:
        try:
            target = upsert_to_mongo(doc)
            print(f"[info] upserted to {target}")
        except Exception as e:
            print(f"[err] mongo upsert failed: {e}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
