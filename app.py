import io
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from data_service import filter_customers, kpis, load_customers, prepare_dataframe
from ui_components import chart_theme, inject_css, kpi_card


st.set_page_config(
    page_title="CreditLens",
    page_icon="CL",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()


NAV_ITEMS = [
    "Overview",
    "Portfolio Analytics",
    "Credit Risk Analysis",
    "Customer Insights",
    "Delinquency Analysis",
    "Transaction Analytics",
    "Data Management",
    "Reports & Exports",
    "Settings",
]


@st.cache_data(show_spinner=False)
def cached_load():
    return load_customers()


if "active_df" not in st.session_state:
    try:
        st.session_state.active_df = cached_load()
    except Exception as exc:
        st.error(f"Unable to load the processed dataset: {exc}")
        st.stop()


df = st.session_state.active_df

with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-mark">CL</div>'
        '<div><div class="brand-name">CreditLens</div>'
        '<div class="brand-sub">Risk intelligence</div></div></div>',
        unsafe_allow_html=True,
    )
    active = st.radio("Navigation", NAV_ITEMS, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**Portfolio filters**")
    limit_options = sorted(df["credit_limit_segment"].dropna().unique().tolist()) if "credit_limit_segment" in df else []
    selected_limits = st.multiselect("Credit limit", limit_options, default=limit_options)
    repayment_options = sorted(df["repayment_segment"].dropna().unique().tolist()) if "repayment_segment" in df else []
    selected_repayments = st.multiselect("Repayment behavior", repayment_options, default=repayment_options)
    st.caption("Data source: UCI historical dataset")


if "global_search" not in st.session_state:
    st.session_state.global_search = ""

top_left, top_right = st.columns([4.2, 1.8], vertical_alignment="bottom")
with top_left:
    st.markdown(
        f'<div class="breadcrumb">Analytics / {active}</div><div class="page-title">{active}</div>',
        unsafe_allow_html=True,
    )
with top_right:
    search = st.text_input("Global search", value=st.session_state.global_search, placeholder="Search customers")
    st.session_state.global_search = search

filtered = filter_customers(
    df,
    credit_segments=selected_limits,
    repayment_segments=selected_repayments,
    search=search,
)
metrics = kpis(filtered)


def no_data():
    st.warning("No records match the current filters.")


def overview_page():
    if filtered.empty:
        no_data()
        return

    st.markdown(
        '<div class="kpi-grid">'
        f'{kpi_card("Total customers", f"{metrics["customers"]:,}", "Records in current view")}'
        f'{kpi_card("Total credit exposure", f"NT$ {metrics["exposure"]/1e6:.2f}M", "Sum of credit limits")}'
        f'{kpi_card("Average credit limit", f"NT$ {metrics["avg_limit"]:,.0f}", "Mean approved limit")}'
        f'{kpi_card("Default rate", f"{metrics["default_rate"]:.2f}%", "Defaults / total customers")}'
        f'{kpi_card("Delinquent customers", f"{metrics["delinquent"]:,}", "One or more positive delay codes")}'
        f'{kpi_card("Outstanding balance", f"NT$ {metrics["outstanding"]/1e6:.2f}M", "Latest positive bill amount")}'
        '</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.35, 1], gap="medium")
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Default rate by credit limit</div>', unsafe_allow_html=True)
        seg = filtered.groupby("credit_limit_segment", observed=False).agg(
            customers=("id", "count"),
            default_rate=("default_flag", "mean"),
        ).reset_index()
        seg["default_rate"] *= 100
        fig = px.bar(seg, x="credit_limit_segment", y="default_rate", text="default_rate",
                     color="credit_limit_segment", labels={"default_rate": "Default rate (%)", "credit_limit_segment": "Segment"})
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(chart_theme(fig, 300), use_container_width=True, config={"displayModeBar": True, "responsive": True})
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Default distribution</div>', unsafe_allow_html=True)
        dist = filtered["default_flag"].value_counts().rename_axis("Outcome").reset_index(name="Customers")
        dist["Outcome"] = dist["Outcome"].map({0: "Non-default", 1: "Default"})
        fig = px.pie(dist, names="Outcome", values="Customers", hole=0.72,
                     color="Outcome", color_discrete_map={"Non-default": "#2E90FA", "Default": "#F04438"})
        fig.update_traces(textposition="outside")
        st.plotly_chart(chart_theme(fig, 300), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Credit utilization distribution</div>', unsafe_allow_html=True)
        util = filtered["credit_utilization_pct"].dropna().clip(lower=0, upper=300)
        fig = px.histogram(util, nbins=35, labels={"value": "Latest bill / credit limit (%)", "count": "Customers"})
        fig.update_traces(marker_color="#2E90FA", opacity=0.88)
        st.plotly_chart(chart_theme(fig, 300), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">6-month repayment trend</div>', unsafe_allow_html=True)
        trend = []
        for i in range(1, 7):
            bill = filtered[f"bill_amt{i}"].mean() if f"bill_amt{i}" in filtered else 0
            payment = filtered[f"pay_amt{i}"].mean() if f"pay_amt{i}" in filtered else 0
            trend.append({"Period": f"M{i}", "Average bill": bill, "Average payment": payment})
        trend_df = pd.DataFrame(trend).melt("Period", var_name="Measure", value_name="NT$")
        fig = px.line(trend_df, x="Period", y="NT$", color="Measure", markers=True)
        st.plotly_chart(chart_theme(fig, 300), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Customer segmentation</div>', unsafe_allow_html=True)
        seg = filtered["credit_limit_segment"].value_counts().rename_axis("Segment").reset_index(name="Customers")
        fig = px.bar(seg, x="Customers", y="Segment", orientation="h", color="Customers",
                     color_continuous_scale=["#D1E9FF", "#175CD3"])
        st.plotly_chart(chart_theme(fig, 280), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Delinquency distribution</div>', unsafe_allow_html=True)
        d = filtered["months_delayed"].value_counts().sort_index().rename_axis("Delayed months").reset_index(name="Customers")
        fig = px.bar(d, x="Delayed months", y="Customers", color_discrete_sequence=["#2E7D6E"])
        st.plotly_chart(chart_theme(fig, 280), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


def portfolio_page():
    if filtered.empty:
        no_data()
        return
    c1, c2 = st.columns([1.4, 1], gap="medium")
    with c1:
        st.markdown('<div class="panel"><div class="panel-title">Exposure by credit limit segment</div>', unsafe_allow_html=True)
        exposure = filtered.groupby("credit_limit_segment", observed=False)["limit_bal"].sum().reset_index(name="Exposure")
        fig = px.bar(exposure, x="credit_limit_segment", y="Exposure",
                     labels={"credit_limit_segment": "Segment", "Exposure": "Credit exposure (NT$)"})
        st.plotly_chart(chart_theme(fig, 330), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="panel"><div class="panel-title">Portfolio composition</div>', unsafe_allow_html=True)
        comp = filtered["repayment_segment"].value_counts().rename_axis("Segment").reset_index(name="Customers")
        fig = px.pie(comp, names="Segment", values="Customers", hole=0.55)
        st.plotly_chart(chart_theme(fig, 330), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="panel"><div class="panel-title">Credit limit distribution</div>', unsafe_allow_html=True)
    fig = px.histogram(filtered, x="limit_bal", nbins=40, labels={"limit_bal": "Credit limit (NT$)"}, color_discrete_sequence=["#244A68"])
    st.plotly_chart(chart_theme(fig, 300), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def risk_page():
    if filtered.empty:
        no_data()
        return
    st.info("This is descriptive portfolio analysis, not an actual lending decision or validated risk model.")
    tabs = st.tabs(["Default analysis", "Education", "Age", "Utilization"])
    with tabs[0]:
        left, right = st.columns(2)
        with left:
            a = filtered.groupby("credit_limit_segment", observed=False)["default_flag"].mean().mul(100).reset_index(name="Default rate")
            fig = px.bar(a, x="credit_limit_segment", y="Default rate", color="Default rate",
                         color_continuous_scale=["#D1E9FF", "#F04438"])
            st.plotly_chart(chart_theme(fig, 300), use_container_width=True)
        with right:
            a = filtered.groupby("repayment_segment")["default_flag"].mean().mul(100).reset_index(name="Default rate")
            fig = px.bar(a, x="repayment_segment", y="Default rate", color="repayment_segment")
            st.plotly_chart(chart_theme(fig, 300), use_container_width=True)
    with tabs[1]:
        if "education" in filtered:
            a = filtered.groupby("education")["default_flag"].agg(["count", "mean"]).reset_index()
            a["default_rate"] = a["mean"] * 100
            fig = px.bar(a, x="education", y="default_rate", hover_data=["count"])
            st.plotly_chart(chart_theme(fig, 320), use_container_width=True)
        else:
            st.caption("Education field is not available in this dataset.")
    with tabs[2]:
        if "age_group" in filtered:
            a = filtered.groupby("age_group", observed=False)["default_flag"].agg(["count", "mean"]).reset_index()
            a["default_rate"] = a["mean"] * 100
            fig = px.bar(a, x="age_group", y="default_rate", hover_data=["count"])
            st.plotly_chart(chart_theme(fig, 320), use_container_width=True)
    with tabs[3]:
        fig = px.histogram(filtered, x="credit_utilization_pct", color="default_flag",
                           barmode="overlay", nbins=35,
                           color_discrete_map={0: "#2E90FA", 1: "#F04438"},
                           labels={"credit_utilization_pct": "Utilization proxy (%)", "default_flag": "Default"})
        st.plotly_chart(chart_theme(fig, 320), use_container_width=True)


def customer_page():
    if filtered.empty:
        no_data()
        return
    c1, c2 = st.columns([1.8, 1], gap="medium")
    with c1:
        st.markdown('<div class="panel"><div class="panel-title">Customer directory</div>', unsafe_allow_html=True)
        preferred = ["id", "age", "sex", "education", "limit_bal", "credit_limit_segment",
                     "repayment_segment", "months_delayed", "credit_utilization_pct",
                     "avg_bill_6m", "avg_payment_6m", "default_flag"]
        cols = [c for c in preferred if c in filtered]
        table = filtered[cols].copy()
        st.dataframe(table, use_container_width=True, height=440)
        st.download_button("Download filtered customers",
                           table.to_csv(index=False).encode("utf-8"),
                           "creditlens_customers_filtered.csv", "text/csv")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="panel"><div class="panel-title">Customer profile</div>', unsafe_allow_html=True)
        ids = filtered["id"].tolist() if "id" in filtered else filtered.index.tolist()
        if ids:
            customer_id = st.selectbox("Customer ID", ids[:1000])
            row = filtered[filtered["id"] == customer_id].iloc[0] if "id" in filtered else filtered.loc[customer_id]
            for label, key, fmt in [
                ("Age", "age", "{:.0f}"),
                ("Credit limit", "limit_bal", "NT$ {:,.0f}"),
                ("Utilization", "credit_utilization_pct", "{:.1f}%"),
                ("Delayed months", "months_delayed", "{:.0f}"),
                ("Average 6m bill", "avg_bill_6m", "NT$ {:,.0f}"),
                ("Average 6m payment", "avg_payment_6m", "NT$ {:,.0f}"),
            ]:
                if key in row:
                    st.markdown(f'<div class="kpi-note">{label}</div><div style="font-size:17px;font-weight:700;color:#344054;margin-bottom:8px">{fmt.format(row[key])}</div>', unsafe_allow_html=True)
            outcome = "Default" if int(row["default_flag"]) == 1 else "Non-default"
            st.markdown(f'<div class="kpi-note">Observed outcome</div><div style="font-size:17px;font-weight:700;color:#344054">{outcome}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def delinquency_page():
    if filtered.empty:
        no_data()
        return
    c1, c2 = st.columns(2)
    with c1:
        d = filtered["months_delayed"].value_counts().sort_index().rename_axis("Delayed months").reset_index(name="Customers")
        fig = px.bar(d, x="Delayed months", y="Customers")
        st.plotly_chart(chart_theme(fig, 320), use_container_width=True)
    with c2:
        d = filtered.groupby("months_delayed")["default_flag"].mean().mul(100).reset_index(name="Default rate")
        fig = px.line(d, x="months_delayed", y="Default rate", markers=True)
        st.plotly_chart(chart_theme(fig, 320), use_container_width=True)
    st.markdown('<div class="panel"><div class="panel-title">Methodology</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="metric-caption">Delinquency is approximated by counting repayment-status values greater than zero across '
        '<code>PAY_0, PAY_2, PAY_3, PAY_4, PAY_5,</code> and <code>PAY_6</code>. It is a descriptive proxy, not an official lender status.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def transaction_page():
    if filtered.empty:
        no_data()
        return
    rows = []
    for i in range(1, 7):
        rows.append({
            "Period": f"Month {i}",
            "Average bill": filtered[f"bill_amt{i}"].mean(),
            "Average payment": filtered[f"pay_amt{i}"].mean(),
        })
    trans = pd.DataFrame(rows)
    left, right = st.columns([1.4, 1])
    with left:
        fig = px.bar(trans, x="Period", y=["Average bill", "Average payment"], barmode="group")
        st.plotly_chart(chart_theme(fig, 340), use_container_width=True)
    with right:
        trans["Payment-to-bill"] = trans["Average payment"] / trans["Average bill"].where(trans["Average bill"] != 0)
        fig = px.line(trans, x="Period", y="Payment-to-bill", markers=True)
        fig.update_layout(yaxis_tickformat=".0%")
        st.plotly_chart(chart_theme(fig, 340), use_container_width=True)


def data_management_page():
    st.markdown('<div class="panel"><div class="panel-title">Upload customer dataset</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Drag and drop a CSV or Excel file", type=["csv", "xlsx", "xls"])
    if uploaded:
        try:
            if uploaded.name.lower().endswith(".csv"):
                preview = pd.read_csv(uploaded)
            else:
                preview = pd.read_excel(uploaded, sheet_name="Data", header=1)
                preview.columns = [str(c).strip().lower().replace(" ", "_") for c in preview.columns]
        except Exception:
            uploaded.seek(0)
            try:
                preview = pd.read_excel(uploaded)
            except Exception as exc:
                st.error(f"Could not read the uploaded file: {exc}")
                preview = None
        if preview is not None:
            preview = prepare_dataframe(preview)
            st.success(f"{uploaded.name} loaded — {len(preview):,} rows and {len(preview.columns)} columns")
            c1, c2, c3 = st.columns(3)
            c1.metric("Missing cells", int(preview.isna().sum().sum()))
            c2.metric("Duplicate rows", int(preview.duplicated().sum()))
            c3.metric("Columns", len(preview.columns))
            st.markdown("**Data preview**")
            st.dataframe(preview.head(20), use_container_width=True)
            missing = preview.isna().sum()
            missing = missing[missing > 0].sort_values(ascending=False)
            if not missing.empty:
                st.warning("Missing values detected")
                st.dataframe(missing.rename("Missing values").to_frame(), use_container_width=True)
            else:
                st.success("No missing values detected")
            if st.button("Use uploaded dataset", type="primary"):
                st.session_state.active_df = preview
                st.success("Uploaded dataset is now active.")
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("Restore UCI default dataset"):
        st.session_state.active_df = cached_load()
        st.success("The default UCI dataset has been restored.")
        st.rerun()


def reports_page():
    st.markdown('<div class="panel"><div class="panel-title">Exports</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("Filtered CSV", filtered.to_csv(index=False).encode("utf-8"),
                           "creditlens_filtered.csv", "text/csv", use_container_width=True)
    with c2:
        summary = pd.DataFrame([kpis(filtered)]).T.reset_index()
        summary.columns = ["Metric", "Value"]
        st.download_button("Summary CSV", summary.to_csv(index=False).encode("utf-8"),
                           "creditlens_summary.csv", "text/csv", use_container_width=True)
    with c3:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            summary.to_excel(writer, sheet_name="Executive Summary", index=False)
            filtered.to_excel(writer, sheet_name="Filtered Customers", index=False)
        st.download_button("Excel workbook", output.getvalue(),
                           "CreditLens_Export.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="panel" style="margin-top:12px"><div class="panel-title">Automated findings</div>', unsafe_allow_html=True)
    m = kpis(filtered)
    st.markdown(
        f"- **{m['customers']:,}** records in the current filtered view  \n"
        f"- Observed default rate: **{m['default_rate']:.2f}%**  \n"
        f"- Average credit limit: **NT$ {m['avg_limit']:,.0f}**  \n"
        f"- Delinquent customers: **{m['delinquent']:,}**  \n"
        "- These are descriptive associations from a historical 2005 Taiwan dataset."
    )
    st.markdown("</div>", unsafe_allow_html=True)


def settings_page():
    st.markdown('<div class="panel"><div class="panel-title">Workspace settings</div>', unsafe_allow_html=True)
    st.toggle("Compact table density", value=False)
    st.toggle("Show methodology notes", value=True)
    st.selectbox("Currency display", ["NT$ (dataset currency)"])
    st.selectbox("Number format", ["Auto"])
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("CreditLens is an educational analytics application. It does not provide lending decisions.")


PAGES = {
    "Overview": overview_page,
    "Portfolio Analytics": portfolio_page,
    "Credit Risk Analysis": risk_page,
    "Customer Insights": customer_page,
    "Delinquency Analysis": delinquency_page,
    "Transaction Analytics": transaction_page,
    "Data Management": data_management_page,
    "Reports & Exports": reports_page,
    "Settings": settings_page,
}

PAGES[active]()
