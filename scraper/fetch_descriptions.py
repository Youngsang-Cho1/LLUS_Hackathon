#!/usr/bin/env python3
"""
Fetch course descriptions from NYU bulletins.nyu.edu details endpoint.

Reads cas_courses.csv (produced by nyu_cas_scraper.py), picks one CRN per
unique course_code, calls route=details once per course, and writes a JSON
mapping {course_code: {title, description, subject_prefix}}.

Usage:
    python3 fetch_descriptions.py
    python3 fetch_descriptions.py --term 1268 --input cas_courses.csv \
                                  --output course_descriptions.json
"""

from __future__ import annotations
import argparse
import csv
import json
import sys
import time
import urllib.request
import urllib.error
from typing import Dict

DETAILS_URL = "https://bulletins.nyu.edu/class-search/api/?page=fose&route=details"


def post_json(url: str, payload: dict, timeout: int = 30) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (CASCourseScraper/1.0)",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_details(course_code: str, crn: str, term: str,
                  retry_delay: float = 2.0) -> dict:
    payload = {
        "group": f"code:{course_code}",
        "key": f"crn:{crn}",
        "srcdb": term,
        "matched": f"crn:{crn}",
    }
    try:
        return post_json(DETAILS_URL, payload)
    except urllib.error.HTTPError as e:
        if e.code in (429, 503):
            print(f"  ! HTTP {e.code} on {course_code} — backing off "
                  f"{retry_delay}s and retrying once", file=sys.stderr)
            time.sleep(retry_delay)
            try:
                return post_json(DETAILS_URL, payload)
            except Exception as e2:
                print(f"  ! Retry failed on {course_code}: {e2}. STOPPING.",
                      file=sys.stderr)
                sys.exit(2)
        print(f"  ! HTTP {e.code} on {course_code}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"  ! Net error on {course_code}: {e}", file=sys.stderr)
        return {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="cas_courses.csv")
    ap.add_argument("--output", default="course_descriptions.json")
    ap.add_argument("--term", default="1268")
    ap.add_argument("--delay", type=float, default=0.4)
    args = ap.parse_args()

    with open(args.input, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # One CRN per unique course_code (first occurrence wins)
    course_to_crn: Dict[str, Dict[str, str]] = {}
    for r in rows:
        code = r["course_code"].strip()
        if code and code not in course_to_crn:
            course_to_crn[code] = {
                "crn": r["crn"].strip(),
                "subject_prefix": r["subject_prefix"].strip(),
            }

    n = len(course_to_crn)
    print(f"Fetching descriptions for {n} unique courses (term {args.term})…")

    out: Dict[str, Dict[str, str]] = {}
    n_with_desc = 0
    for i, (code, meta) in enumerate(course_to_crn.items(), 1):
        d = fetch_details(code, meta["crn"], args.term)
        title = (d.get("title") or "").strip()
        desc = (d.get("description") or "").strip()
        out[code] = {
            "subject_prefix": meta["subject_prefix"],
            "title": title,
            "description": desc,
        }
        if desc:
            n_with_desc += 1
        if i % 25 == 0 or i == n:
            print(f"  [{i:4d}/{n}] {code:<18s} desc_len={len(desc):4d}")
        time.sleep(args.delay)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Wrote {len(out)} courses to {args.output}")
    print(f"  With description : {n_with_desc}")
    print(f"  Empty description: {len(out) - n_with_desc}")


if __name__ == "__main__":
    main()
