
def translate_text(text, language):
    translations = {
        "French": {
            "Upload your CSV file with household-level data to calculate food insecurity risk.": "Téléchargez votre fichier CSV avec des données par ménage pour calculer le risque d'insécurité alimentaire.",
            "Upload CSV": "Télécharger le CSV",
            "Download Results": "Télécharger les résultats",
            "📊 Risk Distribution": "📊 Répartition des risques",
            "📈 Average Risk Trend (Simulated)": "📈 Tendance moyenne du risque (simulée)"
        },
        "Spanish": {
            "Upload your CSV file with household-level data to calculate food insecurity risk.": "Sube tu archivo CSV con datos a nivel de hogar para calcular el riesgo de inseguridad alimentaria.",
            "Upload CSV": "Subir CSV",
            "Download Results": "Descargar resultados",
            "📊 Risk Distribution": "📊 Distribución de Riesgo",
            "📈 Average Risk Trend (Simulated)": "📈 Tendencia Promedio del Riesgo (Simulada)"
        },
        "Arabic": {
            "Upload your CSV file with household-level data to calculate food insecurity risk.": "قم بتحميل ملف CSV الخاص بك مع بيانات على مستوى الأسرة لحساب خطر انعدام الأمن الغذائي.",
            "Upload CSV": "تحميل CSV",
            "Download Results": "تحميل النتائج",
            "📊 Risk Distribution": "📊 توزيع المخاطر",
            "📈 Average Risk Trend (Simulated)": "📈 اتجاه متوسط الخطر (محاكاة)"
        }
    }
    return translations.get(language, {}).get(text, text)
