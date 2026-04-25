"""Course recommendation via semantic search over BGE embeddings."""

from __future__ import annotations
import json
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

# BGE-EN-v1.5 recommends prefixing the query (not passages) for retrieval.
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class CourseRecommender:
    def __init__(
        self,
        emb_path: str,
        idx_path: str,
        model_name: str = "BAAI/bge-small-en-v1.5",
    ) -> None:
        self.emb = np.load(emb_path)
        with open(idx_path, encoding="utf-8") as f:
            self.idx = json.load(f)
        if self.emb.shape[0] != len(self.idx):
            raise ValueError(
                f"emb rows ({self.emb.shape[0]}) != idx entries ({len(self.idx)})"
            )
        self.model = SentenceTransformer(model_name)

    def recommend(
        self,
        query: str,
        k: int = 5,
        subject: Optional[str] = None,
    ) -> list[dict]:
        q = self.model.encode(
            BGE_QUERY_PREFIX + query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype(np.float32)

        # cosine == dot since everything is L2-normalized
        scores = self.emb @ q

        if subject:
            wanted = subject.upper()
            mask = np.array(
                [m["subject_prefix"].upper() == wanted for m in self.idx]
            )
            scores = np.where(mask, scores, -np.inf)

        top = np.argsort(-scores)[:k]
        return [
            {
                "course_code": self.idx[int(i)]["course_code"],
                "subject_prefix": self.idx[int(i)]["subject_prefix"],
                "title": self.idx[int(i)]["title"],
                "description": self.idx[int(i)]["description"],
                "score": float(scores[int(i)]),
            }
            for i in top
            if scores[int(i)] != -np.inf
        ]
