import sys
import time
from pathlib import Path

# Ensure root directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.models.schemas import SearchRequest
from backend.app.search.engine import search_engine
from backend.app.services.demo_service import seed_demo_memories
from backend.app.storage.database import count_memories, init_db

EVAL_CASES = [
    {
        "query": "Find the internship application with the September deadline",
        "expected_id": "demo_internship_01",
        "category": "Temporal / Deadline",
    },
    {
        "query": "Where did I see the Qualcomm AI Hub command to compile on Snapdragon CRD?",
        "expected_id": "demo_github_02",
        "category": "Technical / Code",
    },
    {
        "query": "ONNX Runtime QNN Execution Provider QnnHtp documentation",
        "expected_id": "demo_apidoc_03",
        "category": "Documentation / API",
    },
    {
        "query": "Qualcomm Snapdragon AI Lab Build and Present Challenge",
        "expected_id": "demo_hackathon_04",
        "category": "Hackathon / Competition",
    },
    {
        "query": "Confidential product specification zero-cloud local AES vault",
        "expected_id": "demo_pdf_05",
        "category": "Security / Privacy",
    },
    {
        "query": "Sarah Jenkins email about Demo Day judging schedule",
        "expected_id": "demo_email_06",
        "category": "Communication / Email",
    },
    {
        "query": "Dr Robert Chen weekly call discussing NPU power efficiency TOPS per Watt",
        "expected_id": "demo_meeting_07",
        "category": "Meeting / Discussion",
    },
    {
        "query": "FastAPI high-performance search endpoint route code",
        "expected_id": "demo_code_08",
        "category": "Source Code",
    },
    {
        "query": "RecallX pitch deck slide about privacy architecture",
        "expected_id": "demo_presentation_09",
        "category": "Presentation / Pitch",
    },
    {
        "query": "Project roadmap and critical feature freeze deadlines",
        "expected_id": "demo_deadline_10",
        "category": "Planning / Roadmap",
    },
    {
        "query": "Find the hardware expense invoice with the ₹50,000 amount",
        "expected_id": "demo_finance_11",
        "category": "Finance / Numerical",
    },
    {
        "query": "arXiv paper on dense text embeddings on Qualcomm Hexagon NPU",
        "expected_id": "demo_research_12",
        "category": "Research / Paper",
    },
    {
        "query": "Terminal benchmark output showing 4.8 ms embedding latency",
        "expected_id": "demo_terminal_13",
        "category": "Terminal / Logs",
    },
    {
        "query": "Slack discussion asking about natural language deadline queries",
        "expected_id": "demo_slack_14",
        "category": "Chat / Slack",
    },
    {
        "query": "Obsidian notes on zero cloud dependency and user sovereignty",
        "expected_id": "demo_notes_15",
        "category": "Notes / Philosophy",
    },
    {
        "query": "Settings exclusion rules for banking and password managers",
        "expected_id": "demo_settings_16",
        "category": "Settings / Configuration",
    },
]


def run_evaluation():
    sys.stdout.reconfigure(encoding="utf-8")
    init_db()

    # Ensure demo memories are present in database and vector index
    if count_memories() < 16:
        print("[*] Demo dataset incomplete. Seeding 16 synthetic memories...")
        seed_demo_memories()

    print("\n" + "=" * 70)
    print("        RecallX Search Quality & Retrieval Accuracy Evaluation")
    print("=" * 70)
    print("Dataset: 16 Controlled Realistic Visual Memories (Synthetic Demo Set)")
    print("Metric:  Top-1 & Top-3 Retrieval Accuracy via Hybrid Semantic/Keyword Ranker\n")

    top1_hits = 0
    top3_hits = 0
    total = len(EVAL_CASES)

    print(f"{'#':<3} {'Category':<22} {'Top-1':<7} {'Top-3':<7} {'Query':<30}")
    print("-" * 70)

    t_start = time.perf_counter()

    for idx, case in enumerate(EVAL_CASES, 1):
        q = case["query"]
        expected = case["expected_id"]
        cat = case["category"]

        req = SearchRequest(query=q, limit=5)
        response = search_engine.search(req)

        top1_match = False
        top3_match = False

        if response.results:
            top1_id = response.results[0].id
            top1_match = (top1_id == expected)

            top3_ids = [r.id for r in response.results[:3]]
            top3_match = (expected in top3_ids)

        if top1_match:
            top1_hits += 1
        if top3_match:
            top3_hits += 1

        top1_str = "[PASS]" if top1_match else "[FAIL]"
        top3_str = "[PASS]" if top3_match else "[FAIL]"
        short_q = q if len(q) <= 30 else q[:27] + "..."

        print(f"{idx:<3} {cat:<22} {top1_str:<7} {top3_str:<7} {short_q}")

    elapsed = round(time.perf_counter() - t_start, 2)
    top1_acc = round((top1_hits / total) * 100, 1)
    top3_acc = round((top3_hits / total) * 100, 1)

    print("-" * 70)
    print(f"Total Test Queries:        {total}")
    print(f"Top-1 Retrieval Accuracy:  {top1_acc}% ({top1_hits}/{total})")
    print(f"Top-3 Retrieval Accuracy:  {top3_acc}% ({top3_hits}/{total})")
    print(f"Evaluation Completed In:   {elapsed}s")
    print("=" * 70)
    print("NOTE: These accuracy metrics strictly reflect retrieval quality against the")
    print("synthetic evaluation benchmark set and do not represent generalized user claims.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_evaluation()
