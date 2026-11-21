from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

def load_customers():
    csv_path = PROCESSED / "creditlens_customers.csv"
    if not csv_path.exists():
        raise FileNotFoundError("Processed dataset not found. Run the pipeline first.")
    df = pd.read_csv(csv_path)
    return prepare_dataframe(df)


def prepare_dataframe(df):
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    if "default_payment_next_month" in df.columns and "default_flag" not in df.columns:
        df["default_flag"] = pd.to_numeric(df["default_payment_next_month"], errors="coerce").fillna(0).astype(int)
    if "default_flag" not in df.columns:
        df["default_flag"] = 0

    if "limit_bal" in df.columns:
        df["limit_bal"] = pd.to_numeric(df["limit_bal"], errors="coerce")
    if "age" in df.columns:
        df["age"] = pd.to_numeric(df["age"], errors="coerce")

    if "credit_utilization_pct" not in df.columns:
        if {"bill_amt1", "limit_bal"}.issubset(df.columns):
            df["credit_utilization_pct"] = np.where(
                df["limit_bal"] > 0,
                df["bill_amt1"].clip(lower=0) / df["limit_bal"] * 100,
                np.nan,
            )

    bill_cols = [c for c in [f"bill_amt{i}" for i in range(1, 7)] if c in df.columns]
    payment_cols = [c for c in [f"pay_amt{i}" for i in range(1, 7)] if c in df.columns]
    if bill_cols:
        df["avg_bill_6m"] = df[bill_cols].mean(axis=1)
        df["total_bill_6m"] = df[bill_cols].sum(axis=1)
    if payment_cols:
        df["avg_payment_6m"] = df[payment_cols].mean(axis=1)
        df["total_payment_6m"] = df[payment_cols].sum(axis=1)

    pay_cols = [c for c in ["pay_0", "pay_2", "pay_3", "pay_4", "pay_5", "pay_6"] if c in df.columns]
    if pay_cols:
        df["months_delayed"] = df[pay_cols].apply(pd.to_numeric, errors="coerce").gt(0).sum(axis=1)
        df["repayment_segment"] = np.select(
            [df["months_delayed"] == 0, df["months_delayed"] <= 2],
            ["No recorded delay", "Occasional delay"],
            default="Frequent delay",
        )

    if "limit_bal" in df.columns:
        df["credit_limit_segment"] = pd.cut(
            df["limit_bal"],
            bins=[-np.inf, 50000, 150000, 300000, np.inf],
            labels=["Below 50K", "50K–150K", "150K–300K", "Above 300K"],
        ).astype(str)

    if "age" in df.columns:
        df["age_group"] = pd.cut(
            df["age"],
            bins=[17, 25, 35, 45, 55, np.inf],
            labels=["18–25", "26–35", "36–45", "46–55", "56+"],
            right=True,
        ).astype(str)
    return df


def filter_customers(df, credit_segments=None, repayment_segments=None, search=None):
    filtered = df.copy()
    if credit_segments:
        filtered = filtered[filtered["credit_limit_segment"].isin(credit_segments)]
    if repayment_segments:
        filtered = filtered[filtered["repayment_segment"].isin(repayment_segments)]
    if search:
        needle = str(search).strip().lower()
        if needle:
            text = filtered.astype(str).apply(lambda col: col.str.lower())
            mask = text.apply(lambda col: col.str.contains(needle, regex=False, na=False)).any(axis=1)
            filtered = filtered.loc[mask]
    return filtered


def kpis(df):
    total = len(df)
    defaults = int(pd.to_numeric(df["default_flag"], errors="coerce").fillna(0).sum())
    return {
        "customers": total,
        "exposure": float(pd.to_numeric(df["limit_bal"], errors="coerce").fillna(0).sum()) if "limit_bal" in df else 0.0,
        "avg_limit": float(pd.to_numeric(df["limit_bal"], errors="coerce").mean()) if "limit_bal" in df else 0.0,
        "default_rate": defaults / total * 100 if total else 0.0,
        "delinquent": int(pd.to_numeric(df["months_delayed"], errors="coerce").fillna(0).gt(0).sum()) if "months_delayed" in df else 0,
        "outstanding": float(pd.to_numeric(df["bill_amt1"], errors="coerce").clip(lower=0).fillna(0).sum()) if "bill_amt1" in df else 0.0,
    }
