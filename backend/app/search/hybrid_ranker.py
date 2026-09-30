import math
import re
import time
from backend.app.core.config import settings


def compute_keyword_score(query: str, text: str, title: str, app: str) -> float:
    """
    Computes a normalized lexical token-matching score (0.0 to 1.0).
    Rewards presence of query words in title and text.
    """
    tokens = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 1]
    if not tokens:
        return 0.0

    target = f"{title.lower()} {app.lower()} {text.lower()}"
    matched_count = 0
    title_boost = 0.0

    for tok in tokens:
        if tok in target:
            matched_count += 1
        if tok in title.lower() or tok in app.lower():
            title_boost += 0.2

    base_score = matched_count / len(tokens)
    total_score = min(1.0, base_score + (title_boost / max(len(tokens), 1)))
    return round(total_score, 4)


def compute_recency_score(memory_timestamp: float, now: float | None = None) -> float:
    """
    Decays score smoothly based on age.
    Memories created within the last 24h score ~1.0; 7 days old ~0.5; older ~0.2+.
    """
    if now is None:
        now = time.time()
    age_seconds = max(0.0, now - memory_timestamp)
    # Half-life of 7 days (604,800 seconds)
    half_life = 7 * 86400.0
    recency = math.exp(-0.693 * (age_seconds / half_life))
    return round(float(recency), 4)


def compute_hybrid_rank(
    semantic_score: float,
    keyword_score: float,
    recency_score: float,
    semantic_weight: float | None = None,
    keyword_weight: float | None = None,
    recency_weight: float | None = None,
) -> float:
    """
    Combines three signals:
        W_sem * semantic_score + W_kw * keyword_score + W_rec * recency_score
    Default weights:
        Semantic: 0.65
        Keyword:  0.25
        Recency:  0.10
    """
    w_sem = semantic_weight if semantic_weight is not None else settings.semantic_weight
    w_kw = keyword_weight if keyword_weight is not None else settings.keyword_weight
    w_rec = recency_weight if recency_weight is not None else settings.recency_weight

    # Normalize weights sum to 1.0
    w_total = w_sem + w_kw + w_rec
    if w_total > 0:
        w_sem /= w_total
        w_kw /= w_total
        w_rec /= w_total

    final_score = (w_sem * semantic_score) + (w_kw * keyword_score) + (w_rec * recency_score)
    return round(float(final_score), 4)
