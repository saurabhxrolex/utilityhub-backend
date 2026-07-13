from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from collections import defaultdict

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("GROQ_API_KEY")
URL = "https://api.groq.com/openai/v1/chat/completions"

chat_history = defaultdict(list)

@app.route("/")
def home():
    return "UtilityHub Backend Running!"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    message = data.get("message", "")
    user_id = data.get("user_id", "default")

    history = chat_history[user_id]

    history.append({
        "role": "user",
        "content": message
    })

    if len(history) > 10:
        history = history[-10:]

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [
        {
            "role": "system",
            "content": (
                "You are UtilityHub AI. "
                "Reply in the same language as the user. "
                "Be helpful, accurate and remember previous conversation."
            )
        }
    ] + history

    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages
    }

    try:
        r = requests.post(URL, headers=headers, json=body, timeout=30)

        if r.status_code != 200:
            return jsonify({"reply": r.text})

        result = r.json()
        reply = result["choices"][0]["message"]["content"]

        history.append({
            "role": "assistant",
            "content": reply
        })

        chat_history[user_id] = history

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": str(e)})


@app.route("/history", methods=["POST"])
def history():
    data = request.get_json()
    user_id = data.get("user_id", "default")
    return jsonify(chat_history[user_id])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
