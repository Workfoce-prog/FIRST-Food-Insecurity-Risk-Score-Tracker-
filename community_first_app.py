
import streamlit as st
import pandas as pd
import altair as alt

# Multilingual support
lang = st.selectbox("🌐 Select Language", ["English", "French", "Swahili"])
labels = {
    "English": {
        "title": "📊 Community Food Insecurity Tracker",
        "upload": "Upload Community Data",
        "submit": "Submit Update",
        "admin": "Admin Dashboard",
        "mobile": "📱 Mobile Worker View",
    },
    "French": {
        "title": "📊 Suivi de l'insécurité alimentaire communautaire",
        "upload": "Téléverser des données",
        "submit": "Soumettre une mise à jour",
        "admin": "Tableau de bord administrateur",
        "mobile": "📱 Vue mobile pour les agents",
    },
    "Swahili": {
        "title": "📊 Kifuatiliaji cha Njaa kwa Jamii",
        "upload": "Pakia Taarifa",
        "submit": "Tuma Taarifa",
        "admin": "Dashibodi ya Msimamizi",
        "mobile": "📱 Mwonekano wa Simu ya Jamii",
    }
}

st.title(labels[lang]["title"])

# Simulated user role
view = st.radio("Choose View", ["Community Worker", "Admin"], horizontal=True)

if view == "Community Worker":
    st.subheader(labels[lang]["mobile"])
    uploaded_file = st.file_uploader(labels[lang]["upload"], type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success("✅ File uploaded successfully.")
        st.dataframe(df)
    if st.button(labels[lang]["submit"]):
        st.success("✅ Update submitted to central dashboard.")

else:
    st.subheader(labels[lang]["admin"])
    # Sample data and visualization
    sample_data = pd.DataFrame({
        "County": ["A", "B", "C"],
        "Risk Score": [85, 65, 45]
    })
    chart = alt.Chart(sample_data).mark_bar().encode(
        x="County", y="Risk Score", color="Risk Score"
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(sample_data)
