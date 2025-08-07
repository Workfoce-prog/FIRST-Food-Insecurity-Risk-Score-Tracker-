
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils_ai import generate_ai_flags
from utils_translate import translate_text

st.set_page_config(page_title="Food Insecurity Risk Tracker", layout="wide")
st.title("🍎 Food Insecurity Risk Tracker – Enhanced with AI & Translation")

lang = st.selectbox("🌍 Select Language", ["English", "French", "Spanish", "Arabic"])
translate = lambda text: translate_text(text, lang)

st.markdown(translate("Upload your CSV file with household-level data to calculate food insecurity risk."))

uploaded_file = st.file_uploader(translate("Upload CSV"), type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df["Risk_Score"] = df[["Unemployment", "Food_Expense_Burden", "Shutoff_Notices", "Eviction_Notices"]].mean(axis=1)
    df["Risk_Band"] = pd.cut(df["Risk_Score"], bins=[0, 25, 50, 75, 100], labels=["Green", "Yellow", "Orange", "Red"])
    df["AI_Flag"] = df.apply(generate_ai_flags, axis=1)

    st.dataframe(df)

    # Charts
    st.subheader(translate("📊 Risk Distribution"))
    st.bar_chart(df["Risk_Band"].value_counts())

    st.subheader(translate("📈 Average Risk Trend (Simulated)"))
    trend_data = df.groupby("Region")["Risk_Score"].mean()
    st.line_chart(trend_data)

    # Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(translate("Download Results"), csv, file_name="food_insecurity_results.csv", mime="text/csv")
