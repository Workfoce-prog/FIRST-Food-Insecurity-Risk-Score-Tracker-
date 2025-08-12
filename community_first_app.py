
import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
from datetime import datetime

# PDF export
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors

st.set_page_config(page_title="Minnesota Food Insecurity EWS", page_icon="📊", layout="wide")

# ----------------- Branding -----------------
PRIMARY = "#0B5FFF"   # DHS-style blue accent
ACCENT  = "#0E7C3A"   # MDE/education green accent
BORDER  = "#E5E7EB"   # light gray

def header_brand():
    c1, c2, c3 = st.columns([1,6,1])
    with c1:
        st.image("data/logo_dhs.png", caption="DHS", use_container_width=True)
    with c2:
        st.markdown(f"<h2 style='margin-bottom:0; color:{PRIMARY};'>Minnesota Food Insecurity Early Warning System</h2>", unsafe_allow_html=True)
        st.caption("MN-aligned variables, county RAG alerts, action playbooks, and data dictionary")
    with c3:
        st.image("data/logo_mde.png", caption="MDE", use_container_width=True)
    st.markdown(f"<hr style='border:1px solid {BORDER}; margin-top:0;'>", unsafe_allow_html=True)

# --------------- Helpers --------------------
@st.cache_data
def load_csv(path, parse_dates=None):
    try:
        return pd.read_csv(path, parse_dates=parse_dates) if parse_dates else pd.read_csv(path)
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

# Sidebar uploads
st.sidebar.title("⚙️ Data Sources")
uploaded_latest = st.sidebar.file_uploader("Latest snapshot with RAG (mn_latest_snapshot_with_RAG.csv)", type=["csv"])
uploaded_overview = st.sidebar.file_uploader("Risk overview (current_risk_overview_minnesota.csv)", type=["csv"])
uploaded_metrics_ref = st.sidebar.file_uploader("Metrics reference (metrics_reference_minnesota.csv)", type=["csv"])
st.sidebar.markdown("---")
uploaded_weekly = st.sidebar.file_uploader("Weekly inputs (synthetic_weekly_inputs_minnesota.csv)", type=["csv"])
uploaded_playbook = st.sidebar.file_uploader("RAG playbook (mn_expanded_RAG_action_playbook.csv)", type=["csv"])

# Load data (with fallbacks)
latest = pd.read_csv(uploaded_latest, parse_dates=["date"]) if uploaded_latest else load_csv("data/mn_latest_snapshot_with_RAG.csv", parse_dates=["date"])
overview = pd.read_csv(uploaded_overview) if uploaded_overview else load_csv("data/current_risk_overview_minnesota.csv")
metrics_ref = pd.read_csv(uploaded_metrics_ref) if uploaded_metrics_ref else load_csv("data/metrics_reference_minnesota.csv")
weekly = pd.read_csv(uploaded_weekly, parse_dates=["date"]) if uploaded_weekly else load_csv("data/synthetic_weekly_inputs_minnesota.csv", parse_dates=["date"])
playbook = pd.read_csv(uploaded_playbook) if uploaded_playbook else load_csv("data/mn_expanded_RAG_action_playbook.csv")

# Header
header_brand()

# KPIs
kpi_cols = st.columns(4)
as_of = None
if latest is not None and "date" in latest.columns and not latest.empty:
    try:
        as_of = str(pd.to_datetime(latest["date"]).max().date())
    except Exception:
        as_of = None
kpi_cols[0].metric("As of", as_of or "—")
if overview is not None and not overview.empty:
    red_ct = int((overview["RAG_Status"] == "Red").sum())
    amber_ct = int((overview["RAG_Status"] == "Amber").sum())
    green_ct = int((overview["RAG_Status"] == "Green").sum())
    kpi_cols[1].metric("Counties in Red", red_ct)
    kpi_cols[2].metric("Counties in Amber", amber_ct)
    kpi_cols[3].metric("Counties in Green", green_ct)
else:
    for i, label in enumerate(["Red","Amber","Green"], start=1):
        kpi_cols[i].metric(label, "—")

