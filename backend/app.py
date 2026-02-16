import os
import pickle
import re
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity


def load_models():
    with open('model.pkl', 'rb') as f:
        tfidf = pickle.load(f)

    with open('vectors.pkl', 'rb') as f:
        vectors = pickle.load(f)

    with open('data.pkl', 'rb') as f:
        data = pickle.load(f)

    return tfidf, vectors, data


tfidf, vectors, data = load_models()

app = Flask(__name__)
CORS(app)


load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

genai.configure(api_key=api_key)


llm_model = genai.GenerativeModel('gemini-1.5-flash')


@app.route('/recommend', methods=['POST'])
def recommend():

    req = request.get_json()

    chemical = req['chemical']
    crop = req['crop']

    query = f"{chemical} {crop}".lower()
    query_vec = tfidf.transform([query])

    similarity = cosine_similarity(query_vec, vectors)
    best_idx = similarity.argmax()
    res = data.iloc[best_idx]

    
    prompt = f"""
    A farmer is using {chemical} on {crop}.
    Suggest why switching to {res['organic_alternative']} is better.
    The target issue is {res['problem_or_pest']}.
    Explain in 3 simple bullet points.
    Mention that it should be applied during {res['application_time']}.
    Keep language simple.
    """

    try:
        llm_response = llm_model.generate_content(prompt)
        llm_text = llm_response.text
    except Exception as e:
        llm_text = f"Gemini Error: {str(e)}"

    return jsonify({
        "alternative": res['organic_alternative'],
        "dosage": res['dosage'],
        "llm_advice": llm_text,
        "safety": res['safety_note'],
        "confidence": round(float(similarity[0][best_idx]), 4)
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
