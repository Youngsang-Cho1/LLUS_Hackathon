#!/usr/bin/env python3
"""
Embed course descriptions with BAAI/bge-small-en-v1.5.

Reads course_descriptions.json, strips HTML, encodes title+description,
writes embeddings.npy (float32, L2-normalized) and course_index.json.

Usage:
    python3 embed_courses.py
    python3 embed_courses.py --input course_descriptions.json \
                             --out-emb embeddings.npy \
                             --out-idx course_index.json
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from html.parser import HTMLParser

import numpy as np
from sentence_transformers import SentenceTransformer


class _Stripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        self._chunks.append(data)

    def text(self) -> str:
        return "".join(self._chunks)


def strip_html(s: str) -> str:
    if not s:
        return ""
    p = _Stripper()
    p.feed(s)
    return re.sub(r"\s+", " ", p.text()).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="course_descriptions.json")
    ap.add_argument("--out-emb", default="embeddings.npy")
    ap.add_argument("--out-idx", default="course_index.json")
    ap.add_argument("--model", default="BAAI/bge-small-en-v1.5")
    ap.add_argument("--batch-size", type=int, default=32)
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data: dict = json.load(f)

    codes: list[str] = []
    texts: list[str] = []
    metas: list[dict] = []
    skipped = 0

    for code, v in data.items():
        title = strip_html(v.get("title", ""))
        desc = strip_html(v.get("description", ""))
        if not desc and not title:
            skipped += 1
            continue
        text = f"{title}. {desc}".strip(". ").strip()
        codes.append(code)
        texts.append(text)
        metas.append({
            "course_code": code,
            "subject_prefix": v.get("subject_prefix", ""),
            "title": title,
            "description": desc,
        })

    print(f"Encoding {len(texts)} courses with {args.model} "
          f"(skipped {skipped} empty)…", file=sys.stderr)

    model = SentenceTransformer(args.model)
    emb = model.encode(
        texts,
        batch_size=args.batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,  # so cosine == dot product
        convert_to_numpy=True,
    ).astype(np.float32)

    np.save(args.out_emb, emb)
    with open(args.out_idx, "w", encoding="utf-8") as f:
        json.dump(metas, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Wrote {emb.shape} → {args.out_emb}")
    print(f"✓ Wrote {len(metas)} entries → {args.out_idx}")
    print(f"  dtype={emb.dtype}, normalized=True (use dot product for cosine)")


if __name__ == "__main__":
    main()
