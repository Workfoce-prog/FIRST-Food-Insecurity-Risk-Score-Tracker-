# Minnesota EWS — Branded Streamlit Main (with PDF Export)

## Deploy (Streamlit Cloud)
1. Put `community_first_app.py` and `requirements.txt` in the repo root.
2. Include the `/data` folder (optional, but lets the app render immediately).
3. In App settings → **Main file path**: `community_first_app.py`
4. Deploy.
5. Replace `/data/logo_dhs.png` and `/data/logo_mde.png` with real logo PNGs for branding.

### Features
- Tabs: RAG overview, Trends, Action Playbook, Metrics Reference, **PDF Export**
- Branding colors + header, optional DHS/MDE logos
- Sidebar uploads or bundled sample data
