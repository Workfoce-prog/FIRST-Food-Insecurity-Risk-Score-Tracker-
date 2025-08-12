
import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
from datetime import datetime

# PDF
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="Minnesota Food Insecurity EWS", page_icon="📊", layout="wide")

@st.cache_data
def load_csv(path):
    try:
        return pd.read_csv(path, parse_dates=["date"])
    except Exception:
        try:
            return pd.read_csv(path)
        except Exception:
            return None

def rag_badge(t):
    if t == "Red":
        return ":red_circle: Red"
    if t == "Amber":
        return ":orange_circle: Amber"
    return ":green_circle: Green"

def save_df_as_csv(df, fname="export.csv"):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, file_name=fname, mime="text/csv")

# ---- Sidebar uploads ----
st.sidebar.title("⚙️ Data Sources")
uploaded_latest = st.sidebar.file_uploader("Latest snapshot with RAG (mn_latest_snapshot_with_RAG.csv)", type=["csv"])
uploaded_overview = st.sidebar.file_uploader("Risk overview (current_risk_overview_minnesota.csv)", type=["csv"])
uploaded_metrics_ref = st.sidebar.file_uploader("Metrics reference (metrics_reference_minnesota.csv)", type=["csv"])
st.sidebar.markdown("---")
uploaded_weekly = st.sidebar.file_uploader("Weekly inputs (synthetic_weekly_inputs_minnesota.csv)", type=["csv"])
uploaded_playbook = st.sidebar.file_uploader("RAG playbook (mn_expanded_RAG_action_playbook.csv)", type=["csv"])

# ---- Load data with fallbacks ----
latest = pd.read_csv(uploaded_latest, parse_dates=["date"]) if uploaded_latest else load_csv("data/mn_latest_snapshot_with_RAG.csv")
overview = pd.read_csv(uploaded_overview) if uploaded_overview else load_csv("data/current_risk_overview_minnesota.csv")
metrics_ref = pd.read_csv(uploaded_metrics_ref) if uploaded_metrics_ref else load_csv("data/metrics_reference_minnesota.csv")
weekly = pd.read_csv(uploaded_weekly, parse_dates=["date"]) if uploaded_weekly else load_csv("data/synthetic_weekly_inputs_minnesota.csv")
playbook = pd.read_csv(uploaded_playbook) if uploaded_playbook else load_csv("data/mn_expanded_RAG_action_playbook.csv")

st.title("Minnesota Food Insecurity Early Warning System")
st.caption("State-aligned variables, county-level RAG alerts, and action playbooks.")

# ---- KPIs ----
kpi_cols = st.columns(4)
as_of = None
if latest is not None and "date" in latest.columns:
    as_of = str(pd.to_datetime(latest["date"]).max().date()) if not latest.empty else None
kpi_cols[0].metric("As of", as_of or "—")
if overview is not None and not overview.empty:
    red_ct = (overview["RAG_Status"] == "Red").sum()
    amber_ct = (overview["RAG_Status"] == "Amber").sum()
    green_ct = (overview["RAG_Status"] == "Green").sum()
    kpi_cols[1].metric("Counties in Red", int(red_ct))
    kpi_cols[2].metric("Counties in Amber", int(amber_ct))
    kpi_cols[3].metric("Counties in Green", int(green_ct))
else:
    for i in range(1,4):
        kpi_cols[i].metric(["Red","Amber","Green"][i-1], "—")

st.markdown("---")

# ---- Tabs ----
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📍 Current Risk (RAG)", "📈 Trends", "🧭 Action Playbook", "ℹ️ Metrics Reference", "🖨️ PDF Export"])

