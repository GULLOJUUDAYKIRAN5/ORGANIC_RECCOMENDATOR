import streamlit as st
import pickle
import re
import os
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from google import genai

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY not found in .env file")
    st.stop()

# Initialize Gemini Client (NEW SDK STYLE)
client = genai.Client(api_key=api_key)

# -----------------------------
# Load ML Models
# -----------------------------
def load_models():
    with open('model.pkl', 'rb') as f:
        tfidf = pickle.load(f)

    with open('vectors.pkl', 'rb') as f:
        vectors = pickle.load(f)

    with open('data.pkl', 'rb') as f:
        data = pickle.load(f)

    return tfidf, vectors, data


tfidf, vectors, data = load_models()


def recommend(chemical, crop, acres):
    query_text = f"{chemical} {crop}".lower()
    query_vec = tfidf.transform([query_text])

    similarity = cosine_similarity(query_vec, vectors)
    best_match_idx = similarity.argmax()
    res = data.iloc[best_match_idx]

    try:
        base_num = float(re.search(r"(\d+\.?\d*)", res['dosage']).group(1))

        if 'acre' in res['dosage'].lower():
            total_needed = base_num * acres
            unit = res['dosage'].split('/')[0].replace(str(int(base_num)), "").strip()
            calculated_dosage = f"{total_needed} {unit} total for {acres} acres"
        else:
            calculated_dosage = res['dosage']
    except:
        calculated_dosage = res['dosage']

 
    prompt = f"""
    A farmer is using {chemical} on {crop}.
    Suggest why switching to {res['organic_alternative']} is better.
    The target issue is {res['problem_or_pest']}.
    Explain in 3 simple bullet points.
    Mention that it should be applied during {res['application_time']}.
    Keep language simple.
    """

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-3-pro-preview", contents=prompt
        )
        llm_advice = (response.text)
    except Exception as e:
        llm_advice = f"Gemini Error: {str(e)}"

    return {
        "Organic Alternative": res['organic_alternative'],
        "Quantity": calculated_dosage,
        "Application Time": res['application_time'],
        "Safety Note": res['safety_note'],
        "Confidence Score": round(float(similarity[0][best_match_idx]), 4),
        "LLM Advice": llm_advice
    }


st.title("🌱 Organic Alternative Recommender + AI Advisor")

chemical = st.text_input("Enter Chemical Name")
crop = st.text_input("Enter Crop Name")
acres = st.number_input("Enter Acres", min_value=0.0, value=1.0)

if st.button("Recommend"):
    if chemical and crop:
        result = recommend(chemical, crop, acres)

        st.subheader("Recommendation")
        st.write("**Organic Alternative:**", result["Organic Alternative"])
        st.write("**Quantity Needed:**", result["Quantity"])
        st.write("**Application Time:**", result["Application Time"])
        st.write("**Safety Note:**", result["Safety Note"])
        st.write("**Confidence Score:**", result["Confidence Score"])

        st.subheader("🤖 AI Advice")
        st.write(result["LLM Advice"])
    else:
        st.warning("Please enter both chemical and crop.")
