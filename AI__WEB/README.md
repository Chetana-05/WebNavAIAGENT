# Web Navigator AI Agent — Multi-Store Product & Price Comparison
### TCS Hackathon Submission · Team AgentXplorer

A high-performance web automation and product comparison agent that accepts natural-language product queries and simultaneously scrapes, parses, and compares listings across **4 major Indian e-commerce platforms**:
- **Amazon India** (`amazon.in`)
- **Flipkart** (`flipkart.com`)
- **Croma** (`croma.com`)
- **Ajio** (`ajio.com`)

The agent features a deterministic **Hardware Specification Conflict Prevention Engine** that strictly matches identical product models (eliminating false pairings like Ryzen 5 vs. Ryzen 3), computes instant cross-store rupee savings, and delivers a unified 4-in-1 comparison dashboard designed to save online shoppers 15+ minutes of manual tab browsing.

---

## 👥 Team Information

- **Team Name:** AgentXplorer
- **Team Member:** K. Chetana
- **Hackathon:** TCS Hackathon 2026
- **Task Objective:** *"If I search for any product, it must display results from multiple websites (Amazon, Flipkart, Croma, Ajio) with a site-by-site comparison to save users time."*
- **Originality Status:** ✅ Verified 100% Original Implementation ([Read Full Audit Report](ORIGINALITY_REPORT.md))

---

## 🌟 Problems Solved & Technical Innovations

| Consumer Challenge | Web Navigator AI Agent Solution | Technical Innovation |
| :--- | :--- | :--- |
| **Manual Multi-Tab Searching** (takes 15+ mins to search across 4 tabs) | **Parallel Multi-Store Async Engine** queries Amazon, Flipkart, Croma, and Ajio simultaneously in **5–8 seconds**. | Python `asyncio.gather()` with Playwright Chromium multi-page context isolation. |
| **Mismatched "Similar" Items** (e.g., comparing an Acer Ryzen 5 with an Acer Ryzen 3) | **Hardware Specification Conflict Matrix** strictly enforces CPU family, model series, and RAM/storage consistency. | Deterministic pre-similarity filter rejecting contradictory hardware tiers before Jaccard calculation. |
| **Hidden MRPs & Fake Discounts** | **Normalized Price & Savings Engine** calculates actual rupee price gaps and highlights the lowest-priced platform. | Cross-platform regex parsing for current prices, struck-out MRPs, and net savings. |
| **Dispersed Ratings & Reviews** | **Dual-Factor Objective Value Metric** computes an unbiased 1.0–10.0 score. | Balanced algorithm combining verified star rating with economic price-to-utility ratio. |
| **Fragmented Interfaces** | **Interactive 4-in-1 Comparison UI** providing instant toggles across store catalog views. | Tabbed dashboard with 1) Same Product Match, 2) 4-Store Side-by-Side View, 3) Similar Matches, 4) Unified Deals Table. |

---

## 🏗️ System Architecture

