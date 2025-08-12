
import streamlit as st
import pandas as pd
import numpy as np
import io, os, json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path

# PDF export
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors

st.set_page_config(page_title="Minnesota Food Insecurity EWS", page_icon="📊", layout="wide")

# ----------------- Paths & Branding -----------------
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
PRIMARY = "#0B5FFF"
BORDER  = "#E5E7EB"

def safe_logo(path, caption=None):
    try:
        if path.exists() and path.stat().st_size > 0:
            st.image(str(path), caption=caption, use_container_width=True)
        else:
            st.markdown(f"**{caption or 'Logo'}**")
    except Exception:
        st.markdown(f"**{caption or 'Logo'}**")

def header_brand():
    c1, c2, c3 = st.columns([1,6,1])
    with c1:
        safe_logo(DATA_DIR / "logo_dhs.png", caption="DHS")
    with c2:
        st.markdown(f"<h2 style='margin-bottom:0; color:{PRIMARY};'>Minnesota Food Insecurity Early Warning System</h2>", unsafe_allow_html=True)
        st.caption("MN-aligned variables, county RAG alerts, action playbooks, and data dictionary")
    with c3:
        safe_logo(DATA_DIR / "logo_mde.png", caption="MDE")
    st.markdown(f"<hr style='border:1px solid {BORDER}; margin-top:0;'>", unsafe_allow_html=True)

# --------------- Recommended Actions --------------------
DEFAULT_OVERRIDES = {
    "Hennepin County": {
        "Red": [
            "Activate city–county joint coordination with DHS/MDE; embed liaison to EOC if active.",
            "Expand emergency meal sites with weekend kits; coordinate with Metro Transit for last-mile access.",
            "Same-day SNAP interviews; multilingual SMS (Spanish, Somali, Hmong) via county partners."
        ],
        "Amber": [
            "Pre-stage shelf-stable items at high-throughput pantries; confirm extended hours.",
            "Target hotspot ZIPs with SNAP outreach through clinics and schools.",
            "Notify school nutrition directors; prepare weekend kits."
        ],
        "Green": [
            "Baseline SNAP outreach via community partners.",
            "Monthly drift checks and dashboard sharing with city/county partners."
        ]
    },
    "Ramsey County": {
        "Red": [
            "Scale Saint Paul meal sites and weekend/holiday kits in coordination with MDE.",
            "Stand up SNAP surge staffing; enable walk-in interviews at Service Center.",
            "Partner with culturally specific CBOs for outreach (e.g., Hmong, Karen, Somali)."
        ],
        "Amber": [
            "Advance TEFAP orders; stage food bank inventory for East Side hotspots.",
            "Coordinate with SPPS for breakfast expansion and backpack programs.",
            "Targeted SNAP outreach in transit-poor corridors."
        ],
        "Green": [
            "Maintain baseline pantry logistics and SNAP outreach.",
            "Monthly QA on forecasts; share brief with county board staff."
        ]
    },
    "St. Louis County": {
        "Any": [
            "Coordinate with regional food banks for northland delivery constraints.",
            "Target SNAP outreach in rural ZIPs; leverage school bus routes for kit distribution.",
            "Engage tribal partners on culturally appropriate food distribution."
        ]
    }
}

def recommended_actions_for_rag(rag: str):
    rag = (rag or "").strip().title()
    if rag == "Red":
        return [
            "Pre-position TEFAP and food shelf inventory with regional food banks.",
            "Stand up emergency meal sites (SSO/SFSP windows where eligible); include weekend/holiday kits.",
            "Expedite SNAP processing: same-day interviews; reminders for verifications.",
            "Coordinate with county HHS on emergency housing/utility supports.",
            "Run weekly incident-style command huddles; monitor pantry throughput daily."
        ]
    if rag == "Amber":
        return [
            "Alert school nutrition directors; prep weekend meal kits; watch NSLP/SBP vs enrollment.",
            "Target SNAP outreach in forecast hotspots; promote online apps and phone interviews.",
            "Advance TEFAP orders; stage shelf-stable items; confirm pantry extended hours.",
            "Review staffing vs. caseload; prepare surge schedules."
        ]
    return [
        "Maintain baseline SNAP outreach and pantry logistics.",
        "Monthly forecast QA and drift checks; validate vs observed trends.",
        "Share dashboards with county partners; sustain data-sharing (SNAP, NSLP, pantry)."
    ]

