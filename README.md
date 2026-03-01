# 💸 Financial Impulse Behaviour Analyser

> **Behavioural Analytics Hackathon — Problem Statement 2**  
> Detect impulsive spending patterns in young adults using real bank statement data.

---

## Overview

`bank_analyser` is a production-ready Python module that accepts a bank statement upload, dynamically detects its column structure, and returns a fully structured JSON report containing:

- **Impulse Risk Score (0–100)** per month — ML ensemble, no hardcoded weights
- **Adaptive risk tiers** (Low / Medium / High) derived from the user's own distribution
- **7 behavioural archetypes** with personalised nudges
- **7 analytics charts** as base64 PNGs, ready to embed in any frontend
- **Schema detection report** — exactly which columns were found and how

---

## Project Structure

```
bank_analyser/
├── __init__.py          # Public API exports
└── analyser.py          # Core module — all logic lives here

impulsive_financial_behaviour_v3.ipynb   # Reference notebook + hackathon submission
model_explanation.docx                   # Model Explanation Document (5 pages)
README.md                                # This file
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install pandas numpy scipy scikit-learn matplotlib seaborn openpyxl
```

### 2. Use in a notebook

```python
from bank_analyser import BankStatementAnalyser

analyser = BankStatementAnalyser(currency_symbol='₹')

with open('my_statement.csv', 'rb') as f:
    result = analyser.analyse(file_bytes=f.read(), filename='my_statement.csv')

# Print monthly risk scores
for month in result['monthly_scores']:
    print(month['month'], month['impulse_risk_score'], month['risk_tier'], month['behaviour_profile'])
```

### 3. Plug into Flask

```python
from flask import Flask, request, jsonify
from bank_analyser import BankStatementAnalyser

app = Flask(__name__)
analyser = BankStatementAnalyser()  # initialise once at startup

@app.route('/analyse', methods=['POST'])
def analyse():
    if 'statement' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    f = request.files['statement']
    try:
        result = analyser.analyse(file_bytes=f.read(), filename=f.filename)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': str(e)}), 422
```

### 4. Plug into FastAPI

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from bank_analyser import BankStatementAnalyser

app = FastAPI()
analyser = BankStatementAnalyser()