```
[ Natural Language Goal: "search for laptops under 50k" / "iPhone 15" / "running shoes" ]
                                      │
                            [ Agent Query Parser ]
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼ (Concurrent execution via asyncio.gather across 4 sites)▼
   [ Amazon.in ]             [ Flipkart.com ]          [ Croma.com ]            [ Ajio.com ]
   • Title, Price            • Title, Price            • Title, Price           • Title, Price
   • MRP, Discount           • MRP, Discount           • MRP, Discount          • MRP, Discount
   • Ratings, Reviews        • Ratings, Reviews        • NeuPass Rewards        • Reliance Points
   • Image, Store URL        • Image, Store URL        • Image, Store URL       • Image, Store URL
         └────────────────────────────┬────────────────────────────┘
                                      ▼
             [ Dual-Stage Hardware Spec Conflict Checker ]
             • CPU Tier Check (Ryzen 5 != Ryzen 3 -> HARD REJECT)
             • Model Series Check (Aspire One != Aspire 15 -> HARD REJECT)
             • Memory & Storage Check (8GB != 16GB -> HARD REJECT)
                                      ▼
                 [ Cross-Platform Deal & Savings Engine ]
                 • Identifies Lowest Price Store Across All 4 Sites
                 • Calculates Exact Rupee Savings (e.g., "Save ₹2,200 on Flipkart")
                 • Computes Multi-Store Average Price Spreads
                                      ▼
                 [ Executive Decision Synthesis / AI Verdict ]
                                      │
                     ┌────────────────┴────────────────┐
                     ▼                                 ▼
           [ Modern Web Dashboard ]           [ Formatted CLI Report ]
           (http://127.0.0.1:8000)             (Terminal Structured)
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher
- Playwright Chromium (`python -m playwright install chromium`)

### 2. Start the Interactive Web Application
From the project directory:

```powershell
# Navigate to the project directory
cd C:\Users\chait\Downloads\WebNavAIAGENT-main\WebNavAIAGENT-main\WebNavAIAGENT\AI__WEB

# Start the web server
.\.venv\Scripts\python.exe -m web_agent.web
```

Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in any browser.

#### Available Modes in the Dashboard:
1. **🎯 Compare Same Product:** Shows only 100% verified identical models matched across stores, displaying hardware verification pills (`[Acer] · [Core i3] · [8GB RAM] · [512GB SSD]`), side-by-side product cards, and instant store savings.
2. **⚡ Side-by-Side All Products:** Responsive 4-column catalog layout showcasing Amazon, Flipkart, Croma, and Ajio products side-by-side.
3. **🥊 Similar Matches:** Broader brand-level comparisons that strictly respect CPU and spec comparability.
4. **📊 Unified Deals Table:** Sortable, filterable single-table view across all 4 platforms with store badges and direct purchase buttons.
5. **Display Items Filter:** Select between Top 5, 8, 12, 16, 20, or All items per store with dynamic metric recomputation.

---

### 3. Run via Command Line Interface (CLI)

```powershell
# Run product comparison from terminal
.\.venv\Scripts\python.exe -m web_agent.cli --goal "laptops under 50000"

# Search for smartphones
.\.venv\Scripts\python.exe -m web_agent.cli --goal "iPhone 15"

# Export output as machine-readable JSON
.\.venv\Scripts\python.exe -m web_agent.cli --goal "running shoes under 2000" --json
```

---

## 📂 Project Organization

```
AI__WEB/
├── web_agent/
│   ├── __init__.py          # Package initialization
│   ├── agent.py             # 4-Store parallel scraping coordinator & async pipeline
│   ├── browser.py           # Playwright Chromium lifecycle manager with multi-tab isolation
│   ├── cli.py               # Formatted CLI with multi-store comparison breakdown
│   ├── comparer.py          # Spec conflict matrix, same-product matcher & value score engine
│   ├── extractors.py        # Extractors for Amazon, Flipkart, Croma, and Ajio with resilient fallback
│   ├── ollama_client.py     # Local LLM integration with automatic algorithmic fallback
│   ├── planner.py           # Natural-language query normalization
│   └── web.py               # Modern responsive web dashboard (http://127.0.0.1:8000)
├── ORIGINALITY_REPORT.md    # TCS Hackathon academic integrity & plagiarism audit report
├── requirements.txt         # Open-source dependencies
└── README.md                # Comprehensive project documentation
```

---

## 🛡️ Academic Integrity & Originality Verification

This project was built from scratch for the TCS Hackathon 2026. A detailed **[Originality & Plagiarism Audit Report](ORIGINALITY_REPORT.md)** is included, confirming:
- **0% Plagiarism** from external code repositories.
- Custom algorithms developed by the team (Hardware Spec Conflict Matrix, Jaccard Spec-Preserving Matcher).
- Full disclosure of permissive open-source packages (Playwright, Typer, Python 3.12 stdlib).