def load_overrides(uploaded_json):
    try:
        if uploaded_json is not None:
            return json.load(uploaded_json)
    except Exception:
        pass
    try:
        p = DATA_DIR / "county_overrides.json"
        if p.exists():
            with open(p, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return DEFAULT_OVERRIDES

def recommended_actions_for_county(county: str, rag: str, overrides: dict):
    c = (county or "").strip()
    r = (rag or "").strip().title()
    if c in overrides and isinstance(overrides[c], dict) and r in overrides[c]:
        return overrides[c][r], True
    if c in overrides and isinstance(overrides[c], dict) and "Any" in overrides[c]:
        return overrides[c]["Any"], True
    return recommended_actions_for_rag(r), False

# --------------- Embedded Example Data --------------------
def make_embedded_weekly():
    start = pd.Timestamp.today().normalize() - pd.Timedelta(weeks=60)
    weeks = pd.date_range(start, periods=60, freq="W")
    counties = ["Hennepin County", "Ramsey County", "St. Louis County"]
    rows = []
    rng = np.random.default_rng(42)
    for c in counties:
        base_snap_apps = rng.integers(300, 600)
        base_snap_cases = rng.integers(5000, 12000)
        base_meals = rng.integers(8000, 20000)
        base_pantry = rng.integers(700, 1400)
        base_unemp = rng.integers(500, 2000)
        base_cpi = 250 + rng.uniform(-5, 5)
        season = (np.sin(np.linspace(0, 4*np.pi, len(weeks))) + 1)/2
        snap_apps = base_snap_apps + 40*season + rng.normal(0, 15, len(weeks))
        snap_cases = base_snap_cases + 200*season + rng.normal(0, 60, len(weeks))
        school_meals = base_meals + 1500*(1-season) + rng.normal(0, 250, len(weeks))
        pantry_visits = base_pantry + 120*season + rng.normal(0, 35, len(weeks))
        unemp_claims = base_unemp + 80*season + rng.normal(0, 25, len(weeks))
        cpi_food = base_cpi + np.linspace(0, 5, len(weeks)) + rng.normal(0, 0.5, len(weeks))
        for i, d in enumerate(weeks):
            rows.append({
                "date": d,
                "county": c,
                "SNAP_Applications": int(max(0, round(snap_apps[i]))),
                "SNAP_Active_Cases": int(max(0, round(snap_cases[i]))),
                "NSLP_SBP_Participation": int(max(0, round(school_meals[i]))),
                "Food_Shelf_Visits": int(max(0, round(pantry_visits[i]))),
                "Unemployment_Claims": int(max(0, round(unemp_claims[i]))),
                "CPI_Food_At_Home_Index": float(cpi_food[i]),
                "Eviction_Filings": int(rng.integers(5, 30)),
                "Utility_Shutoffs": int(rng.integers(10, 45)),
                "Drought_Severity_Index": float(np.clip(0.4 + 0.2*np.sin(i/8), 0, 1)),
                "Household_Pulse_Food_Insufficiency_Pct": float(6 + 2*season[i] + rng.normal(0, 0.4))
            })
    return pd.DataFrame(rows)

def make_embedded_overview(weekly_df):
    latest = weekly_df.groupby("county").tail(8).copy()
    probs = []
    for c, grp in latest.groupby("county"):
        x = grp["Food_Shelf_Visits"]
        mu, sd = x.mean(), x.std(ddof=1) if x.std(ddof=1)>0 else 1.0
        z = (x.iloc[-1] - mu)/sd
        p = float(1/(1+np.exp(-z)))
        probs.append({"County": c, "Prob_Spike_8w": p})
    df = pd.DataFrame(probs).sort_values("Prob_Spike_8w", ascending=False)
    def rag(p): return "Red" if p>0.60 else "Amber" if p>=0.30 else "Green"
    df["RAG_Status"] = df["Prob_Spike_8w"].apply(rag)
    df["As_Of_Date"] = str(pd.to_datetime(weekly_df["date"]).max().date())
    df["Lead_Time_Weeks"] = 8
    return df

def make_embedded_playbook():
    rows = []
    for c in ["Hennepin County","Ramsey County","St. Louis County"]:
        rows.append({
            "County": c, "RAG_Status": "Amber",
            "Lead Agency": "DHS (with MDE & county HHS)",
            "Governance Cadence": "Biweekly situation meeting",
            "Outreach Focus": "ZIP-targeted SNAP outreach; clinic/school partners"
        })
    return pd.DataFrame(rows)

def make_embedded_metrics_ref():
    return pd.DataFrame([
        {"Metric":"SNAP_Applications","Definition":"New SNAP apps per week","Refresh Cadence":"Weekly"},
        {"Metric":"Food_Shelf_Visits","Definition":"Pantry client visits per week","Refresh Cadence":"Weekly"},
        {"Metric":"Unemployment_Claims","Definition":"UI claims filed","Refresh Cadence":"Weekly"},
        {"Metric":"CPI_Food_At_Home_Index","Definition":"Grocery price index","Refresh Cadence":"Monthly"},
        {"Metric":"RAG_Status","Definition":"Risk tier from 8w spike probability","Refresh Cadence":"Weekly"},
    ])

# --------------- Robust loader with embedded fallback --------------------
@st.cache_data
def load_or_embed_all(uploaded_latest, uploaded_overview, uploaded_metrics_ref, uploaded_weekly, uploaded_playbook):
    def try_csv(upload, relpath, parse_dates=None):
        if upload is not None:
            return pd.read_csv(upload, parse_dates=parse_dates) if parse_dates else pd.read_csv(upload)
        p = DATA_DIR / relpath
        if p.exists():
            return pd.read_csv(p, parse_dates=parse_dates) if parse_dates else pd.read_csv(p)
        if Path(relpath).exists():
            return pd.read_csv(relpath, parse_dates=parse_dates) if parse_dates else pd.read_csv(relpath)
        return None

    weekly = try_csv(uploaded_weekly, "synthetic_weekly_inputs_minnesota.csv", parse_dates=["date"])
    if weekly is None: weekly = make_embedded_weekly()

    overview = try_csv(uploaded_overview, "current_risk_overview_minnesota.csv")
    if overview is None: overview = make_embedded_overview(weekly)

    latest = try_csv(uploaded_latest, "mn_latest_snapshot_with_RAG.csv", parse_dates=["date"])
    if latest is None:
        latest = (weekly[weekly["date"]==weekly["date"].max()]
                  [["county","date","SNAP_Applications","SNAP_Active_Cases","NSLP_SBP_Participation","Food_Shelf_Visits",
                    "Unemployment_Claims","CPI_Food_At_Home_Index","Eviction_Filings","Utility_Shutoffs",
                    "Drought_Severity_Index","Household_Pulse_Food_Insufficiency_Pct"]].copy())
        ov = overview[["County","Prob_Spike_8w","RAG_Status","Lead_Time_Weeks"]].rename(columns={"County":"county"})
        latest = latest.merge(ov, on="county", how="left")

    metrics = try_csv(uploaded_metrics_ref, "metrics_reference_minnesota.csv")
    if metrics is None: metrics = make_embedded_metrics_ref()

    playbook = try_csv(uploaded_playbook, "mn_expanded_RAG_action_playbook.csv")
    if playbook is None: playbook = make_embedded_playbook()

    return latest, overview, metrics, weekly, playbook

# ----------------- App Body -----------------
header_brand()

# Sidebar uploads
st.sidebar.title("⚙️ Data Sources")
uploaded_latest = st.sidebar.file_uploader("Latest snapshot with RAG (mn_latest_snapshot_with_RAG.csv)", type=["csv"])
uploaded_overview = st.sidebar.file_uploader("Risk overview (current_risk_overview_minnesota.csv)", type=["csv"])
uploaded_metrics_ref = st.sidebar.file_uploader("Metrics reference (metrics_reference_minnesota.csv)", type=["csv"])
st.sidebar.markdown("---")
uploaded_weekly = st.sidebar.file_uploader("Weekly inputs (synthetic_weekly_inputs_minnesota.csv)", type=["csv"])
uploaded_playbook = st.sidebar.file_uploader("RAG playbook (mn_expanded_RAG_action_playbook.csv)", type=["csv"])
st.sidebar.markdown("---")
uploaded_overrides = st.sidebar.file_uploader("County overrides (county_overrides.json)", type=["json"])

with st.sidebar.expander("Need a template?"):
    st.caption("Download a ready-made JSON template, edit locally, then upload it above.")
    template_str = json.dumps(DEFAULT_OVERRIDES, indent=2)
    st.download_button("Download overrides template", template_str, file_name="county_overrides_template.json", mime="application/json")
    st.code(template_str[:1000] + ("\n... (truncated)" if len(template_str)>1000 else ""))

latest, overview, metrics_ref, weekly, playbook = load_or_embed_all(
    uploaded_latest, uploaded_overview, uploaded_metrics_ref, uploaded_weekly, uploaded_playbook
)

# Load overrides (uploaded or file or defaults)
overrides = load_overrides(uploaded_overrides)

# KPIs
kpi_cols = st.columns(4)
as_of = None
if latest is not None and "date" in latest.columns and not latest.empty:
    try:
        as_of = str(pd.to_datetime(latest["date"]).max().date())
    except Exception:
        as_of = None
st.session_state["as_of"] = as_of
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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📍 Current Risk (RAG)",
    "📈 Trends",
    "🧭 Action Playbook",
    "ℹ️ Metrics Reference",
    "🖨️ PDF Export",
    "📚 Examples"
])

