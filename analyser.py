"""
bank_analyser/analyser.py
=========================
Production-ready Bank Statement Analyser Module
Plug into any web backend — accepts uploaded file bytes, returns structured JSON results.

Usage (Flask/FastAPI example):
    from bank_analyser.analyser import BankStatementAnalyser

    analyser = BankStatementAnalyser()
    result = analyser.analyse(file_bytes=request.files['statement'].read(),
                              filename='statement.csv')
    return jsonify(result)
"""

import io
import re
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import base64

from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import roc_auc_score

warnings.filterwarnings('ignore')


# ══════════════════════════════════════════════════════════════════════════════
# COLUMN SEMANTIC MAPPER
# Maps any bank's column names → canonical internal names
# Add new bank formats here without touching any other code.
# ══════════════════════════════════════════════════════════════════════════════

# Each entry: list of regex patterns that match a bank's raw column name
COLUMN_SEMANTIC_MAP = {
    # ── date ──────────────────────────────────────────────────────────────────
    'date': [
        r'^date$', r'^txn\s*date$', r'^transaction\s*date$',
        r'^trans\s*date$', r'^posting\s*date$', r'^value\s*date$',
        r'^dt$', r'^tran\s*dt$',
    ],
    # ── narration / description ───────────────────────────────────────────────
    'narration': [
        r'^narration$', r'^description$', r'^particulars$',
        r'^remarks$', r'^transaction\s*details?$', r'^details?$',
        r'^merchant\s*name$', r'^trans\s*description$', r'^memo$',
    ],
    # ── reference number ──────────────────────────────────────────────────────
    'ref_no': [
        r'^chq\.?/?ref\.?\s*no\.?$', r'^reference\s*(no\.?|number)?$',
        r'^cheque\s*(no\.?|number)?$', r'^transaction\s*id$',
        r'^ref\.?\s*no\.?$', r'^utr$', r'^rrn$',
    ],
    # ── debit / withdrawal ────────────────────────────────────────────────────
    'withdrawal': [
        r'^withdrawal\s*amt\.?$', r'^debit\s*amt\.?$', r'^debit$',
        r'^withdrawal$', r'^dr\.?\s*amount$', r'^dr$',
        r'^amount\s*\(?dr\.?\)?$', r'^spent$', r'^paid$',
    ],
    # ── credit / deposit ──────────────────────────────────────────────────────
    'deposit': [
        r'^deposit\s*amt\.?$', r'^credit\s*amt\.?$', r'^credit$',
        r'^deposit$', r'^cr\.?\s*amount$', r'^cr$',
        r'^amount\s*\(?cr\.?\)?$', r'^received$',
    ],
    # ── running balance ───────────────────────────────────────────────────────
    'balance': [
        r'^closing\s*balance$', r'^balance$', r'^running\s*balance$',
        r'^available\s*balance$', r'^ledger\s*balance$',
        r'^bal\.?$', r'^closing\s*bal\.?$',
    ],
    # ── single amount column (some banks use one column + dr/cr flag) ─────────
    'amount': [
        r'^amount$', r'^transaction\s*amount$', r'^txn\s*amount$',
    ],
    # ── dr/cr flag ────────────────────────────────────────────────────────────
    'dr_cr_flag': [
        r'^dr\.?/?cr\.?$', r'^type$', r'^transaction\s*type$',
        r'^cr\.?/dr\.?$', r'^debit\s*credit$',
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY RULES  (extend freely — no code changes elsewhere needed)
# ══════════════════════════════════════════════════════════════════════════════

CATEGORY_RULES = {
    'EMI / Loan':          r'ACH\s*D|EMI|LOAN|FINANCE|KISETSUSAISON|BAJAJ|NACH|REPAYMENT|INSTALLMENT',
    'Utilities':           r'AIRTEL|BSNL|VODAFONE|JIO|ELECTRICITY|BESCOM|TATA\s*POWER|GAS\s*BILL|WATER\s*BILL|BROADBAND|DTH|RECHARGE|UTILITY',
    'Food & Dining':       r'ZOMATO|SWIGGY|RESTAURANTS?|FOOD|CAFE|DOMINO|PIZZA|BURGER|STARBUCKS|DINING|BIRYANI|BAKERY|DUNKIN|KFC|MCDONALD|SUBWAY',
    'Groceries':           r'BIGBASKET|GROFERS|BLINKIT|GROCERY|DMART|RELIANCE\s*FRESH|SUPERMARKET|NILGIRIS|ZEPTO|INSTAMART|MORE\s*RETAIL',
    'Entertainment':       r'NETFLIX|AMAZON\s*PRIME|HOTSTAR|DISNEY|SPOTIFY|YOUTUBE|GAMING|PLAYSTATI|XBOX|STEAM|BOOKMYSHOW|PVRINOX|CINEPOLIS',
    'Shopping / Fashion':  r'AMAZON|FLIPKART|MYNTRA|AJIO|NYKAA|H&M|TONI\s*AND\s*GUY|MEESHO|SHOPSY|SHEIN|ZARA|LIFESTYLE|WESTSIDE|PANTALOON',
    'Travel':              r'IRCTC|RAILWAYS|UBER|OLA|RAPIDO|FLIGHT|MAKEMYTRIP|YATRA|GOIBIBO|CLEARTRIP|PETROL|FUEL|INDIGO|AIRINDIA|SPICEJET',
    'ATM / Cash':          r'ATM|CASH\s*WITHDRAWAL|CASH\s*WDL',
    'Health':              r'PHARMACY|HOSPITAL|CLINIC|DOCTOR|MEDICAL|APOLLO|FORTIS|THYROCARE|LYBRATE|MEDPLUS|NETMEDS|1MG',
    'Investment / Saving': r'MUTUAL\s*FUND|SIP|ZERODHA|GROWW|KUVERA|NSE|BSE|FD\s*|PPF|INSURANCE|LIC|HDFC\s*LIFE|ICICI\s*PRU',
    'Alcohol / Bars':      r'\bBAR\b|LIQUOR|WINE\s*SHOP|BEER|SPIRITS|TASMAC|\bPUB\b|BREWERI',
    'Salary / Income':     r'SALARY|PAYROLL|NEFT\s*CR|IMPS\s*CR|CREDIT\s*INTEREST|DIVIDEND',
}

IMPULSIVE_CATEGORIES = {
    'Food & Dining', 'Entertainment', 'Shopping / Fashion',
    'Alcohol / Bars', 'ATM / Cash'
}


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ANALYSER CLASS
# ══════════════════════════════════════════════════════════════════════════════

class BankStatementAnalyser:
    """
    End-to-end impulse behaviour analyser for bank statements.

    Supports:
    - CSV, TSV, TXT, XLSX file formats
    - Any bank's column naming convention (via semantic mapping)
    - Single-amount-column format with DR/CR flag
    - Dual debit/credit column format
    - Masked header rows (***) that banks insert
    - Multiple files concatenated for multi-year analysis

    Returns a structured dict ready to be JSON-serialised and sent to a frontend.
    """

    def __init__(self, currency_symbol: str = '₹'):
        self.currency = currency_symbol
        self._df_raw = None          # raw loaded dataframe
        self._df = None              # normalised dataframe
        self._df_monthly = None      # monthly feature matrix
        self._column_map = {}        # detected column mapping
        self._schema_report = {}     # what was detected and how

    # ──────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────────────────────────────────────

    def analyse(self, file_bytes: bytes = None, filename: str = '',
                filepath: str = None) -> dict:
        """
        Main entry point. Call with either file_bytes (for web upload) or filepath.

        Returns
        -------
        dict with keys:
            schema_report   – what columns were detected and how
            summary         – high-level numbers
            monthly_scores  – per-month risk scores + tier + profile + nudges
            category_spend  – spend by category
            risk_distribution – Low/Medium/High counts
            charts          – base64-encoded PNG charts for embedding in HTML
            warnings        – list of data quality warnings
        """
        # 1. Load
        raw_df = self._load(file_bytes=file_bytes, filename=filename, filepath=filepath)

        # 2. Detect columns dynamically
        self._df = self._normalise(raw_df)

        # 3. Tag categories
        self._tag_categories()

        # 4. Build monthly feature matrix
        self._df_monthly = self._build_monthly_features()

        # 5. Score with ML ensemble
        self._compute_risk_scores()

        # 6. Assign profiles + nudges
        self._assign_profiles()

        # 7. Optional: ML classification (if enough labelled months)
        self._run_classification()

        # 8. Generate charts
        charts = self._generate_charts()

        # 9. Compile result
        return self._compile_result(charts)

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 1 — DYNAMIC LOADING
    # ──────────────────────────────────────────────────────────────────────────

    def _load(self, file_bytes=None, filename='', filepath=None) -> pd.DataFrame:
        """Detect format, parse file, strip masked rows."""
        ext = filename.lower().split('.')[-1] if filename else (
              filepath.lower().split('.')[-1] if filepath else 'csv')

        # Read raw bytes or file
        if file_bytes is not None:
            buf = io.BytesIO(file_bytes)
        else:
            buf = filepath

        if ext in ('xlsx', 'xls'):
            # First, read without skipping to find the header row
            df_test = pd.read_excel(buf, dtype=str, header=None)
            header_idx = 0
            
            # Check if the first row is already a recognizable header
            has_recognizable = False
            if not df_test.empty:
                raw_cols = set(df_test.iloc[0].dropna().astype(str).str.strip().str.lower())
                for canonical, patterns in COLUMN_SEMANTIC_MAP.items():
                    if any(any(re.fullmatch(p, raw) for p in patterns) for raw in raw_cols):
                        has_recognizable = True
                        break
            
            if not has_recognizable:
                # Scan the first 100 rows for a recognizable header
                for i in range(min(100, len(df_test))):
                    row_vals = df_test.iloc[i].dropna().astype(str).str.lower()
                    if any(any(term in val for val in row_vals) for term in ['date', 'txn date', 'transaction date']):
                        if any(any(term in val for val in row_vals) for term in ['amount', 'withdrawal', 'deposit', 'debit', 'credit', 'balance', 'description']):
                            header_idx = i
                            break
            
            if header_idx > 0:
                 # Re-read from the start to reset the buffer/file pointer if needed
                 if isinstance(buf, io.BytesIO):
                     buf.seek(0)
                 df = pd.read_excel(buf, dtype=str, skiprows=header_idx)
            else:
                 if isinstance(buf, io.BytesIO):
                     buf.seek(0)
                 df = pd.read_excel(buf, dtype=str)

        elif ext in ('tsv', 'txt'):
            df = self._try_delimiters(buf, ['\t', ',', ';', '|'])
        else:  # csv default
            df = self._try_delimiters(buf, [',', '\t', ';', '|'])

        # Strip masked rows (banks insert a row of *** below header)
        mask_row = df.apply(lambda r: r.astype(str).str.fullmatch(r'\*+').all(), axis=1)
        df = df[~mask_row].copy()
        df.reset_index(drop=True, inplace=True)

        # Drop fully-empty rows
        df.dropna(how='all', inplace=True)
        df.reset_index(drop=True, inplace=True)

        self._raw_columns = df.columns.tolist()
        return df

    def _try_delimiters(self, buf, delimiters):
        """Try each delimiter, pick the one that produces the most columns."""
        best, best_cols = None, 0
        if isinstance(buf, io.BytesIO):
            content = buf.read()
            content_str = content.decode('utf-8', errors='ignore')
        else:
            with open(buf, 'rb') as f:
                content = f.read()
            content_str = content.decode('utf-8', errors='ignore')

        lines = content_str.splitlines()

        for delim in delimiters:
            try:
                # 1. First Pass: Try to read the whole file to see if we can find the columns directly
                df_test = pd.read_csv(io.BytesIO(content), sep=delim, dtype=str, engine='python', on_bad_lines='skip')
                
                # Check if this df has any recognizable columns
                raw_cols = {str(c).strip().lower() for c in df_test.columns}
                has_recognizable = False
                for canonical, patterns in COLUMN_SEMANTIC_MAP.items():
                    if any(any(re.fullmatch(p, raw) for p in patterns) for raw in raw_cols):
                        has_recognizable = True
                        break
                
                if has_recognizable and len(df_test.columns) > best_cols:
                    best, best_cols = df_test, len(df_test.columns)
                    continue
                
                # 2. Second Pass: If no recognizable columns, try to find a header row
                # Many statements have a preamble. Scan the first 100 rows for a recognizable header.
                header_idx = 0
                for i, line in enumerate(lines[:100]):
                    line_lower = line.lower()
                    if any(term in line_lower for term in ['date', 'txn date', 'transaction date']):
                        if any(term in line_lower for term in ['amount', 'withdrawal', 'deposit', 'debit', 'credit', 'balance', 'description']):
                            header_idx = i
                            break
                
                if header_idx > 0:
                    # Re-read skipping the preamble
                    clean_content = '\n'.join(lines[header_idx:]).encode('utf-8')
                    df_skip = pd.read_csv(io.BytesIO(clean_content), sep=delim, dtype=str, engine='python', on_bad_lines='skip')
                    if len(df_skip.columns) > best_cols:
                        best, best_cols = df_skip, len(df_skip.columns)

            except Exception:
                continue
        if best is None:
            raise ValueError("Could not parse file with any known delimiter (,  tab  ;  |)")
        return best

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 2 — DYNAMIC COLUMN DETECTION & NORMALISATION
    # ──────────────────────────────────────────────────────────────────────────

    def _normalise(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect which raw column maps to which canonical role using the
        COLUMN_SEMANTIC_MAP.  Build a clean normalised dataframe regardless
        of the bank's naming convention.
        """
        raw_cols = {c: c.strip().lower() for c in df.columns}
        detected = {}          # canonical_name → raw_column_name
        ambiguous = []

        for canonical, patterns in COLUMN_SEMANTIC_MAP.items():
            matches = []
            for raw, raw_lower in raw_cols.items():
                if any(re.fullmatch(p, raw_lower) for p in patterns):
                    matches.append(raw)
            if len(matches) == 1:
                detected[canonical] = matches[0]
            elif len(matches) > 1:
                # Prefer exact case-insensitive match first, then first hit
                detected[canonical] = matches[0]
                ambiguous.append(f"'{canonical}' matched multiple columns: {matches}. Used '{matches[0]}'.")

        # ── Validate minimum required columns ──────────────────────────────
        warnings_list = list(ambiguous)
        required = ['date']  # absolute minimum
        missing = [r for r in required if r not in detected]
        if missing:
            raise ValueError(
                f"Could not detect required columns: {missing}.\n"
                f"Detected columns: {list(detected.values())}\n"
                f"Raw columns in file: {list(df.columns)}"
            )

        # ── Resolve amount columns ──────────────────────────────────────────
        # Case A: separate withdrawal + deposit columns (most Indian banks)
        # Case B: single amount column + DR/CR flag
        # Case C: single amount column (positive=credit, negative=debit or vice versa)

        has_withdrawal = 'withdrawal' in detected
        has_deposit    = 'deposit'    in detected
        has_amount     = 'amount'     in detected
        has_flag       = 'dr_cr_flag' in detected

        if not has_withdrawal and not has_deposit and not has_amount:
            raise ValueError(
                "No amount column found. Expected one of: "
                "Withdrawal/Debit, Deposit/Credit, or Amount columns."
            )

        # ── Build clean df ──────────────────────────────────────────────────
        clean = pd.DataFrame()

        # Date
        date_raw = df[detected['date']].astype(str).str.strip()
        clean['date'] = pd.to_datetime(date_raw, dayfirst=True, errors='coerce')
        n_bad_dates = clean['date'].isna().sum()
        if n_bad_dates > 0:
            warnings_list.append(f"{n_bad_dates} rows had unparseable dates and were dropped.")
        clean.dropna(subset=['date'], inplace=True)

        # Narration
        if 'narration' in detected:
            clean['narration'] = df.loc[clean.index, detected['narration']].astype(str).str.strip()
        else:
            clean['narration'] = ''
            warnings_list.append("No narration/description column found — category tagging will be limited.")

        # Ref no
        clean['ref_no'] = (df.loc[clean.index, detected['ref_no']].astype(str).str.strip()
                           if 'ref_no' in detected else '')

        # Balance
        if 'balance' in detected:
            clean['balance'] = self._to_numeric(df.loc[clean.index, detected['balance']])
        else:
            clean['balance'] = np.nan
            warnings_list.append("No balance column found — balance trend chart will be skipped.")

        # Amount columns
        if has_withdrawal and has_deposit:
            # Classic dual-column format
            clean['withdrawal'] = self._to_numeric(df.loc[clean.index, detected['withdrawal']])
            clean['deposit']    = self._to_numeric(df.loc[clean.index, detected['deposit']])

        elif has_amount and has_flag:
            # Single amount + DR/CR flag
            amt = self._to_numeric(df.loc[clean.index, detected['amount']])
            flag = df.loc[clean.index, detected['dr_cr_flag']].astype(str).str.strip().str.upper()
            is_debit = flag.isin(['DR', 'D', 'DEBIT', 'DR.'])
            clean['withdrawal'] = amt.where(is_debit, 0)
            clean['deposit']    = amt.where(~is_debit, 0)
            warnings_list.append("Single amount + DR/CR flag format detected and handled.")

        elif has_amount:
            # Single amount — try to infer direction from sign or balance movement
            amt = self._to_numeric(df.loc[clean.index, detected['amount']])
            if (amt < 0).any():
                # Negative = debit convention
                clean['withdrawal'] = amt.where(amt < 0, 0).abs()
                clean['deposit']    = amt.where(amt > 0, 0)
                warnings_list.append("Single amount column (negative=debit) format detected.")
            else:
                # All positive — use balance movement to infer direction
                if 'balance' in detected:
                    bal = clean['balance']
                    bal_diff = bal.diff().shift(-1)
                    is_debit = bal_diff < 0
                    clean['withdrawal'] = amt.where(is_debit, 0)
                    clean['deposit']    = amt.where(~is_debit, 0)
                    warnings_list.append("Single amount column: direction inferred from balance movement.")
                else:
                    clean['withdrawal'] = amt
                    clean['deposit']    = 0.0
                    warnings_list.append("Single amount column with no flag — treated all as withdrawals.")

        elif has_withdrawal:
            clean['withdrawal'] = self._to_numeric(df.loc[clean.index, detected['withdrawal']])
            clean['deposit']    = 0.0
        else:
            clean['withdrawal'] = 0.0
            clean['deposit']    = self._to_numeric(df.loc[clean.index, detected['deposit']])

        clean['withdrawal'] = clean['withdrawal'].fillna(0)
        clean['deposit']    = clean['deposit'].fillna(0)

        # ── Time features ───────────────────────────────────────────────────
        clean = clean.sort_values('date').reset_index(drop=True)
        clean['day_of_week']     = clean['date'].dt.dayofweek
        clean['day_of_month']    = clean['date'].dt.day
        clean['month']           = clean['date'].dt.month
        clean['year']            = clean['date'].dt.year
        clean['is_end_of_month'] = (clean['day_of_month'] >= 25).astype(int)
        clean['month_year']      = clean['date'].dt.to_period('M')
        clean['is_credit']       = (clean['deposit'] > 0).astype(int)

        # ── Store schema report ─────────────────────────────────────────────
        self._column_map = detected
        self._schema_report = {
            'raw_columns':       list(df.columns),
            'detected_mapping':  {k: v for k, v in detected.items()},
            'amount_format':     ('dual_column' if has_withdrawal and has_deposit
                                  else 'single_with_flag' if has_flag
                                  else 'single_amount'),
            'total_rows_loaded': len(clean),
            'warnings':          warnings_list,
        }

        return clean

    @staticmethod
    def _to_numeric(series: pd.Series) -> pd.Series:
        """Robustly convert a string series to float, handling commas and blanks."""
        return (series.astype(str)
                      .str.replace(',', '', regex=False)
                      .str.replace(' ', '', regex=False)
                      .str.strip()
                      .replace({'': np.nan, '-': np.nan, 'nan': np.nan, 'None': np.nan})
                      .astype(float)
                      .fillna(0))

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 3 — CATEGORY TAGGING
    # ──────────────────────────────────────────────────────────────────────────

    def _tag_categories(self):
        def categorise(narration):
            n = str(narration).upper()
            for cat, pattern in CATEGORY_RULES.items():
                if re.search(pattern, n):
                    return cat
            return 'Other'

        self._df['category'] = self._df['narration'].apply(categorise)
        self._df['is_impulsive_category'] = (
            self._df['category'].isin(IMPULSIVE_CATEGORIES).astype(int)
        )

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 4 — MONTHLY FEATURE ENGINEERING
    # ──────────────────────────────────────────────────────────────────────────

    def _build_monthly_features(self) -> pd.DataFrame:
        rows = []
        df = self._df
        spends = df[df['withdrawal'] > 0]

        for period, grp in spends.groupby('month_year'):
            full_month = df[df['month_year'] == period]

            n_txn       = len(grp)
            total_spend = grp['withdrawal'].sum()
            avg_txn     = grp['withdrawal'].mean()
            std_txn     = grp['withdrawal'].std(ddof=0)
            cv_amount   = std_txn / (avg_txn + 1e-6)

            # End-of-month surge
            eom_spend   = grp[grp['is_end_of_month'] == 1]['withdrawal'].sum()
            reg_spend   = grp[grp['is_end_of_month'] == 0]['withdrawal'].sum()
            eom_ratio   = eom_spend / (reg_spend + 1e-6)
            eom_txn_share = grp['is_end_of_month'].mean()

            # Impulsive category share
            imp_cat_share = grp['is_impulsive_category'].mean()
            imp_cat_spend_share = (
                grp[grp['is_impulsive_category'] == 1]['withdrawal'].sum()
                / (total_spend + 1e-6)
            )

            # Large transactions (> 2× median)
            med = grp['withdrawal'].median()
            large_txn_share = (grp['withdrawal'] > med * 2).mean()

            # Spending spike (max txn / avg txn)
            spike_ratio = grp['withdrawal'].max() / (avg_txn + 1e-6)

            # Weekend spend
            weekend_share = (
                grp[grp['day_of_week'].isin([5, 6])]['withdrawal'].sum()
                / (total_spend + 1e-6)
            )

            # Income & spend-to-income
            income          = full_month['deposit'].sum()
            net_cashflow    = income - total_spend
            spend_to_income = total_spend / (income + 1e-6)

            # ATM cash share
            atm_share = (grp['category'] == 'ATM / Cash').sum() / (n_txn + 1e-6)

            # UPI share (digital spend signal)
            upi_share = grp['narration'].str.upper().str.startswith('UPI').mean()

            rows.append({
                'month_year':          str(period),
                'n_transactions':      n_txn,
                'total_spend':         total_spend,
                'income':              income,
                'net_cashflow':        net_cashflow,
                'avg_txn_amount':      avg_txn,
                'std_txn_amount':      std_txn,
                'cv_amount':           cv_amount,
                'eom_spend_ratio':     eom_ratio,
                'eom_txn_share':       eom_txn_share,
                'imp_cat_share':       imp_cat_share,
                'imp_cat_spend_share': imp_cat_spend_share,
                'large_txn_share':     large_txn_share,
                'spike_ratio':         spike_ratio,
                'weekend_spend_share': weekend_share,
                'spend_to_income_ratio': spend_to_income,
                'atm_cash_share':      atm_share,
                'upi_share':           upi_share,
            })

        return pd.DataFrame(rows)

    FEATURE_COLS = [
        'cv_amount', 'eom_spend_ratio', 'eom_txn_share',
        'imp_cat_share', 'imp_cat_spend_share', 'large_txn_share',
        'spike_ratio', 'weekend_spend_share', 'spend_to_income_ratio',
        'atm_cash_share',
    ]

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 5 — DATA-DRIVEN RISK SCORING (ML Ensemble)
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_risk_scores(self):
        dm = self._df_monthly
        X  = dm[self.FEATURE_COLS].fillna(0)

        # ── Method 1: Z-Score Anomaly (personalised baseline) ────────────────
        z   = stats.zscore(X, ddof=1, nan_policy='omit')
        z   = np.nan_to_num(z, nan=0.0)
        z_pos = np.clip(z, 0, None)          # only flag upward deviations
        z_raw = np.sqrt((z_pos ** 2).mean(axis=1))

        # ── Method 2: Isolation Forest (unsupervised ML anomaly) ─────────────
        contamination = max(0.05, min(0.4, 1 / 3))
        iso = IsolationForest(n_estimators=300, contamination=contamination,
                              random_state=42, max_samples='auto')
        iso.fit(X)
        iso_raw = -iso.decision_function(X)   # flip: higher = more anomalous

        # ── Method 3: PCA Reconstruction Error ───────────────────────────────
        scaler_pca = StandardScaler()
        Xs = scaler_pca.fit_transform(X)
        ev = np.cumsum(PCA().fit(Xs).explained_variance_ratio_)
        n_comp = max(1, min(len(self.FEATURE_COLS) - 1,
                            int(np.searchsorted(ev, 0.80)) + 1))
        pca = PCA(n_components=n_comp, random_state=42)
        Xr  = pca.inverse_transform(pca.fit_transform(Xs))
        pca_raw = np.mean((Xs - Xr) ** 2, axis=1)

        # ── Ensemble ─────────────────────────────────────────────────────────
        def norm01(a):
            lo, hi = a.min(), a.max()
            return (a - lo) / (hi - lo) if hi > lo else np.full_like(a, 0.5)

        ensemble = pd.Series(
            (norm01(z_raw) + norm01(iso_raw) + norm01(pca_raw)) / 3 * 100,
            index=dm.index
        ).round(2)

        dm['score_zscore']       = np.round(norm01(z_raw)   * 100, 2)
        dm['score_isoforest']    = np.round(norm01(iso_raw)  * 100, 2)
        dm['score_pca']          = np.round(norm01(pca_raw)  * 100, 2)
        dm['impulse_risk_score'] = ensemble

        # ── Adaptive thresholds from own data ────────────────────────────────
        p33 = float(np.percentile(ensemble, 33))
        p67 = float(np.percentile(ensemble, 67))
        self._p33, self._p67 = p33, p67

        dm['risk_tier'] = ensemble.apply(
            lambda s: 'High' if s >= p67 else ('Medium' if s >= p33 else 'Low'))
        dm['is_high_impulse'] = (dm['risk_tier'] == 'High').astype(int)

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 6 — BEHAVIOUR PROFILES & NUDGES
    # ──────────────────────────────────────────────────────────────────────────

    NUDGE_MAP = {
        '🔥 Overspender':         ['🚨 You spent more than you earned this month.',
                                    '💳 Set a hard spending cap of 80% of last month\'s income.',
                                    '🏦 Auto-transfer 10% of salary to savings on pay day.'],
        '📅 Month-End Binger':    ['💰 Move 25% of balance to a locked savings pocket on the 20th.',
                                    '📉 Set a forecast alert when projected EOM spend exceeds budget.',
                                    '🎯 Challenge: stay under ₹500/day in the last week.'],
        '🎮 Lifestyle Overindulger': ['🏷️ Set monthly caps per category (entertainment, dining etc.).',
                                    '📱 Weekly category breakdown notification every Monday.',
                                    '🔁 For every impulsive spend > ₹500, invest the same amount.'],
        '⚡ High Impulse Month':  ['⏰ Apply a 24-hour "cooling off" rule for non-essential purchases.',
                                    '📈 Review spending daily for 2 weeks.',
                                    '🤝 Share your budget with an accountability partner.'],
        '🔄 Binge-Pause Cycler':  ['📅 Weekly envelope budget — once weekly cash is gone, stop.',
                                    '📊 Visualise spending rhythm with a monthly heatmap.'],
        '⚠️ Situational Spender': ['📣 You tend to overspend on specific days — review those triggers.',
                                    '🧘 Pause before large transactions: "Is this planned?"'],
        '✅ Disciplined Month':   ['🎖️ Great month! Consider investing surplus in a SIP or FD.',
                                    '📈 Increase your SIP contribution this month.'],
    }

    def _assign_profiles(self):
        def profile(row):
            s   = row['impulse_risk_score']
            sti = row['spend_to_income_ratio']
            eom = row['eom_spend_ratio']
            cat = row['imp_cat_spend_share']
            cv  = row['cv_amount']
            p67 = self._p67
            p33 = self._p33
            if s >= p67:
                if sti > 0.9:  return '🔥 Overspender'
                if eom > 1.5:  return '📅 Month-End Binger'
                if cat > 0.5:  return '🎮 Lifestyle Overindulger'
                return '⚡ High Impulse Month'
            elif s >= p33:
                if cv > 1.5:   return '🔄 Binge-Pause Cycler'
                return '⚠️ Situational Spender'
            return '✅ Disciplined Month'

        self._df_monthly['behaviour_profile'] = self._df_monthly.apply(profile, axis=1)

        def generate_nudges(row):
            p = row['behaviour_profile']
            total_spend = row['total_spend']
            eom_spend_ratio = row['eom_spend_ratio']
            base_nudges = self.NUDGE_MAP.get(p, []).copy()
            
            # Make nudges dynamic based on the actual month's data to avoid exact duplicates
            dynamic_nudges = []
            import random
            
            if p == '🔥 Overspender':
                dynamic_nudges.append(f"🚨 You spent ₹{total_spend:,.0f} this month, pushing your budget to the limit.")
                dynamic_nudges.append(f"💳 Set a hard cap of 80% of this month's income for next month.")
            elif p == '📅 Month-End Binger':
                dynamic_nudges.append(f"💰 Your end-of-month spend was {eom_spend_ratio:.1f}x higher than usual.")
                dynamic_nudges.append(f"📉 Try to lock away 20% of your balance before the 20th of the month.")
            elif p == '🎮 Lifestyle Overindulger':
                dynamic_nudges.append(f"🏷️ A large chunk of your ₹{total_spend:,.0f} went to impulsive categories.")
                dynamic_nudges.append(f"📱 Try setting a weekly limit for entertainment and dining.")
            elif p == '⚡ High Impulse Month':
                dynamic_nudges.append(f"⏰ High risk score detected ({row['impulse_risk_score']:.1f}). Apply a 24h cooling off rule.")
                dynamic_nudges.append(f"📈 Review your spending daily to catch unplanned purchases.")
            elif p == '🔄 Binge-Pause Cycler':
                dynamic_nudges.append(f"📅 Your spending was highly volatile this month (CV: {row['cv_amount']:.2f}).")
                dynamic_nudges.append(f"📊 Try a weekly envelope budget to smooth out your cash flow.")
            elif p == '⚠️ Situational Spender':
                dynamic_nudges.append(f"📣 You had specific high-spend days. Review your largest transactions.")
                dynamic_nudges.append(f"🧘 Pause before large transactions: 'Is this planned?'")
            elif p == '✅ Disciplined Month':
                dynamic_nudges.append(f"🎖️ Great month! You kept your risk score low at {row['impulse_risk_score']:.1f}.")
                dynamic_nudges.append(f"📈 Consider investing whatever surplus you have left in a SIP or FD.")
            else:
                dynamic_nudges = base_nudges
                
            return dynamic_nudges

        self._df_monthly['nudges'] = self._df_monthly.apply(generate_nudges, axis=1)

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 7 — OPTIONAL ML CLASSIFICATION
    # ──────────────────────────────────────────────────────────────────────────

    def _run_classification(self):
        dm = self._df_monthly
        X  = dm[self.FEATURE_COLS].fillna(0)
        y  = dm['is_high_impulse']
        self._ml_results = {}

        if y.nunique() < 2:
            self._ml_results['status'] = 'skipped_single_class'
            return

        scaler = StandardScaler()
        Xs = scaler.fit_transform(X)
        cv_folds = min(5, int(y.sum()), int((y == 0).sum()))

        models = {
            'Logistic Regression': LogisticRegression(max_iter=500, C=0.5, random_state=42),
            'Random Forest':       RandomForestClassifier(n_estimators=100, random_state=42),
            'Gradient Boosting':   GradientBoostingClassifier(n_estimators=100, random_state=42),
        }

        if cv_folds < 2:
            # Simple split
            X_tr, X_te, y_tr, y_te = train_test_split(Xs, y, test_size=0.3,
                                                        random_state=42)
            scores = {}
            for name, model in models.items():
                model.fit(X_tr, y_tr)
                prob = model.predict_proba(X_te)[:, 1]
                try:
                    auc = float(roc_auc_score(y_te, prob))
                except Exception:
                    auc = float('nan')
                scores[name] = {'auc': round(auc, 4), 'method': 'train_test_split'}
            self._ml_results = {'status': 'completed', 'mode': 'split', 'scores': scores}
        else:
            scores = {}
            for name, model in models.items():
                cv_s = cross_val_score(model, Xs, y, cv=cv_folds, scoring='roc_auc')
                model.fit(Xs, y)
                scores[name] = {'cv_auc': round(float(cv_s.mean()), 4),
                                'cv_std':  round(float(cv_s.std()), 4),
                                'method':  f'{cv_folds}-fold CV'}
            # Feature importances from RF
            rf = models['Random Forest']
            rf.fit(Xs, y)
            self._feature_importances = pd.Series(
                rf.feature_importances_, index=self.FEATURE_COLS).sort_values(ascending=False)
            self._ml_results = {'status': 'completed', 'mode': 'cross_val',
                                'scores': scores,
                                'feature_importances': self._feature_importances.round(4).to_dict()}

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 8 — CHART GENERATION (base64 PNG, embeddable in HTML/React)
    # ──────────────────────────────────────────────────────────────────────────

    def _fig_to_b64(self, fig) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=130, bbox_inches='tight')
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

    def _generate_charts(self) -> dict:
        charts = {}
        df  = self._df
        dm  = self._df_monthly
        spends = df[df['withdrawal'] > 0]
        tier_clr = {'High': '#E74C3C', 'Medium': '#F39C12', 'Low': '#2ECC71'}

        # ── Chart 1: Risk Score Timeline ─────────────────────────────────────
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.bar(dm['month_year'].astype(str), dm['impulse_risk_score'],
               color=[tier_clr[t] for t in dm['risk_tier']], alpha=0.85, zorder=3)
        ax.axhline(self._p67, color='red',    ls='--', lw=1.5,
                   label=f'High ≥ {self._p67:.0f}')
        ax.axhline(self._p33, color='orange', ls='--', lw=1.5,
                   label=f'Medium ≥ {self._p33:.0f}')
        ax.set_title('Impulse Risk Score — Monthly Timeline', fontweight='bold')
        ax.set_ylabel('Score (0–100)')
        ax.tick_params(axis='x', rotation=45, labelsize=7)
        ax.legend(fontsize=8); ax.grid(axis='y', alpha=0.3)
        charts['risk_timeline'] = {
            'base64': self._fig_to_b64(fig),
            'interpretation': "This timeline tracks how your spending impulsivity fluctuates month-over-month. Green bars represent months where your spending was controlled and disciplined. Yellow and Red bars indicate periods where your spending patterns became erratic, showing high variance or sudden spikes, which pushes your risk score up."
        }
        plt.close(fig)

        # ── Chart 2: Method Breakdown ─────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(12, 4))
        x = np.arange(len(dm)); w = 0.25
        ax.bar(x - w, dm['score_zscore'],    w, label='Z-Score',          color='#3498DB', alpha=0.85)
        ax.bar(x,     dm['score_isoforest'], w, label='Isolation Forest',  color='#E67E22', alpha=0.85)
        ax.bar(x + w, dm['score_pca'],       w, label='PCA Recon. Error',  color='#9B59B6', alpha=0.85)
        ax.set_xticks(x)
        ax.set_xticklabels(dm['month_year'].astype(str), rotation=45, ha='right', fontsize=7)
        ax.set_title('Risk Score — Method Breakdown per Month', fontweight='bold')
        ax.set_ylabel('Score (0–100)'); ax.legend(fontsize=8); ax.grid(axis='y', alpha=0.3)
        charts['method_breakdown'] = {
            'base64': self._fig_to_b64(fig),
            'interpretation': "Here we break down the overall risk score into our three ML methods. Z-Score flags simple unusually large transactions. Isolation Forest detects hidden anomalies across multiple factors simultaneously. PCA Error highlights months where your spending fundamentally deviated from your usual 'healthy' baseline print."
        }
        plt.close(fig)

        # ── Chart 3: Category Spend ───────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(10, 5))
        cat_spend = spends.groupby('category')['withdrawal'].sum().sort_values()
        colors_c  = ['#E74C3C' if c in IMPULSIVE_CATEGORIES else '#3498DB'
                     for c in cat_spend.index]
        cat_spend.plot.barh(ax=ax, color=colors_c)
        ax.set_title('Total Spend by Category  (🔴 = Impulsive)', fontweight='bold')
        ax.set_xlabel(f'{self.currency}'); ax.tick_params(axis='y', labelsize=8)
        charts['category_spend'] = {
            'base64': self._fig_to_b64(fig),
            'interpretation': "This chart visualises where your money goes. Categories highlighted in red (like Food, Entertainment, Shopping) are traditionally classified as 'Impulsive' and heavily influence your risk score if they dominate your overall cash outflow."
        }
        plt.close(fig)

        # ── Chart 4: Monthly Spend Trend ──────────────────────────────────────
        fig, ax = plt.subplots(figsize=(12, 4))
        monthly_s = spends.groupby('month_year')['withdrawal'].sum()
        ax.bar(monthly_s.index.astype(str), monthly_s.values, color='steelblue', alpha=0.8)
        ax.set_title('Monthly Withdrawal Trend', fontweight='bold')
        ax.set_ylabel(f'{self.currency} Withdrawn')
        ax.tick_params(axis='x', rotation=45, labelsize=7)
        for i, v in enumerate(monthly_s.values):
            ax.text(i, v + (v * 0.02), f'{v/1000:.0f}k', ha='center', va='bottom', fontsize=7)
        charts['monthly_trend'] = {
            'base64': self._fig_to_b64(fig),
            'interpretation': "A simple overview of your total cash outflow over time. Consistent bar heights indicate stable budgeting, while huge spikes suggest unexpected large expenses or unbudgeted shopping sprees."
        }
        plt.close(fig)

        # ── Chart 5: Balance Trend ────────────────────────────────────────────
        if 'balance' in df.columns and df['balance'].notna().any():
            fig, ax = plt.subplots(figsize=(12, 4))
            df_b = df.dropna(subset=['balance'])
            ax.plot(df_b['date'], df_b['balance'], color='#27AE60', lw=2)
            ax.fill_between(df_b['date'], df_b['balance'], color='#27AE60', alpha=0.1)
            ax.set_title('Running Balance Over Time', fontweight='bold')
            ax.set_ylabel(f'Balance ({self.currency})')
            ax.grid(alpha=0.3)
            # format y axis
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
            charts['balance_trend'] = {
                'base64': self._fig_to_b64(fig),
                'interpretation': "Your running balance acts as the ultimate pulse check. A consistent upward trend indicates healthy saving habits. Sharp drops, especially towards zero, represent cash flow crunches."
            }
            plt.close(fig)

        # ── Chart 6: End of Month vs Regular ──────────────────────────────────
        fig, ax = plt.subplots(figsize=(10, 5))
        eom = dm['eom_spend_ratio'].mean()
        ax.bar(['Regular (Days 1-24)', 'End of Month (Days 25+)'],
               [1, eom], color=['#34495E', '#E74C3C'])
        ax.set_title('Average Spend Intensity: Regular vs Month-End', fontweight='bold')
        charts['eom_comparison'] = {
            'base64': self._fig_to_b64(fig),
            'interpretation': "Many people binge spend their remaining cash right before payday. This chart compares your spending intensity at the end of the month (Days 25+) against the rest of the month. A high red bar signals 'Month-End Binger' behaviour."
        }
        plt.close(fig)

        # ── Chart 7: Behaviour Profiles Pie ───────────────────────────────────
        fig, ax = plt.subplots(figsize=(6, 6))
        prof_counts = dm['behaviour_profile'].value_counts()
        ax.pie(prof_counts, labels=prof_counts.index, autopct='%1.0f%%',
               startangle=140, colors=plt.cm.Set3.colors)
        ax.set_title('Your Behaviour Profiles', fontweight='bold')
        charts['behaviour_profiles'] = {
            'base64': self._fig_to_b64(fig),
            'interpretation': "Your financial year summarized into distinct algorithmic profiles. It shows the proportion of months you spent as an 'Overspender', a 'Disciplined Saver', or a 'Situational Spender', giving you a high-level summary of your financial personality."
        }
        plt.close(fig)

        return charts

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 9 — COMPILE FINAL JSON-SERIALISABLE RESULT
    # ──────────────────────────────────────────────────────────────────────────

    def _compile_result(self, charts: dict) -> dict:
        df  = self._df
        dm  = self._df_monthly
        spends = df[df['withdrawal'] > 0]

        monthly_records = []
        for _, row in dm.sort_values('month_year').iterrows():
            monthly_records.append({
                'month':               str(row['month_year']),
                'total_spend':         round(float(row['total_spend']), 2),
                'income':              round(float(row['income']), 2),
                'n_transactions':      int(row['n_transactions']),
                'impulse_risk_score':  float(row['impulse_risk_score']),
                'score_zscore':        float(row['score_zscore']),
                'score_isoforest':     float(row['score_isoforest']),
                'score_pca':           float(row['score_pca']),
                'risk_tier':           row['risk_tier'],
                'behaviour_profile':   row['behaviour_profile'],
                'nudges':              list(row['nudges']),
                'key_features': {
                    'spend_to_income':     round(float(row['spend_to_income_ratio']), 3),
                    'eom_spend_ratio':     round(float(row['eom_spend_ratio']), 3),
                    'impulsive_cat_share': round(float(row['imp_cat_spend_share']), 3),
                    'cv_amount':           round(float(row['cv_amount']), 3),
                    'spike_ratio':         round(float(row['spike_ratio']), 3),
                },
            })

        cat_spend = (spends.groupby('category')['withdrawal']
                     .sum().sort_values(ascending=False).round(2).to_dict())

        return {
            'schema_report':       self._schema_report,
            'summary': {
                'date_range':       f"{df['date'].min().date()} → {df['date'].max().date()}",
                'total_months':     len(dm),
                'total_transactions': int(len(df)),
                'total_withdrawn':  round(float(df['withdrawal'].sum()), 2),
                'total_deposited':  round(float(df['deposit'].sum()), 2),
                'adaptive_thresholds': {
                    'low_below':     round(self._p33, 1),
                    'medium_range':  f"{self._p33:.1f} – {self._p67:.1f}",
                    'high_above':    round(self._p67, 1),
                },
            },
            'risk_distribution': dm['risk_tier'].value_counts().to_dict(),
            'monthly_scores':    monthly_records,
            'category_spend':    cat_spend,
            'ml_classification': self._ml_results,
            'charts':            charts,   # base64 PNG strings, embed as <img src="data:image/png;base64,...">
        }
