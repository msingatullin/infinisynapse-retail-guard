# Retail Stockout & Reorder Guard (InfiniSynapse AI Agent)

**Submission for InfiniSynapse Vibe Coding Hackathon 2026**
*Track: Retail & Replenishment / SMB Operations*
*Developer: Mikhail (@msingatullin)*

---

## 1. Project Overview & Problem Statement
Stockouts cost global retailers over $1.2 trillion annually, while excess inventory ties up working capital. Small and medium retail operators (SMBs) struggle with:
1. **Dynamic Depletion Blindness:** Products with sudden velocity spikes run out before standard weekly replenishment cycles.
2. **Supplier Lead Time Mismatches:** Ordering too late leads to empty shelves; ordering too early strains warehouse space.
3. **Manual PO Formulation:** Store managers spend hours compiling disparate spreadsheets into purchase orders.

**Retail Stockout & Reorder Guard** solves this with an autonomous, declarative InfiniSynapse AI Agent that transforms raw stock and sales velocity tables into prioritized risk mitigation plans and instant, optimized Purchase Order (PO) dispatch batches.

---

## 2. Key Architecture & Features

```
[ Raw Inventory CSV / POS Stream ]
               │
               ▼
   [ InfiniSynapse Agent Engine ]
   ├── Safety Stock Calculation (95% Service Level)
   ├── Dynamic Reorder Point (ROP) Modelling
   └── MOQ-Constrained Economic Order Quantities
               │
               ▼
[ InfiniSynapse Reasoning Directive ]
   └── High-urgency executive PO summary
               │
               ▼
   [ Interactive Web Dashboard ]
   ├── Prioritized Risk Tiers (Critical, High, Reorder Window, Healthy)
   ├── 1-Click PO Dispatch CSV Export
   └── Multi-Supplier Consolidator
```

* **Statistical Runout Prediction:** Dynamically calculates days-to-stockout against supplier lead-time margins.
* **InfiniSynapse Decision Synthesis:** Automatically formulates executive directives for store operators.
* **Supplier Consolidator:** Batches purchase orders according to Minimum Order Quantities (MOQ) and unit economics.

---

## 3. Quick Start & Local Execution

```bash
# 1. Clone & Navigate
cd infinisynapse-vibe-coding

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Set your InfiniSynapse API Key
export INFINISYNAPSE_API_KEY="your-key-here"

# 4. Launch Application
python main.py
```
Open `http://localhost:5000` in your browser. Click **"Load Retail Inventory"** or upload your custom retail CSV.

---

## 4. Evaluation Rubric Compliance
- **Scenario Value (40%):** Direct application for retail store operators to prevent stockouts and preserve revenue.
- **Technical Completeness (35%):** Full-stack solution (Flask + JavaScript + Pandas) with end-to-end data ingestion, algorithmic scoring, and CSV export.
- **Innovation (25%):** Bridges deterministic inventory optimization with InfiniSynapse LLM reasoning.

---

## 5. Submission Manifest
- **Source Code:** Open source under Apache 2.0.
- **Sample Dataset:** `data/sample_inventory.csv` (40 real-world SKU profiles across 8 retail categories).