@app.post("/analyse")
async def analyse(statement: UploadFile = File(...)):
    contents = await statement.read()
    try:
        return analyser.analyse(file_bytes=contents, filename=statement.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
```

### 5. Embed a chart in HTML

```html
<img src="data:image/png;base64,{{ result.charts.risk_timeline }}" />
```

---

## Supported Bank Formats

The module auto-detects column structure — no configuration needed for new banks.

| Bank / Format | Column Style | Handled? |
|---|---|---|
| IndusInd Bank | `Withdrawal Amt.` / `Deposit Amt.` / `Closing Balance` (TSV + `***` separator row) | ✅ |
| HDFC Bank | `Debit` / `Credit` / `Balance` (CSV) | ✅ |
| ICICI Bank | `Withdrawal Amount (INR)` / `Deposit Amount (INR)` | ✅ |
| SBI | `Debit` / `Credit` / `Balance` | ✅ |
| Axis / Kotak | `Amount` + `Dr/Cr` flag column | ✅ |
| Generic exports | Signed `Amount` column (negative = debit) | ✅ |
| XLSX exports | Any of the above in Excel format | ✅ |

To add a new bank, add a regex pattern to `COLUMN_SEMANTIC_MAP` in `analyser.py`. No other changes needed.

---

## How the Risk Score Works

The pipeline replaces manual/hardcoded weights with a **3-method ML ensemble**, each capturing a different dimension of behavioural anomaly:

| Method | What it detects | Why it's better than manual weights |
|---|---|---|
| **Z-Score Anomaly** | How many std deviations each month deviates from *your own* baseline (upward only) | Personalised — adapts to your income level and lifestyle |
| **Isolation Forest** | Structurally unusual months across all features simultaneously | Catches multi-feature outliers no single metric sees |
| **PCA Reconstruction Error** | Months that don't fit your learnt normal spending pattern | Captures correlated feature shifts |

The three normalised scores are averaged with equal weight → **Impulse Risk Score (0–100)**.

**Adaptive thresholds** are derived from the user's own score distribution:
- **Low** = below 33rd percentile of your scores
- **Medium** = 33rd–67th percentile
- **High** = above 67th percentile

This means the tiers always reflect *your* personal context — someone with consistently high food spending will not be permanently stuck in High risk.

---

## Feature Engineering

10 monthly behavioural features are computed from raw transactions:

| Feature | Behavioural signal |
|---|---|
| `cv_amount` | Spending variability — binge-pause cycles |
| `eom_spend_ratio` | End-of-month spending surge |
| `eom_txn_share` | Frequency of late-month transactions |
| `imp_cat_share` | Share of transactions in impulsive categories |
| `imp_cat_spend_share` | Share of spend value in impulsive categories |
| `large_txn_share` | Proportion of unusually large single transactions |
| `spike_ratio` | Max transaction relative to monthly average |
| `weekend_spend_share` | Weekend leisure spending |
| `spend_to_income_ratio` | Overspending signal — values > 1 are critical |
| `atm_cash_share` | Cash withdrawal frequency |

**Impulsive categories:** Food & Dining, Entertainment, Shopping / Fashion, Alcohol / Bars, ATM / Cash.

---

## API Output Structure

```json
{
  "schema_report": {
    "raw_columns": ["Date", "Narration", ...],
    "detected_mapping": {"date": "Date", "withdrawal": "Withdrawal Amt.", ...},
    "amount_format": "dual_column",
    "total_rows_loaded": 412,
    "warnings": []
  },
  "summary": {
    "date_range": "2023-04-01 → 2025-03-31",
    "total_months": 24,
    "total_transactions": 412,
    "total_withdrawn": 847320.50,
    "total_deposited": 1200000.00,
    "adaptive_thresholds": {"low_below": 28.4, "medium_range": "28.4 – 51.7", "high_above": 51.7}
  },
  "risk_distribution": {"Low": 8, "Medium": 8, "High": 8},
  "monthly_scores": [
    {
      "month": "2023-04",
      "impulse_risk_score": 38.0,
      "score_zscore": 43.5,
      "score_isoforest": 28.0,
      "score_pca": 42.6,
      "risk_tier": "Medium",
      "behaviour_profile": "⚠️ Situational Spender",
      "nudges": ["📣 You tend to overspend on specific days...", "🧘 Pause before large transactions..."],
      "key_features": {
        "spend_to_income": 0.612,
        "eom_spend_ratio": 1.23,
        "impulsive_cat_share": 0.41,
        "cv_amount": 0.87,
        "spike_ratio": 3.2
      }
    }
  ],
  "category_spend": {"EMI / Loan": 98340.0, "Food & Dining": 42100.0, ...},
  "ml_classification": {"status": "completed", "mode": "cross_val", "scores": {...}, "feature_importances": {...}},
  "charts": {
    "risk_timeline": "<base64 PNG>",
    "method_breakdown": "<base64 PNG>",
    "category_spend": "<base64 PNG>",
    "monthly_trend": "<base64 PNG>",
    "balance_trend": "<base64 PNG>",
    "eom_comparison": "<base64 PNG>",
    "behaviour_profiles": "<base64 PNG>"
  }
}
```

---

## Behavioural Profiles & Nudges

| Profile | Trigger Condition | Key Nudges |
|---|---|---|
| 🔥 Overspender | `spend_to_income > 0.9` | Hard spending cap; auto-save 10% of salary |
| 📅 Month-End Binger | `eom_spend_ratio > 1.5` | Lock 25% balance on the 20th; EOM streak challenge |
| 🎮 Lifestyle Overindulger | `imp_cat_spend_share > 0.5` | Per-category caps; mirror-invest rule |
| ⚡ High Impulse Month | All signals elevated | 24-hour cooling-off rule; daily review |
| 🔄 Binge-Pause Cycler | `cv_amount > 1.5` | Weekly envelope budget; rhythm visualisation |
| ⚠️ Situational Spender | Medium risk | Context-aware alerts; mindfulness pause |
| ✅ Disciplined Month | All signals low | SIP increment; positive reinforcement |

---

## Extending the Module

### Add a new bank format
```python
# In analyser.py → COLUMN_SEMANTIC_MAP
'withdrawal': [
    ...existing patterns...,
    r'^debit\s*transactions?$',   # add your bank's column name as a regex
]
```

### Add a new spending category
```python
# In analyser.py → CATEGORY_RULES
'Pet Care': r'PETCO|PETSMART|VET|VETERINARY|PAWSOME',

# Optionally mark it as impulsive
IMPULSIVE_CATEGORIES.add('Pet Care')
```

### Change ensemble weights
```python
# In BankStatementAnalyser._compute_risk_scores()
ensemble = (0.5 * norm01(z_raw) + 0.3 * norm01(iso_raw) + 0.2 * norm01(pca_raw)) * 100
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `pandas` | Data loading and manipulation |
| `numpy` | Numerical computation |
| `scipy` | Z-score computation |
| `scikit-learn` | Isolation Forest, PCA, classifiers, scalers |
| `matplotlib` | Chart generation |
| `seaborn` | Plot styling |
| `openpyxl` | XLSX file reading |

---

## Limitations

- **Minimum data:** 6 months recommended; 12–24 months ideal for reliable ML scoring.
- **Supervised layer:** With ~24 months of data, classification results are directional. Feature importances are more reliable than model accuracy figures.
- **Category detection:** Regex-based — high accuracy for major platforms (Zomato, Amazon, IRCTC etc.); may misclassify obscure or regional merchants.
- **No cross-user benchmarking:** All comparisons are against the user's own baseline. Population-level percentile benchmarking requires a privacy-preserving multi-user dataset.

---

## Submitted for

**Behavioural Analytics Hackathon · Problem Statement 2**  
*Detecting Financial Impulse Behaviour in Young Adults*