with tab1:
    st.subheader("County Risk Overview — 8-week Horizon")
    if overview is None or overview.empty:
        st.info("Upload or place `current_risk_overview_minnesota.csv` into `data/` to view this table.")
    else:
        df = overview.copy()
        df["RAG_Badge"] = df["RAG_Status"].apply(rag_badge)
        st.dataframe(df[["County","As_Of_Date","Prob_Spike_8w","RAG_Status","RAG_Badge","Lead_Time_Weeks"]], use_container_width=True)
        save_df_as_csv(df, "current_risk_overview_minnesota.csv")

        # Chart for PDF capture
        fig1, ax1 = plt.subplots()
        ax1.bar(df["County"], df["Prob_Spike_8w"])
        ax1.set_ylim(0,1)
        ax1.set_ylabel("Probability")
        ax1.set_title("Predicted Probability of Spike in 8 Weeks — Counties")
        st.pyplot(fig1)

with tab2:
    st.subheader("Weekly Trends — Food Shelf Visits & Key Drivers")
    county = None
    if latest is not None and "county" in latest.columns and not latest.empty:
        county = st.selectbox("Select County", sorted(latest["county"].unique()))
    elif weekly is not None and "county" in weekly.columns:
        county = st.selectbox("Select County", sorted(weekly["county"].unique()))
    else:
        st.info("Upload or place `synthetic_weekly_inputs_minnesota.csv` into `data/` to plot trends.")

    fig2 = None
    fig3 = None
    if county and weekly is not None and "date" in weekly.columns:
        w = weekly[weekly["county"]==county].sort_values("date")
        c1, c2 = st.columns(2)

        with c1:
            fig2, ax2 = plt.subplots()
            ax2.plot(w["date"], w["Food_Shelf_Visits"])
            ax2.set_title(f"Food Shelf Visits — {county}")
            ax2.set_xlabel("Date"); ax2.set_ylabel("Weekly Visits")
            st.pyplot(fig2)

        with c2:
            fig3, ax3 = plt.subplots()
            ax3.plot(w["date"], w["SNAP_Applications"], label="SNAP_Applications")
            ax3.plot(w["date"], w["Unemployment_Claims"], label="Unemployment_Claims")
            ax3.legend()
            ax3.set_title(f"Lead Indicators — {county}")
            ax3.set_xlabel("Date"); ax3.set_ylabel("Weekly Count / Index Units")
            st.pyplot(fig3)

with tab3:
    st.subheader("RAG Action Playbook (MN-aligned)")
    if playbook is None or playbook.empty:
        st.info("Upload or place `mn_expanded_RAG_action_playbook.csv` into `data/` to view recommendations.")
    else:
        st.dataframe(playbook, use_container_width=True)
        save_df_as_csv(playbook, "mn_expanded_RAG_action_playbook.csv")

with tab4:
    st.subheader("Metrics Reference")
    if metrics_ref is None or metrics_ref.empty:
        st.info("Upload or place `metrics_reference_minnesota.csv` into `data/` to view the data dictionary.")
    else:
        st.dataframe(metrics_ref, use_container_width=True)
        save_df_as_csv(metrics_ref, "metrics_reference_minnesota.csv")

