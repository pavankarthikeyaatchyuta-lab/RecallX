import sys
import time
from pathlib import Path
import requests
import uvicorn
from threading import Thread

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.main import app


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    server_running = False
    try:
        r = requests.get("http://127.0.0.1:8000/api/health", timeout=1.0)
        if r.status_code == 200:
            server_running = True
    except Exception:
        server_running = False

    if not server_running:
        t = Thread(target=run_server, daemon=True)
        t.start()
        time.sleep(2.5)

    print("=" * 60)
    print("Testing RecallX Server Endpoints")
    print("=" * 60)

    # Health
    h = requests.get("http://127.0.0.1:8000/api/health").json()
    print("[1] /api/health ->", h)

    # Status
    s = requests.get("http://127.0.0.1:8000/api/status").json()
    print(f"[2] /api/status -> Capturing: {s['is_capturing']}, Total: {s['total_memories']}, Cloud Requests: {s['cloud_requests']}")

    # Hardware
    hw = requests.get("http://127.0.0.1:8000/api/hardware").json()
    print(f"[3] /api/hardware -> Processor: {hw['processor']}")
    print(f"    Status: {hw['acceleration_status']}")

    # Memories
    m = requests.get("http://127.0.0.1:8000/api/memories?limit=3").json()
    print(f"[4] /api/memories -> Total in DB: {m['total']}, Apps: {m['unique_apps']}")
    for item in m["memories"][:2]:
        print(f"    - [{item['application_name']}] {item['window_title']}")

    # Search
    search_payload = {"query": "internship September deadline", "limit": 2}
    sr = requests.post("http://127.0.0.1:8000/api/search", json=search_payload).json()
    print(f"[5] /api/search -> Returned {len(sr['results'])} matches in {sr['elapsed_ms']} ms")
    if sr["results"]:
        top = sr["results"][0]
        print(f"    Top Match: [{top['application_name']}] {top['window_title']} ({round(top['score']*100, 1)}%)")
        print(f"    Explanation: {top['match_explanation']}")

    # Frontend Static Serving
    frontend_res = requests.get("http://127.0.0.1:8000/")
    print(f"[6] / (Frontend SPA) -> Status: {frontend_res.status_code}, Bytes: {len(frontend_res.text)}")
    assert "<div id=\"root\">" in frontend_res.text

    print("\n[SUCCESS] All server endpoints, vector search, and frontend serving verified!")


if __name__ == "__main__":
    main()
