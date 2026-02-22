import os
import pickle
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not set in environment variables")

genai.configure(api_key=api_key)
llm_model = genai.GenerativeModel("gemini-3-flash-preview")


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

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["10 per minute"]
)


tfidf = None
vectors = None
data = None

def load_models():
    with open("model.pkl", "rb") as f:
        tfidf_model = pickle.load(f)

    with open("vectors.pkl", "rb") as f:
        vector_data = pickle.load(f)

    with open("data.pkl", "rb") as f:
        dataframe = pickle.load(f)

    return tfidf_model, vector_data, dataframe


def get_models():
    global tfidf, vectors, data
    if tfidf is None:
        tfidf, vectors, data = load_models()
    return tfidf, vectors, data


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Backend Running"})


@app.route("/recommend", methods=["POST"])
@limiter.limit("5 per minute")
def recommend():
    try:
        req = request.get_json()

        chemical = req.get("chemical")
        crop = req.get("crop")
        acres = req.get("acres")

        if not chemical or not crop or not acres:
            return jsonify({
                "status": "error",
                "message": "Missing required fields."
            }), 400

        tfidf_model, vector_data, dataframe = get_models()

        query = f"{chemical} {crop}".lower()
        query_vec = tfidf_model.transform([query])

        similarity = cosine_similarity(query_vec, vector_data)
        best_idx = similarity.argmax()
        best_score = similarity.max()

        if best_score <= 0.4:
            return jsonify({
                "status": "error",
                "message": f"No reliable match found for '{chemical}' on '{crop}'."
            }), 400

        res = dataframe.iloc[best_idx]

        prompt = f"""
        Act as a friendly agricultural expert.
        A farmer uses {chemical} on {crop} for {res['problem_or_pest']}.
        The organic alternative is {res['organic_alternative']}.

        - Explain why it is cheaper for the farmer.
        - Step 1: How to apply it for {acres} acres.
        - Step 2: Remind them to apply during {res['application_time']}.
        - Explain why {res['organic_alternative']} is better for soil.

        Provide the response ONLY in bullet points using '-' followed by a space.
        Do not use bold or headers.
        """

        try:
            llm_response = llm_model.generate_content(prompt)
            llm_text = llm_response.text
        except Exception as e:
            llm_text = f"Gemini Error: {str(e)}"

        return jsonify({
            "status": "success",
            "alternative": res["organic_alternative"],
            "dosage": res["dosage"],
            "application_time": res["application_time"],
            "safety_note": res["safety_note"],
            "llm_advice": llm_text,
            "confidence": round(float(best_score), 4)
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

