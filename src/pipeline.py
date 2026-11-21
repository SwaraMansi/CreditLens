from pathlib import Path
import sys, urllib.request, zipfile, io, warnings
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
for p in (RAW, OUT, REPORTS):
    p.mkdir(parents=True, exist_ok=True)

URLS = [
 "https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip",
 "https://archive.ics.uci.edu/ml/machine-learning-databases/00350/default%20of%20credit%20card%20clients.xls"
]
XLS = RAW / "default_of_credit_card_clients.xls"

def acquire():
    if XLS.exists():
        print(f"Using existing dataset: {XLS}")
        return
    print("Downloading the public UCI credit default dataset...")
    last = None
    for url in URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CreditLens-Analytics-Project/1.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                content = r.read()
            if url.endswith(".zip") or content[:2] == b"PK":
                with zipfile.ZipFile(io.BytesIO(content)) as z:
                    name = next(n for n in z.namelist() if n.lower().endswith(".xls"))
                    XLS.write_bytes(z.read(name))
            else:
                XLS.write_bytes(content)
            print("Dataset downloaded.")
            return
        except Exception as e:
            last = e
            print(f"Download attempt failed: {e}")
    raise RuntimeError(
        "Could not download the UCI dataset. Check your internet connection and rerun. "
        f"Last error: {last}"
    )

def load_data():
    acquire()
    df = pd.read_excel(XLS, sheet_name="Data", header=1)
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    expected = "default_payment_next_month"
    if expected not in df.columns:
        raise ValueError(f"Unexpected dataset columns. Found: {df.columns.tolist()}")
    df = df.drop_duplicates().copy()
    df["credit_utilization_pct"] = np.where(
        df["limit_bal"] > 0,
        (df["bill_amt1"].clip(lower=0) / df["limit_bal"]) * 100,
        np.nan
    )
    df["credit_utilization_pct"] = df["credit_utilization_pct"].clip(upper=500)
    df["total_bill_6m"] = df[[f"bill_amt{i}" for i in range(1,7)]].sum(axis=1)
    df["total_payment_6m"] = df[[f"pay_amt{i}" for i in range(1,7)]].sum(axis=1)
    df["avg_bill_6m"] = df[[f"bill_amt{i}" for i in range(1,7)]].mean(axis=1)
    df["avg_payment_6m"] = df[[f"pay_amt{i}" for i in range(1,7)]].mean(axis=1)
    pay_cols = ["pay_0","pay_2","pay_3","pay_4","pay_5","pay_6"]
    df["months_delayed"] = (df[pay_cols] > 0).sum(axis=1)
    df["repayment_segment"] = np.select(
        [df["months_delayed"] == 0, df["months_delayed"] <= 2],
        ["No recorded delay", "Occasional delay"],
        default="Frequent delay"
    )
    df["credit_limit_segment"] = pd.cut(
        df["limit_bal"],
        bins=[-np.inf, 50000, 150000, 300000, np.inf],
        labels=["Below 50K", "50K–150K", "150K–300K", "Above 300K"]
    ).astype(str)
    df["default_flag"] = df[expected].astype(int)
    return df

def main():
    df = load_data()
    clean_path = OUT / "creditlens_customers.csv"
    df.to_csv(clean_path, index=False)
    engine = create_engine(f"sqlite:///{(OUT / 'creditlens.db').as_posix()}")
    df.to_sql("credit_customers", engine, if_exists="replace", index=False)
    # Aggregated, dashboard-ready tables
    segment = df.groupby("credit_limit_segment", observed=False).agg(
        customers=("id","count"), default_rate=("default_flag","mean"),
        avg_credit_limit=("limit_bal","mean"),
        avg_utilization=("credit_utilization_pct","mean")
    ).reset_index()
    segment.to_csv(OUT / "credit_segment_summary.csv", index=False)
    repayment = df.groupby("repayment_segment").agg(
        customers=("id","count"), default_rate=("default_flag","mean"),
        avg_bill=("avg_bill_6m","mean"), avg_payment=("avg_payment_6m","mean")
    ).reset_index()
    repayment.to_csv(OUT / "repayment_summary.csv", index=False)
    summary = pd.DataFrame({
        "metric": ["Total customers","Defaulted customers","Default rate (%)",
                   "Average credit limit","Average utilization (%)",
                   "Total 6-month bill amount","Total 6-month payment amount"],
        "value": [len(df), int(df.default_flag.sum()), round(df.default_flag.mean()*100,2),
                  round(df.limit_bal.mean(),2), round(df.credit_utilization_pct.mean(),2),
                  round(df.total_bill_6m.sum(),2), round(df.total_payment_6m.sum(),2)]
    })
    summary.to_csv(OUT / "executive_kpis.csv", index=False)
    with pd.ExcelWriter(OUT / "CreditLens_Analysis.xlsx", engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Executive KPIs", index=False)
        segment.to_excel(writer, sheet_name="Credit Segments", index=False)
        repayment.to_excel(writer, sheet_name="Repayment Analysis", index=False)
        df.head(1000).to_excel(writer, sheet_name="Customer Sample", index=False)
    report = f"""# CreditLens – Automated Findings

## Dataset
- Records analyzed: {len(df):,}
- Defaulted customers: {int(df.default_flag.sum()):,}
- Observed default rate: {df.default_flag.mean()*100:.2f}%
- Average credit limit: {df.limit_bal.mean():,.2f} NT dollars
- Average calculated utilization: {df.credit_utilization_pct.mean():.2f}%

## Segment analysis
{segment.to_markdown(index=False)}

## Repayment analysis
{repayment.to_markdown(index=False)}

## Interpretation notes
- These are descriptive associations, not causal findings.
- The dataset is historical Taiwan credit-card research data from 2005, not current Indian or Synchrony customer data.
- The utilization calculation uses latest bill amount divided by credit limit; it is a proxy and can exceed 100%.
- Delinquency is approximated from positive repayment-status codes in the six recorded months.
"""
    (REPORTS / "business_insights.md").write_text(report, encoding="utf-8")
    print("\nSUCCESS: CreditLens data pipeline completed.")
    print(f"Rows: {len(df):,} | Columns: {len(df.columns)}")
    print(f"Default rate: {df.default_flag.mean()*100:.2f}%")
    print(f"SQLite DB: {OUT / 'creditlens.db'}")
    print(f"Excel report: {OUT / 'CreditLens_Analysis.xlsx'}")
    print(f"Clean CSV: {clean_path}")

if __name__ == "__main__":
    main()
