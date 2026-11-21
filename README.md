# CreditLens – Credit Card Portfolio & Risk Analytics

An end-to-end fintech portfolio analytics application using Python, SQLite, Plotly and Streamlit.

## Application features
- Executive portfolio dashboard with actual dataset KPIs
- Portfolio, credit risk, customer, delinquency and transaction analysis
- Global search and credit-limit / repayment filters
- Searchable customer directory and customer profile view
- CSV and Excel upload with preview, missing-value and duplicate checks
- Filtered CSV exports and multi-sheet Excel export
- Professional responsive analytics shell with persistent navigation

## Run (Windows)
1. Extract this ZIP.
2. Ensure Python 3.10+ and internet access are available.
3. Double-click `run_project.bat`.
4. On first run it creates a virtual environment, installs packages, downloads the UCI dataset, processes it, creates a SQLite database and Excel workbook, then launches the dashboard in your browser.

No MySQL server configuration is required. SQLite is used so the project runs out of the box. SQL queries are in `sql/analysis_queries.sql` and can be adapted to MySQL.

## Outputs
- `data/processed/creditlens_customers.csv` – cleaned and feature-enriched data
- `data/processed/creditlens.db` – SQLite database (`credit_customers` table)
- `data/processed/CreditLens_Analysis.xlsx` – multi-sheet Excel analysis
- `data/processed/executive_kpis.csv`
- `data/processed/credit_segment_summary.csv`
- `reports/business_insights.md`
- Streamlit dashboard at the local URL shown in terminal

## Dataset and responsible use
Source: Yeh, I-C. (2009), Default of Credit Card Clients, UCI Machine Learning Repository, dataset ID 350, DOI: https://doi.org/10.24432/C55S3H.
Dataset page: https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients
License: CC BY 4.0. Cite the source and indicate project adaptations.

The dataset contains 30,000 historical customer records from Taiwan, with payment history from 2005 and a next-month default outcome. It is not Synchrony data, not Indian consumer data, and not representative of current lending portfolios. The dashboard is descriptive and educational, not a credit decision system.

## Notes
- `credit_utilization_pct` is calculated as latest bill amount / credit limit * 100 and is a proxy.
- `months_delayed` counts positive repayment status codes across six recorded months.
- The UCI dataset's original currency is New Taiwan dollars (NTD), not INR or USD.
