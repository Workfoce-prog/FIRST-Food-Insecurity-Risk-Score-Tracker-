
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Community FIRST Risk Tracker", layout="wide")

st.title("🍎 Food Insecurity Risk Score Tracker (Community Version)")
st.markdown("For use by schools, community centers, or food access teams.")

# Upload CSV
uploaded_file = st.file_uploader("Upload Household Data (CSV)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Compute Risk Score
    components = ["FRL_Status", "SNAP_Use", "Unemployed", "Pantry_Use", "Utility_Shutoff_Risk", "Housing_Instability"]
    df["Risk_Score"] = df[components].sum(axis=1) * 15

    def categorize(score):
        if score >= 90:
            return "Critical"
        elif score >= 70:
            return "High"
        elif score >= 40:
            return "Medium"
        else:
            return "Low"

    df["Risk_Level"] = df["Risk_Score"].apply(categorize)

    # Show Data
    st.subheader("Scored Households")
    st.dataframe(df)

    # Download
    csv_out = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Scored CSV", data=csv_out, file_name="FIRST_Scored_Results.csv", mime="text/csv")

    st.markdown("---")
    st.info("Risk levels: Low (0–39), Medium (40–69), High (70–89), Critical (90–100)")

st.caption("StratDesign Solutions – Community FIRST Demo")
