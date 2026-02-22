import os
import pickle
import re
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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



CORS(app, resources={
    r"/*": {
        "origins": [
            "https://organicbuddy.me",
            "https://www.organicbuddy.me",
            "https://organic-reccomendator-k2c8.vercel.app"
        ]
    }
})
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

genai.configure(api_key=api_key)

llm_model = genai.GenerativeModel('gemini-3-flash-preview')

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["10 per minute"]
)

@app.route('/recommend', methods=['POST'])
@limiter.limit("5 per minute")

def recommend():

    req = request.get_json()

    chemical = req['chemical']
    crop = req['crop']
    acres = req['acres']

    query = f"{chemical} {crop}".lower()
    query_vec = tfidf.transform([query])

    similarity = cosine_similarity(query_vec, vectors)
    best_idx = similarity.argmax()
    best_score = similarity.max()

    if best_score <= 0.4:
        return jsonify({
            "status": "error",
            "message": f"I couldn't find a reliable match for '{chemical}' on '{crop}'. Please check your spelling."
        }), 400
    
    res = data.iloc[best_idx]
    prompt = f"""
        Act as a friendly agricultural expert.
        A farmer uses {chemical} on {crop} for {res['problem_or_pest']}.
        The organic alternative is {res['organic_alternative']}.
        
        - Explain why it is cheaper for the farmer.
        - Step 1: How to apply it for {acres} acres.
        - Step 2: Remind them to apply during {res['application_time']}.
        
        - Explain why {res['organic_alternative']} is better for soil.

        Provide the response ONLY in bullet points using '-' followed by a space.
        DO NOT use bold (**) or headers. 
        DO NOT use introductory sentences.
        """
    
    print(round(float(similarity[0][best_idx]), 4))
    try:
        llm_response = llm_model.generate_content(prompt)
        llm_text = llm_response.text
    except Exception as e:
        llm_text = f"Gemini Error: {str(e)}"

    return jsonify({
        "status": "success",
        "alternative": res['organic_alternative'],
        "dosage": res['dosage'],
        "application_time": res['application_time'],
        "safety_note": res['safety_note'],
        "llm_advice": llm_text,
        "confidence": round(float(similarity[0][best_idx]), 4)
    })
    


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