with tab1:
    st.subheader("County Risk Overview — 8-week Horizon")
    df = overview.copy()
    if "RAG_Status" in df.columns:
        df["RAG_Badge"] = df["RAG_Status"].apply(lambda t: ":red_circle: Red" if t=="Red" else (":orange_circle: Amber" if t=="Amber" else ":green_circle: Green"))
    # add summary for export based on overrides
    def summary_row(row):
        acts, _ = recommended_actions_for_county(row["County"], row["RAG_Status"], overrides)
        return " | ".join(acts[:3])
    df["Recommended_Action_Summary"] = df.apply(summary_row, axis=1)
    st.dataframe(df, use_container_width=True)

    # Chart
    if "County" in df.columns and "Prob_Spike_8w" in df.columns:
        fig, ax = plt.subplots()
        ax.bar(df["County"], df["Prob_Spike_8w"]); ax.set_ylim(0,1)
        ax.set_ylabel("Probability"); ax.set_title("Predicted Probability of Spike in 8 Weeks — Counties")
        st.pyplot(fig)

    st.markdown("### Recommended Actions")
    sel = st.selectbox("Select a county", df["County"].tolist())
    rag = df.loc[df["County"]==sel, "RAG_Status"].iloc[0]
    actions, customized = recommended_actions_for_county(sel, rag, overrides)
    st.markdown("**Status:** " + (":red_circle: Red" if rag=="Red" else (":orange_circle: Amber" if rag=="Amber" else ":green_circle: Green")))
    if customized:
        st.success("Using **county-specific overrides**")
    st.markdown("\n".join([f"- {a}" for a in actions]))

