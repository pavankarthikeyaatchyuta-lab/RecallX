import time
from typing import Optional
from backend.app.embeddings.manager import model_manager
from backend.app.models.schemas import SearchRequest, SearchResponse, SearchResult
from backend.app.search.explainer import generate_match_explanation
from backend.app.search.hybrid_ranker import (
    compute_hybrid_rank,
    compute_keyword_score,
    compute_recency_score,
)
from backend.app.search.vector_index import vector_index
from backend.app.storage.database import get_all_memories_for_search, get_memory


class SearchEngine:
    """End-to-end local search engine for RecallX."""

    def search(self, request: SearchRequest) -> SearchResponse:
        start_time = time.perf_counter()
        query = request.query.strip()

        if not query:
            return SearchResponse(query="", total=0, elapsed_ms=0.0, results=[])

        # Step 1: Generate query embedding
        query_vector, _ = model_manager.embed_text(query)

        # Step 2: Retrieve semantic matches from vector index
        vector_results = vector_index.search(query_vector, top_k=100)
        vector_scores = {mid: score for mid, score in vector_results}

        # Step 3: Fetch candidate memories from SQLite
        all_memories = get_all_memories_for_search()
        now = time.time()

        ranked_items: list[SearchResult] = []

        for mem in all_memories:
            # Filter by application if requested
            if request.application and request.application.lower() not in mem.application_name.lower():
                continue

            # Filter by date if requested
            if request.date_from and mem.iso_timestamp[:10] < request.date_from:
                continue
            if request.date_to and mem.iso_timestamp[:10] > request.date_to:
                continue

            sem_score = vector_scores.get(mem.id, 0.0)
            kw_score = compute_keyword_score(query, mem.extracted_text, mem.window_title, mem.application_name)
            rec_score = compute_recency_score(mem.timestamp, now)

            # Combined hybrid score
            final_score = compute_hybrid_rank(sem_score, kw_score, rec_score)

            # Threshold check: keep if there is any reasonable relevance
            if final_score >= 0.15 or kw_score > 0.1 or sem_score > 0.35:
                explanation, snippet = generate_match_explanation(
                    query=query,
                    extracted_text=mem.extracted_text,
                    window_title=mem.window_title,
                    app_name=mem.application_name,
                    semantic_score=sem_score,
                    keyword_score=kw_score,
                )

                ranked_items.append(
                    SearchResult(
                        id=mem.id,
                        screenshot_path=mem.screenshot_path,
                        timestamp=mem.timestamp,
                        iso_timestamp=mem.iso_timestamp,
                        extracted_text=mem.extracted_text,
                        snippet=snippet,
                        application_name=mem.application_name,
                        window_title=mem.window_title,
                        score=final_score,
                        semantic_score=sem_score,
                        keyword_score=kw_score,
                        recency_score=rec_score,
                        match_explanation=explanation,
                        is_demo=mem.is_demo,
                    )
                )

        # Sort by final score descending
        ranked_items.sort(key=lambda x: x.score, reverse=True)
        top_results = ranked_items[: request.limit]

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return SearchResponse(
            query=query,
            total=len(ranked_items),
            elapsed_ms=elapsed_ms,
            results=top_results,
        )


search_engine = SearchEngine()
