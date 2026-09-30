import time
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image, ImageDraw

from backend.app.core.config import DEMO_DIR, SCREENSHOTS_DIR
from backend.app.services.memory_service import memory_service

# 16 realistic demo scenarios covering all required categories
DEMO_SCENARIOS = [
    {
        "id": "demo_internship_01",
        "app": "Google Chrome",
        "title": "Qualcomm Careers — AI Software Engineer Internship Application",
        "text": "Qualcomm Technologies, Inc. Summer Internship Program 2027.\nRole: Machine Learning / Snapdragon NPU Optimization Intern.\nApplications close on September 30.\nLocation: San Diego, CA or Bangalore, India.\nRequirements: Experience with ONNX Runtime, QNN SDK, and C++ / Python deep learning deployment.",
        "header_color": (37, 99, 235),
        "days_ago": 1,
    },
    {
        "id": "demo_github_02",
        "app": "Visual Studio Code",
        "title": "github.com/qualcomm/ai-hub-models — Nomic Embed Text QNN Export",
        "text": "Qualcomm AI Hub Models Repository.\nExporting Nomic Embed Text for Snapdragon X Elite Hexagon NPU.\nCommand: qai-hub compile --device 'Snapdragon X Elite CRD' --target-runtime qnn_lib_direct.\nGenerated artifacts: nomic_embed_text_qnn.onnx and libQnnHtp.so.",
        "header_color": (30, 41, 59),
        "days_ago": 1,
    },
    {
        "id": "demo_apidoc_03",
        "app": "Brave Browser",
        "title": "Qualcomm AI Hub Documentation — ONNX Runtime QNN Execution Provider",
        "text": "Qualcomm AI Hub Docs: Integrating QNNExecutionProvider with Windows 11.\nSession Options:\noptions.add_provider_option('QNNExecutionProvider', {'backend_path': 'QnnHtp.dll', 'profiling_level': 'basic'})\nEnables sub-millisecond on-device semantic embedding inference on Hexagon NPU.",
        "header_color": (234, 88, 12),
        "days_ago": 2,
    },
    {
        "id": "demo_hackathon_04",
        "app": "Google Chrome",
        "title": "Qualcomm Snapdragon AI Lab Build & Present Challenge 2026",
        "text": "Challenge Overview: Build innovative on-device AI applications leveraging Snapdragon NPU and Qualcomm AI Hub.\nJudging Criteria: Real on-device acceleration, privacy architecture, UI responsiveness, and practical utility.\nRecallX: Privacy-first visual memory for Windows.",
        "header_color": (225, 29, 72),
        "days_ago": 2,
    },
    {
        "id": "demo_pdf_05",
        "app": "Adobe Acrobat",
        "title": "Confidential_Product_Specification_RecallX_v2.pdf",
        "text": "RecallX Architecture Specification.\nSection 4.2: Vector Storage & Zero-Cloud Guarantee.\nAll screen screenshots are stored in local AES encrypted vaults.\nEmbedding vectors computed on local NPU with 384 dimensions. No external telemetry or cloud vector DB allowed.",
        "header_color": (220, 38, 38),
        "days_ago": 3,
    },
    {
        "id": "demo_email_06",
        "app": "Microsoft Outlook",
        "title": "Inbox — Team Sync: Final Prototype Review and Demo Day Schedule",
        "text": "From: Sarah Jenkins (Lead Organizer)\nSubject: Demo Day Schedule for Snapdragon AI Challenge\nHi team, please ensure your live offline demonstration is prepared.\nJudging starts tomorrow at 10:00 AM EST.\nWe will test disconnected mode and check cloud request counters.",
        "header_color": (2, 132, 199),
        "days_ago": 3,
    },
    {
        "id": "demo_meeting_07",
        "app": "Microsoft Teams",
        "title": "Meeting: Qualcomm Developer Ecosystem Weekly Call",
        "text": "Participants: Dr. Robert Chen (Qualcomm AI), Priya Sharma, Alex Vance.\nKey Discussion: Windows on ARM adoption, NPU power efficiency metrics (TOPS/Watt).\nAction Item: Benchmark QNN HTP vs CPU latency on batch size 1 and batch size 32.",
        "header_color": (79, 70, 229),
        "days_ago": 4,
    },
    {
        "id": "demo_code_08",
        "app": "Visual Studio Code",
        "title": "main.py — FastAPI High-Performance Search Endpoint",
        "text": "from fastapi import FastAPI, Depends\n@app.post('/api/search')\nasync def execute_search(req: SearchRequest):\n    # Local hybrid ranking: semantic_score + keyword_score + recency_score\n    res = search_engine.search(req)\n    return res",
        "header_color": (30, 41, 59),
        "days_ago": 4,
    },
    {
        "id": "demo_presentation_09",
        "app": "Microsoft PowerPoint",
        "title": "RecallX_Qualcomm_Pitch_Deck_Final.pptx — Slide 4: Privacy Architecture",
        "text": "RecallX: 'Your screen history stays on your device.'\nCloud requests: 0.\nLocal OCR via Windows Native WinRT.\nLocal Embeddings via Snapdragon NPU.\nLocal Vector Search via optimized Cosine Index.",
        "header_color": (194, 65, 12),
        "days_ago": 5,
    },
    {
        "id": "demo_deadline_10",
        "app": "Notion",
        "title": "Project Roadmap & Critical Deadlines — Q3 2026",
        "text": "September Deadlines Checklist:\n- Sept 25: Feature freeze and offline validation\n- Sept 28: Seed synthetic demo memories\n- September 30: Final submission deadline for Qualcomm Challenge at 11:59 PM.\n- Oct 5: Winner announcement.",
        "header_color": (15, 23, 42),
        "days_ago": 5,
    },
    {
        "id": "demo_finance_11",
        "app": "Microsoft Excel",
        "title": "Budget_Expense_Report_2026.xlsx — Sheet1: Lab Hardware",
        "text": "Hardware Procurement Table:\nItem: Qualcomm Snapdragon X Elite Development Kit CRD (32GB RAM, 45 TOPS NPU)\nInvoice Amount: ₹50,000 (INR)\nStatus: Approved & Reimbursed\nVendor: Qualcomm Direct Developer Store",
        "header_color": (22, 101, 52),
        "days_ago": 6,
    },
    {
        "id": "demo_research_12",
        "app": "Google Chrome",
        "title": "arXiv:2404.01234 — On-Device Small Language Models and Embedding Systems",
        "text": "Abstract: We evaluate the energy efficiency and throughput of dense text embeddings on mobile and desktop NPUs.\nEmpirical results demonstrate a 4.2x latency reduction and 6.8x power efficiency advantage when running Nomic Embed Text on Qualcomm Hexagon NPU over standard host CPU.",
        "header_color": (59, 130, 246),
        "days_ago": 6,
    },
    {
        "id": "demo_terminal_13",
        "app": "Windows Terminal",
        "title": "PowerShell — python scripts/benchmark.py",
        "text": "================================\nRecallX Benchmark Report\n================================\nHardware: Windows 11 on Snapdragon\nExecution Provider: QNNExecutionProvider (HTP)\nAverage Embedding Latency: 4.8 ms\nP95 Embedding Latency: 6.2 ms\nAverage Search Latency: 1.1 ms\nStatus: 100% Local Execution\n================================",
        "header_color": (15, 23, 42),
        "days_ago": 7,
    },
    {
        "id": "demo_slack_14",
        "app": "Slack",
        "title": "#general — AI Lab Hackathon Team Channel",
        "text": "David: 'Did anyone test whether the search responds to natural language queries like where did I see the September deadline?'\nPriya: 'Yes! The hybrid ranker matches both the semantic meaning and exact keyword with 96% score.'",
        "header_color": (74, 21, 75),
        "days_ago": 7,
    },
    {
        "id": "demo_notes_15",
        "app": "Obsidian",
        "title": "Notes/On-Device-AI-Principles.md",
        "text": "# Core Principles of Privacy-First Computing\n1. Zero Cloud Dependency: Core user loops must work disconnected.\n2. Transparent Scoring: Match explanations show real keyword overlap and semantic confidence.\n3. User Sovereignty: Instant one-click memory deletion and exclusion lists.",
        "header_color": (88, 28, 135),
        "days_ago": 8,
    },
    {
        "id": "demo_settings_16",
        "app": "RecallX Settings",
        "title": "RecallX — Privacy & Local Hardware Dashboard",
        "text": "Privacy Guard Status: 100% Local.\nNetwork Activity: 0 Outbound Packets.\nActive Provider: Qualcomm QNN (NPU) / CPU Fallback Ready.\nData Directory: data/screenshots\nExclusion Rules: Active for Banking and Password Managers.",
        "header_color": (37, 99, 235),
        "days_ago": 8,
    },
]


