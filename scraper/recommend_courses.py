#!/usr/bin/env python3
"""
Recommend NYU CAS courses by semantic similarity to a free-text query.

Loads embeddings.npy + course_index.json, encodes the query with the same
BGE model (with the recommended query prefix), and returns top-k by cosine
similarity. Optionally re-ranks with MMR for diversity.

Usage:
    python3 recommend_courses.py "machine learning with applications to biology"
    python3 recommend_courses.py "ancient greek philosophy" --k 5
    python3 recommend_courses.py "neural networks" --subject CSCI-UA
    python3 recommend_courses.py "data analysis" --mmr --mmr-lambda 0.6
"""

from __future__ import annotations
import argparse
import json
import sys

import numpy as np
from sentence_transformers import SentenceTransformer

# BGE-EN-v1.5 recommends prefixing the *query* (not passages) for retrieval.
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def mmr_rerank(query_vec: np.ndarray, doc_vecs: np.ndarray,
               candidate_idx: np.ndarray, k: int, lam: float) -> list[int]:
    """Maximal Marginal Relevance: balance relevance and diversity.
    All vectors assumed L2-normalized so cosine == dot."""
    selected: list[int] = []
    remaining = list(candidate_idx)
    rel = doc_vecs[candidate_idx] @ query_vec  # (N,)
    rel_map = {int(i): float(s) for i, s in zip(candidate_idx, rel)}

    while remaining and len(selected) < k:
        if not selected:
            best = max(remaining, key=lambda i: rel_map[i])
        else:
            sel_mat = doc_vecs[selected]  # (S, D)
            best, best_score = None, -1e9
            for i in remaining:
                redundancy = float(np.max(doc_vecs[i] @ sel_mat.T))
                score = lam * rel_map[i] - (1 - lam) * redundancy
                if score > best_score:
                    best, best_score = i, score
        selected.append(best)
        remaining.remove(best)
    return selected


def truncate(s: str, n: int) -> str:
    s = s.replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="Free-text description of what you want to learn")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--subject", default=None,
                    help="Restrict to a subject prefix, e.g. CSCI-UA")
    ap.add_argument("--mmr", action="store_true",
                    help="Re-rank top candidates with MMR for diversity")
    ap.add_argument("--mmr-lambda", type=float, default=0.5,
                    help="MMR trade-off: 1.0=pure relevance, 0.0=pure diversity")
    ap.add_argument("--candidate-pool", type=int, default=50,
                    help="How many top hits to consider before MMR rerank")
    ap.add_argument("--emb", default="embeddings.npy")
    ap.add_argument("--idx", default="course_index.json")
    ap.add_argument("--model", default="BAAI/bge-small-en-v1.5")
    args = ap.parse_args()

    emb: np.ndarray = np.load(args.emb)
    with open(args.idx, encoding="utf-8") as f:
        idx: list[dict] = json.load(f)
    if emb.shape[0] != len(idx):
        print(f"! emb rows ({emb.shape[0]}) != idx entries ({len(idx)})",
              file=sys.stderr)
        sys.exit(1)

    # Subject filter
    mask = np.ones(len(idx), dtype=bool)
    if args.subject:
        wanted = args.subject.upper()
        mask = np.array([m["subject_prefix"].upper() == wanted for m in idx])
        if not mask.any():
            print(f"! No courses match subject={args.subject}", file=sys.stderr)
            sys.exit(1)

    model = SentenceTransformer(args.model)
    q = model.encode(
        BGE_QUERY_PREFIX + args.query,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype(np.float32)

    # Cosine == dot product because everything is L2-normalized
    scores = emb @ q  # (N,)
    scores = np.where(mask, scores, -np.inf)

    # Sort all by descending cosine, take top-k (or pool for MMR)
    pool = max(args.candidate_pool, args.k) if args.mmr else args.k
    top_idx = np.argsort(-scores)[:pool]

    if args.mmr:
        chosen = mmr_rerank(q, emb, top_idx, args.k, args.mmr_lambda)
    else:
        chosen = list(top_idx[: args.k])

    print(f'Query: "{args.query}"')
    if args.subject:
        print(f'Filter: subject={args.subject}')
    if args.mmr:
        print(f'MMR rerank: λ={args.mmr_lambda} (pool={pool})')
    print()
    print(f'{"#":<3}{"score":<8}{"course":<14}{"title":<42}description')
    print("-" * 110)
    for rank, i in enumerate(chosen, 1):
        m = idx[i]
        s = float(emb[i] @ q)
        print(f'{rank:<3}{s:<8.3f}{m["course_code"]:<14}'
              f'{truncate(m["title"], 40):<42}'
              f'{truncate(m["description"], 50)}')


if __name__ == "__main__":
    main()