st.markdown(f"<hr style='border:1px solid {BORDER};'>", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📍 Current Risk (RAG)", "📈 Trends", "🧭 Action Playbook", "ℹ️ Metrics Reference", "🖨️ PDF Export"])

with tab1:
    st.subheader("County Risk Overview — 8-week Horizon")
    if overview is None or overview.empty:
        st.info("Upload or place `current_risk_overview_minnesota.csv` into `data/` to view this table.")
    else:
        df = overview.copy()
        if "RAG_Status" in df.columns:
            df["RAG_Badge"] = df["RAG_Status"].apply(rag_badge)
        st.dataframe(df, use_container_width=True)
        save_df_as_csv(df, "current_risk_overview_minnesota.csv")

        # bar chart
        if "County" in df.columns and "Prob_Spike_8w" in df.columns:
            fig, ax = plt.subplots()
            ax.bar(df["County"], df["Prob_Spike_8w"])
            ax.set_ylim(0,1)
            ax.set_ylabel("Probability")
            ax.set_title("Predicted Probability of Spike in 8 Weeks — Counties")
            st.pyplot(fig)

with tab2:
    st.subheader("Weekly Trends — Food Shelf Visits & Lead Indicators")
    county = None
    if weekly is not None and "county" in weekly.columns:
        try:
            county = st.selectbox("Select County", sorted(weekly["county"].dropna().unique()))
        except Exception:
            county = None

    if county and weekly is not None and "date" in weekly.columns:
        w = weekly[weekly["county"]==county].sort_values("date")
        c1, c2 = st.columns(2)
        with c1:
            fig1, ax1 = plt.subplots()
            ax1.plot(w["date"], w.get("Food_Shelf_Visits", []))
            ax1.set_title(f"Food Shelf Visits — {county}")
            ax1.set_xlabel("Date"); ax1.set_ylabel("Weekly Visits")
            st.pyplot(fig1)
        with c2:
            fig2, ax2 = plt.subplots()
            if "SNAP_Applications" in w.columns:
                ax2.plot(w["date"], w["SNAP_Applications"], label="SNAP_Applications")
            if "Unemployment_Claims" in w.columns:
                ax2.plot(w["date"], w["Unemployment_Claims"], label="Unemployment_Claims")
            if len(ax2.lines) == 0:
                ax2.plot([], [])
            ax2.legend()
            ax2.set_title(f"Lead Indicators — {county}")
            ax2.set_xlabel("Date"); ax2.set_ylabel("Weekly Count / Index Units")
            st.pyplot(fig2)
    else:
        st.info("Upload or place `synthetic_weekly_inputs_minnesota.csv` into `data/` to plot trends.")

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
    st.subheader("One-click PDF Export (Branded)")
    st.caption("Generates an executive summary PDF with RAG counts, top counties, and a county trend chart.")
    county_for_pdf = None
    if weekly is not None and "county" in weekly.columns:
        county_for_pdf = st.selectbox("County for trend chart in PDF", sorted(weekly["county"].dropna().unique()))
    include_playbook = st.checkbox("Include RAG action playbook summary", value=True)

    if st.button("Generate PDF"):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=LETTER)
        W, H = LETTER
        M = 0.6*inch

        # header band
        c.setFillColor(colors.HexColor(PRIMARY))
        c.rect(0, H-30, W, 30, fill=True, stroke=False)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(M, H-22, "Minnesota Food Insecurity EWS — Executive Summary")

        y = H - 50

        # logos (optional placeholders)
        try:
            dhs = ImageReader("data/logo_dhs.png")
            c.drawImage(dhs, W-2.2*inch, H-28, width=0.9*inch, height=0.9*inch, mask='auto')
        except Exception:
            pass
        try:
            mde = ImageReader("data/logo_mde.png")
            c.drawImage(mde, W-1.1*inch, H-28, width=0.9*inch, height=0.9*inch, mask='auto')
        except Exception:
            pass

        # as-of
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(M, y, f"As of: {st.session_state.get('as_of', '—') if 'as_of' in st.session_state else '—'}   Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        y -= 16

        # RAG counts
        if overview is not None and not overview.empty:
            red_ct = int((overview['RAG_Status']=='Red').sum())
            amber_ct = int((overview['RAG_Status']=='Amber').sum())
            green_ct = int((overview['RAG_Status']=='Green').sum())
            c.setFont("Helvetica-Bold", 11)
            c.drawString(M, y, "Current RAG Status (Counties)")
            y -= 14
            c.setFont("Helvetica", 10)
            c.drawString(M, y, f"Red: {red_ct}   Amber: {amber_ct}   Green: {green_ct}")
            y -= 18

        # Top counties chart
        if overview is not None and not overview.empty:
            try:
                df_tmp = overview.copy().sort_values("Prob_Spike_8w", ascending=False).head(10)
                img_buf = io.BytesIO()
                fig, ax = plt.subplots()
                ax.bar(df_tmp["County"], df_tmp["Prob_Spike_8w"])
                ax.set_ylim(0,1); ax.set_ylabel("Probability")
                ax.set_title("Top 10 Counties — 8-week Spike Probability")
                fig.tight_layout()
                fig.savefig(img_buf, format="png", dpi=150)
                plt.close(fig)
                img_buf.seek(0)
                img = ImageReader(img_buf)
                img_w = W - 2*M
                img_h = img_w * 0.45
                c.drawImage(img, M, y - img_h, width=img_w, height=img_h, mask='auto')
                y -= (img_h + 10)
            except Exception:
                pass

        # County trend
        if county_for_pdf and weekly is not None and "date" in weekly.columns:
            try:
                wpdf = weekly[weekly["county"]==county_for_pdf].sort_values("date")
                img_buf2 = io.BytesIO()
                fig2, ax2 = plt.subplots()
                ax2.plot(wpdf["date"], wpdf["Food_Shelf_Visits"])
                ax2.set_title(f"Food Shelf Visits — {county_for_pdf}")
                ax2.set_xlabel("Date"); ax2.set_ylabel("Weekly Visits")
                fig2.tight_layout()
                fig2.savefig(img_buf2, format="png", dpi=150)
                plt.close(fig2)
                img_buf2.seek(0)
                img2 = ImageReader(img_buf2)
                img_w2 = W - 2*M
                img_h2 = img_w2 * 0.35
                if y - img_h2 < M:
                    c.showPage()
                    # header on new page
                    c.setFillColor(colors.HexColor(PRIMARY)); c.rect(0, H-30, W, 30, fill=True, stroke=False)
                    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 12)
                    c.drawString(M, H-22, "Minnesota Food Insecurity EWS — Executive Summary (cont.)")
                    y = H - 50
                c.drawImage(img2, M, y - img_h2, width=img_w2, height=img_h2, mask='auto')
                y -= (img_h2 + 10)
            except Exception:
                pass

        # Playbook summary
        if include_playbook and playbook is not None and not playbook.empty:
            if y < 1.5*inch:
                c.showPage()
                c.setFillColor(colors.HexColor(PRIMARY)); c.rect(0, H-30, W, 30, fill=True, stroke=False)
                c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 12)
                c.drawString(M, H-22, "Minnesota Food Insecurity EWS — RAG Playbook")
                y = H - 50
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(M, y, "RAG Action Playbook — Summary")
            y -= 14
            c.setFont("Helvetica", 9)
            cols_show = ["County","RAG_Status","Lead Agency","Governance Cadence","Outreach Focus"]
            pb = playbook.copy()
            for _, row in pb.head(6).iterrows():
                text = f"- {row.get('County','?')}: {row.get('RAG_Status','?')}; Lead: {row.get('Lead Agency','?')}; Cadence: {row.get('Governance Cadence','?')}; Outreach: {row.get('Outreach Focus','?')}"
                c.drawString(M, y, text[:120])
                y -= 12
                if y < M:
                    c.showPage()
                    c.setFillColor(colors.HexColor(PRIMARY)); c.rect(0, H-30, W, 30, fill=True, stroke=False)
                    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 12)
                    c.drawString(M, H-22, "Minnesota Food Insecurity EWS — RAG Playbook (cont.)")
                    y = H - 50

        c.showPage()
        c.save()
        buffer.seek(0)
        st.download_button("Download PDF", buffer, file_name="MN_EWS_Executive_Summary.pdf", mime="application/pdf")

st.markdown(f"<hr style='border:1px solid {BORDER};'>", unsafe_allow_html=True)
st.caption("© {} Minnesota Food Insecurity EWS — Branded Main".format(pd.Timestamp.today().year))