def render_demo_screenshot(scenario: dict) -> Path:
    """Generates an aesthetic, high-resolution synthetic screenshot card."""
    width, height = 1280, 720
    img = Image.new("RGB", (width, height), color=(15, 17, 26))
    draw = ImageDraw.Draw(img)

    # Top application title bar
    bar_height = 48
    draw.rectangle([0, 0, width, bar_height], fill=scenario["header_color"])
    # Mac/Win window buttons
    draw.ellipse([16, 18, 28, 30], fill=(239, 68, 68))
    draw.ellipse([36, 18, 48, 30], fill=(245, 158, 11))
    draw.ellipse([56, 18, 68, 30], fill=(16, 185, 129))

    # App & window title
    draw.text((80, 16), f"{scenario['app']} — {scenario['title']}", fill=(255, 255, 255))

    # DEMO DATA watermark badge
    draw.rectangle([width - 150, 10, width - 20, 38], fill=(225, 29, 72))
    draw.text((width - 135, 16), "DEMO DATA", fill=(255, 255, 255))

    # Main content panel
    draw.rectangle([40, 72, width - 40, height - 40], fill=(24, 27, 38), outline=(45, 52, 72), width=1)

    # Sub-header
    draw.rectangle([40, 72, width - 40, 120], fill=(30, 34, 48))
    draw.text((64, 88), scenario["title"], fill=(96, 165, 250))

    # Content body
    y = 150
    for line in scenario["text"].splitlines():
        draw.text((64, y), line, fill=(226, 232, 240))
        y += 32

    # Footer banner
    draw.rectangle([40, height - 90, width - 40, height - 40], fill=(18, 20, 28))
    draw.text(
        (64, height - 72),
        "RecallX Demo Memory • Privacy-Preserved Local Capture • Snapdragon AI Optimization",
        fill=(100, 116, 139),
    )

    out_file = SCREENSHOTS_DIR / f"{scenario['id']}.png"
    img.save(out_file, "PNG", optimize=True)
    return out_file


def seed_demo_memories() -> int:
    """Populates local database and vector index with 16 realistic demo memories."""
    now = datetime.now()
    count = 0

    for scenario in DEMO_SCENARIOS:
        img_path = render_demo_screenshot(scenario)
        days = scenario.get("days_ago", 1)
        simulated_ts = (now - timedelta(days=days, hours=days * 2, minutes=days * 15)).timestamp()

        relative_path = f"/data/screenshots/{img_path.name}"
        memory_service.create_memory(
            screenshot_path=relative_path,
            extracted_text=scenario["text"],
            application_name=scenario["app"],
            window_title=scenario["title"],
            ocr_latency_ms=12.5,
            is_demo=True,
            custom_id=scenario["id"],
            custom_timestamp=simulated_ts,
        )
        count += 1

    return count