with tab2:
    st.subheader("Weekly Trends — Food Shelf Visits & Lead Indicators")
    county = st.selectbox("Select County", sorted(weekly["county"].dropna().unique()))
    w = weekly[weekly["county"]==county].sort_values("date")
    c1, c2 = st.columns(2)
    with c1:
        fig1, ax1 = plt.subplots()
        ax1.plot(w["date"], w["Food_Shelf_Visits"])
        ax1.set_title(f"Food Shelf Visits — {county}")
        ax1.set_xlabel("Date"); ax1.set_ylabel("Weekly Visits")
        st.pyplot(fig1)
    with c2:
        fig2, ax2 = plt.subplots()
        ax2.plot(w["date"], w["SNAP_Applications"], label="SNAP_Applications")
        ax2.plot(w["date"], w["Unemployment_Claims"], label="Unemployment_Claims")
        ax2.legend()
        ax2.set_title(f"Lead Indicators — {county}")
        ax2.set_xlabel("Date"); ax2.set_ylabel("Weekly Count / Index Units")
        st.pyplot(fig2)

with tab3:
    st.subheader("RAG Action Playbook (MN-aligned)")
    st.dataframe(playbook, use_container_width=True)

with tab4:
    st.subheader("Metrics Reference")
    st.dataframe(metrics_ref, use_container_width=True)

