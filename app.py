from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("GROQ_API_KEY")

URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route("/")
def home():
    return "UtilityHub Backend Running!"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ]
    }

    try:
        r = requests.post(URL, headers=headers, json=body, timeout=30)

        if r.status_code != 200:
            return jsonify({"reply": r.text})

        result = r.json()
        reply = result["choices"][0]["message"]["content"]

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
