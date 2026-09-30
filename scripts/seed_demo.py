import sys
import time
from pathlib import Path

# Ensure root directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.storage.database import init_db
from backend.app.services.demo_service import seed_demo_memories
from backend.app.search.engine import search_engine
from backend.app.models.schemas import SearchRequest


def main():
    print("=" * 60)
    print("RecallX Demo Dataset Generator & Verifier")
    print("=" * 60)

    sys.stdout.reconfigure(encoding="utf-8")
    print("\n[1/3] Initializing local SQLite database and WAL mode...")
    init_db()

    print("[2/3] Generating synthetic screenshot cards and computing local embeddings...")
    t0 = time.perf_counter()
    count = seed_demo_memories()
    elapsed = round(time.perf_counter() - t0, 2)
    print(f"[+] Successfully seeded {count} realistic DEMO memories in {elapsed}s.")

    print("\n[3/3] Testing natural-language semantic queries over demo memories...")
    test_queries = [
        "Find the internship application with the September deadline",
        "Where did I see the Qualcomm AI Hub documentation?",
        "Find the document with the ₹50,000 amount",
        "Show me what I was looking at regarding Snapdragon NPU",
    ]

    for query in test_queries:
        res = search_engine.search(SearchRequest(query=query, limit=2))
        print(f"\nQuery: \"{query}\" (Latency: {res.elapsed_ms} ms)")
        if res.results:
            top = res.results[0]
            print(f"  Top Match: [{top.application_name}] {top.window_title}")
            print(f"  Hybrid Score: {round(top.score * 100, 1)}% (Semantic: {round(top.semantic_score * 100, 1)}%, Keyword: {round(top.keyword_score * 100, 1)}%)")
            print(f"  Evidence: {top.snippet}")
            print(f"  Explanation: {top.match_explanation}")
        else:
            print("  No matches returned.")

    print("\n" + "=" * 60)
    print("Demo dataset ready. Start the frontend to explore.")
    print("=" * 60)


if __name__ == "__main__":
    main()