with tab5:
    st.subheader("One-click PDF Export (Branded)")
    st.caption("Includes RAG counts, top counties, a county trend chart, and **county-specific recommended actions** when defined.")
    county_for_pdf = st.selectbox("County for trend chart in PDF", sorted(weekly["county"].dropna().unique()))
    include_playbook = st.checkbox("Include RAG action playbook summary", value=True)
    if st.button("Generate PDF"):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=LETTER)
        W, H = LETTER; M = 0.6*inch
        # header band
        c.setFillColor(colors.HexColor(PRIMARY)); c.rect(0, H-30, W, 30, fill=True, stroke=False)
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 12)
        c.drawString(M, H-22, "Minnesota Food Insecurity EWS — Executive Summary")
        y = H - 50
        # as-of + RAG counts
        c.setFillColor(colors.black); c.setFont("Helvetica", 10)
        c.drawString(M, y, f"As of: {st.session_state.get('as_of','—')}   Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"); y -= 16
        red_ct = int((overview['RAG_Status']=='Red').sum()); amber_ct = int((overview['RAG_Status']=='Amber').sum()); green_ct = int((overview['RAG_Status']=='Green').sum())
        c.setFont("Helvetica-Bold", 11); c.drawString(M, y, "Current RAG Status (Counties)"); y -= 14
        c.setFont("Helvetica", 10); c.drawString(M, y, f"Red: {red_ct}   Amber: {amber_ct}   Green: {green_ct}"); y -= 18
        # top-10 chart
        try:
            df_tmp = overview.copy().sort_values("Prob_Spike_8w", ascending=False).head(10)
            img_buf = io.BytesIO(); fig, ax = plt.subplots()
            ax.bar(df_tmp["County"], df_tmp["Prob_Spike_8w"]); ax.set_ylim(0,1); ax.set_ylabel("Probability"); ax.set_title("Top 10 Counties — 8-week Spike Probability")
            fig.tight_layout(); fig.savefig(img_buf, format="png", dpi=150); plt.close(fig); img_buf.seek(0)
            img = ImageReader(img_buf); img_w = W - 2*M; img_h = img_w * 0.45
            c.drawImage(img, M, y - img_h, width=img_w, height=img_h, mask='auto'); y -= (img_h + 10)
        except Exception: pass
        # Recommended actions: top 3 counties (with overrides)
        c.setFont("Helvetica-Bold", 11); c.drawString(M, y, "Recommended Actions — Top 3 Counties"); y -= 14
        c.setFont("Helvetica", 9)
        for _, row in df_tmp.head(3).iterrows():
            county = row["County"]; rag = row["RAG_Status"]
            acts, custom = recommended_actions_for_county(county, rag, load_overrides(None))  # use file/default for PDF
            c.drawString(M, y, f"{county} ({rag})" + (" — customized" if custom else "")); y -= 12
            for act in acts[:3]:
                c.drawString(M+14, y, u"• " + act[:100]); y -= 12
                if y < M + 0.8*inch:
                    c.showPage(); c.setFont("Helvetica-Bold", 12); c.drawString(M, LETTER[1]-40, "Recommended Actions (cont.)"); y = LETTER[1]-60
            y -= 4
        # county trend
        try:
            wpdf = weekly[weekly["county"]==county_for_pdf].sort_values("date")
            img_buf2 = io.BytesIO(); fig2, ax2 = plt.subplots()
            ax2.plot(wpdf["date"], wpdf["Food_Shelf_Visits"]); ax2.set_title(f"Food Shelf Visits — {county_for_pdf}")
            ax2.set_xlabel("Date"); ax2.set_ylabel("Weekly Visits")
            fig2.tight_layout(); fig2.savefig(img_buf2, format="png", dpi=150); plt.close(fig2); img_buf2.seek(0)
            img2 = ImageReader(img_buf2); img_w2 = W - 2*M; img_h2 = img_w2 * 0.35
            if y - img_h2 < M:
                c.showPage(); c.setFont("Helvetica-Bold", 12); c.drawString(M, LETTER[1]-40, "Executive Summary (cont.)"); y = LETTER[1] - 60
            c.drawImage(img2, M, y - img_h2, width=img_w2, height=img_h2, mask='auto'); y -= (img_h2 + 10)
        except Exception: pass
        # optional playbook summary
        if include_playbook:
            if y < 1.5*inch:
                c.showPage(); c.setFont("Helvetica-Bold", 12); c.drawString(M, LETTER[1]-40, "RAG Playbook"); y = LETTER[1]-60
            c.setFont("Helvetica-Bold", 11); c.drawString(M, y, "RAG Action Playbook — Summary"); y -= 14
            c.setFont("Helvetica", 9)
            for _, row in playbook.head(6).iterrows():
                text = f"- {row.get('County','?')}: {row.get('RAG_Status','?')}; Lead: {row.get('Lead Agency','?')}; Cadence: {row.get('Governance Cadence','?')}"
                c.drawString(M, y, text[:120]); y -= 12
                if y < M:
                    c.showPage(); c.setFont("Helvetica-Bold", 12); c.drawString(M, LETTER[1]-40, "RAG Playbook (cont.)"); y = LETTER[1] - 60
        c.showPage(); c.save(); buffer.seek(0)
        st.download_button("Download PDF", buffer, file_name="MN_EWS_Executive_Summary.pdf", mime="application/pdf")

