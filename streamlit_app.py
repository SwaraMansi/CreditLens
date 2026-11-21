import runpy
import sys
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent
PROCESSED_CSV = ROOT / "data" / "processed" / "creditlens_customers.csv"


if not PROCESSED_CSV.exists():
    with st.spinner("Preparing the CreditLens dataset..."):
        sys.path.insert(0, str(ROOT / "src"))
        from pipeline import main as run_pipeline

        run_pipeline()

runpy.run_path(str(ROOT / "app.py"), run_name="__main__")