with tab5:
    st.subheader("One-click PDF Export")
    st.caption("Creates a 1–2 page brief with current RAG, top metrics, and charts.")
    county_for_pdf = None
    if weekly is not None and "county" in weekly.columns:
        county_for_pdf = st.selectbox("County for trend chart in PDF", sorted(weekly["county"].unique()))
    include_playbook = st.checkbox("Include RAG action playbook", value=True)

    if st.button("Generate PDF"):
        # Build PDF in memory
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=LETTER)
        width, height = LETTER
        margin = 0.75*inch
        y = height - margin

        # Header
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, y, "Minnesota Food Insecurity Early Warning System — Executive Summary")
        y -= 16
        c.setFont("Helvetica", 10)
        c.drawString(margin, y, f"As of: {as_of or '—'}    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        y -= 20

        # RAG counts
        if overview is not None and not overview.empty:
            red_ct = int((overview['RAG_Status']=='Red').sum())
            amber_ct = int((overview['RAG_Status']=='Amber').sum())
            green_ct = int((overview['RAG_Status']=='Green').sum())
            c.setFont("Helvetica-Bold", 11)
            c.drawString(margin, y, "Current RAG Status (Counties)")
            y -= 14
            c.setFont("Helvetica", 10)
            c.drawString(margin, y, f"Red: {red_ct}   Amber: {amber_ct}   Green: {green_ct}")
            y -= 18

        # Insert probabilities bar chart from Tab 1
        try:
            img_buf = io.BytesIO()
            fig_pdf, ax_pdf = plt.subplots()
            df_tmp = overview.copy().sort_values("Prob_Spike_8w", ascending=False).head(10)
            ax_pdf.bar(df_tmp["County"], df_tmp["Prob_Spike_8w"])
            ax_pdf.set_ylim(0,1)
            ax_pdf.set_title("Predicted Probability of Spike (Top 10 Counties)")
            ax_pdf.set_ylabel("Probability")
            fig_pdf.tight_layout()
            fig_pdf.savefig(img_buf, format="png", dpi=150)
            plt.close(fig_pdf)
            img_buf.seek(0)
            img = ImageReader(img_buf)
            img_w = width - 2*margin
            img_h = img_w * 0.45
            c.drawImage(img, margin, y - img_h, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
            y -= (img_h + 10)
        except Exception as e:
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(margin, y, f"(Chart unavailable: {e})")
            y -= 12

        # County trend chart
        if county_for_pdf and weekly is not None and "date" in weekly.columns:
            try:
                wpdf = weekly[weekly["county"]==county_for_pdf].sort_values("date")
                img_buf2 = io.BytesIO()
                fig_pdf2, ax_pdf2 = plt.subplots()
                ax_pdf2.plot(wpdf["date"], wpdf["Food_Shelf_Visits"])
                ax_pdf2.set_title(f"Food Shelf Visits — {county_for_pdf}")
                ax_pdf2.set_xlabel("Date"); ax_pdf2.set_ylabel("Weekly Visits")
                fig_pdf2.tight_layout()
                fig_pdf2.savefig(img_buf2, format="png", dpi=150)
                plt.close(fig_pdf2)
                img_buf2.seek(0)
                img2 = ImageReader(img_buf2)
                img_w2 = width - 2*margin
                img_h2 = img_w2 * 0.35
                if y - img_h2 < margin:
                    c.showPage(); y = height - margin
                c.drawImage(img2, margin, y - img_h2, width=img_w2, height=img_h2, preserveAspectRatio=True, mask='auto')
                y -= (img_h2 + 10)
            except Exception as e:
                c.setFont("Helvetica-Oblique", 9)
                c.drawString(margin, y, f"(Trend chart unavailable: {e})")
                y -= 12

        # Optional playbook summary
        if include_playbook and playbook is not None and not playbook.empty:
            if y < 1.5*inch:
                c.showPage(); y = height - margin
            c.setFont("Helvetica-Bold", 11)
            c.drawString(margin, y, "RAG Action Playbook — Summary")
            y -= 14
            c.setFont("Helvetica", 9)
            # Show up to first 6 rows compactly
            cols_show = ["County","RAG_Status","Lead Agency","Governance Cadence","Outreach Focus"]
            pb = playbook.copy()
            for _, row in pb.head(6).iterrows():
                text = f"- {row.get('County','?')}: {row.get('RAG_Status','?')}; Lead: {row.get('Lead Agency','?')}; Cadence: {row.get('Governance Cadence','?')}; Outreach: {row.get('Outreach Focus','?')}"
                c.drawString(margin, y, text[:115])
                y -= 12
                if y < margin:
                    c.showPage(); y = height - margin

        c.showPage()
        c.save()
        buffer.seek(0)
        st.download_button("Download PDF", buffer, file_name="MN_EWS_Executive_Summary.pdf", mime="application/pdf")

st.markdown("---")
st.caption("© {} Minnesota Food Insecurity EWS — Demo build".format(pd.Timestamp.today().year))