with tab6:
    st.subheader("Examples — Generated from embedded dataset")
    c1, c2, c3 = st.columns(3)
    df = overview.copy()
    figA, axA = plt.subplots(); axA.bar(df["County"], df["Prob_Spike_8w"]); axA.set_ylim(0,1); axA.set_title("Spike Probability — Example"); c1.pyplot(figA)
    county_ex = df["County"].iloc[0]
    w = weekly[weekly["county"]==county_ex].sort_values("date")
    figB, axB = plt.subplots(); axB.plot(w["date"], w["Food_Shelf_Visits"]); axB.set_title(f"Food Shelf Visits — {county_ex}"); c2.pyplot(figB)
    labels = ["SNAP_Applications","Unemployment_Claims","CPI_Food_At_Home_Index"]
    def pctchg(col):
        g = weekly.groupby("date")[col].sum() if col!="CPI_Food_At_Home_Index" else weekly.groupby("date")[col].mean()
        recent, prior = g.tail(4).mean(), g.tail(8).head(4).mean()
        return 0 if prior==0 else (recent-prior)/prior*100
    vals = [pctchg(x) for x in labels]
    figC, axC = plt.subplots(); axC.bar(labels, vals); axC.set_ylabel("% change"); axC.setTitle = "Top Drivers — 4w vs prior 4w"; c3.pyplot(figC)

st.markdown(f"<hr style='border:1px solid {BORDER};'>", unsafe_allow_html=True)
st.caption("© {} Minnesota Food Insecurity EWS — Overrides template download built-in".format(pd.Timestamp.today().year))
