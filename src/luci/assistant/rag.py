"""Search in the assistant's documentation (RAG), so only what a question needs is sent.

Two searches are combined:

* BM25 on words (local, free, instant);
* OpenAI embeddings (meaning: "my molecules give no conformers" ~ "CSEARCH failed").
  Document vectors are computed once and cached in the LUCI folder; per question
  only the question's vector is computed. Without a connection, BM25 alone.

Results are merged by rank (Reciprocal Rank Fusion). Pieces about the program
on screen weigh more, but every program can be found: the assistant must
notice when the user is in the wrong program.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
import re
import threading
import unicodedata

from . import config as cfg
from . import knowledge as kb

STOPWORDS = set("""a an the and or of to in on for with is are be by it this that as at from how what which
when where who why can do does i me my we you your not no yes if then than so use using into about there
el la los las un una unos unas y o de del al en con por para que como cual cuando donde es son ser se su sus
lo le les mi me tu te no si ya hay esta este esto estos estas puedo quiero hacer""".split())


def _plain(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def tokens(text: str) -> list[str]:
    found = []
    for word in re.findall(r"[a-z0-9_+\-]+", _plain(text)):
        word = word.strip("-+")
        if len(word) < 2 or word in STOPWORDS:
            continue
        found.append(word[:7] if len(word) > 7 else word.rstrip("s") if len(word) > 4 else word)
    return found


class Knowledge:
    def __init__(self):
        self._docs = None
        self._vectors: dict[str, list[float]] = {}
        self._lock = threading.Lock()
        self._embeddings_ok = True

    # ---- corpus -------------------------------------------------------------
    def documents(self) -> list[dict]:
        if self._docs is None:
            docs = [{"id": i, "scope": s, "title": t, "text": x} for i, s, t, x in kb.documents()]
            for doc in docs:
                doc["tokens"] = tokens(doc["title"] + " " + doc["text"])
                doc["hash"] = hashlib.sha1((doc["title"] + doc["text"]).encode("utf-8")).hexdigest()
            self._docs = docs
            self._prepare_bm25()
        return self._docs

    def _prepare_bm25(self):
        docs = self._docs
        self._n = len(docs)
        self._mean = sum(len(d["tokens"]) for d in docs) / max(1, self._n)
        frequency = Counter()
        for doc in docs:
            doc["tf"] = Counter(doc["tokens"])
            frequency.update(set(doc["tokens"]))
        self._idf = {t: math.log(1 + (self._n - n + 0.5) / (n + 0.5)) for t, n in frequency.items()}

    def _bm25(self, query: str, candidates: list[dict]) -> list[float]:
        words = tokens(query)
        k1, b = 1.4, 0.75
        scores = []
        for doc in candidates:
            score = 0.0
            length = len(doc["tokens"]) or 1
            for word in words:
                f = doc["tf"].get(word)
                if f:
                    score += self._idf.get(word, 0) * f * (k1 + 1) / (f + k1 * (1 - b + b * length / self._mean))
            scores.append(score)
        return scores

    # ---- embeddings ------------------------------------------------------------
    def _cache_file(self):
        return cfg.cache_dir() / "embeddings.json"

    def _load_vectors(self):
        if self._vectors:
            return
        try:
            self._vectors = json.loads(self._cache_file().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self._vectors = {}

    def _ensure_vectors(self, docs: list[dict]):
        from .client import embeddings
        self._load_vectors()
        missing = [d for d in docs if d["hash"] not in self._vectors]
        if not missing:
            return
        for start in range(0, len(missing), 64):
            batch = missing[start:start + 64]
            vectors = embeddings([d["title"] + "\n" + d["text"][:6000] for d in batch])
            for doc, vector in zip(batch, vectors):
                self._vectors[doc["hash"]] = [round(x, 5) for x in vector]
        try:
            alive = {d["hash"] for d in self._docs}
            self._cache_file().write_text(json.dumps({h: v for h, v in self._vectors.items() if h in alive}),
                                          encoding="utf-8")
        except OSError:
            pass

    def _semantic(self, query: str, candidates: list[dict]) -> list[float]:
        from .client import embeddings
        self._ensure_vectors(candidates)
        q = embeddings([query])[0]
        norm_q = math.sqrt(sum(x * x for x in q)) or 1
        scores = []
        for doc in candidates:
            v = self._vectors.get(doc["hash"])
            if not v:
                scores.append(0.0)
                continue
            norm_v = math.sqrt(sum(x * x for x in v)) or 1
            scores.append(sum(a * b for a, b in zip(q, v)) / (norm_q * norm_v))
        return scores

    def warm_up(self):
        """Compute the document vectors once (first time the chat opens)."""
        with self._lock:
            docs = self.documents()
            if self._embeddings_ok:
                try:
                    self._ensure_vectors(docs)
                except Exception:
                    self._embeddings_ok = False

    # ---- search --------------------------------------------------------------------
    def search(self, query: str, screen_scopes: set[str], static_ids: set[str],
               k: int = cfg.RAG_CHUNKS, budget: int = cfg.RAG_BUDGET) -> list[tuple[str, str]]:
        """Pieces relevant to ``query`` that are not already in the screen's fixed context."""
        with self._lock:
            docs = self.documents()
            candidates = [d for d in docs if d["id"] not in static_ids]
            if not candidates or not query.strip():
                return []
            bm = self._bm25(query, candidates)
            rankings = [sorted(range(len(candidates)), key=lambda i: -bm[i])]
            relevant = {i for i in range(len(candidates)) if bm[i] > 0}
            if self._embeddings_ok:
                try:
                    semantic = self._semantic(query, candidates)
                    rankings.append(sorted(range(len(candidates)), key=lambda i: -semantic[i]))
                    relevant |= {i for i in range(len(candidates)) if semantic[i] >= 0.30}
                except Exception:
                    self._embeddings_ok = False  # offline or no permission: BM25 only
            fused = Counter()
            for ranking in rankings:
                for position, i in enumerate(ranking):
                    # what belongs to the screen weighs more
                    scope = candidates[i]["scope"]
                    weight = 1.5 if scope in screen_scopes and scope != "app" else 1.0
                    fused[i] += weight / (60 + position)
            chosen, used = [], 0
            for i, _ in fused.most_common():
                if i not in relevant:
                    continue
                doc = candidates[i]
                if used + len(doc["text"]) > budget and chosen:
                    continue
                chosen.append(doc)
                used += len(doc["text"])
                if len(chosen) >= k:
                    break
            return [(d["title"], d["text"]) for d in chosen]
