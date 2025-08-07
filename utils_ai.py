
def generate_ai_flags(row):
    if row["Risk_Score"] > 75:
        return "Immediate Attention"
    elif row["Risk_Score"] > 50:
        return "Follow-Up Needed"
    else:
        return "Stable"
