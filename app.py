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
            "You were developed by Saurabh. "
            "Your owner is Saurabh. "
            "If someone asks 'Who made you?', 'Who developed you?', or 'Who is your owner?', reply that you were developed by Saurabh and your owner is Saurabh. "
            "Reply in the same language as the user. "
            "Be friendly, accurate, detailed, and remember previous messages from this conversation."
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
        chat_history[user_id] = history

    latest_keywords = [
        "latest",
        "today",
        "current",
        "news",
        "live",
        "weather",
        "score",
        "price",
        "breaking",
        "update",
        "aaj",
        "abhi",
        "news",
        "taaza"
    ]

    web_context = ""

    if any(word in message.lower() for word in latest_keywords):
        web_context = search_web(message)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    messages.extend(history)

    if web_context:
        messages.append({
            "role": "system",
            "content":
            "Latest Web Search Results:\n\n" + web_context
        })

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7
    }

    try:
        r = requests.post(
            GROQ_URL,
            headers=headers,
            json=body,
            timeout=30
        )

        if r.status_code != 200:
            return jsonify({
                "reply": r.text
            })

        result = r.json()

        reply = result["choices"][0]["message"]["content"]

        history.append({
            "role": "assistant",
            "content": reply
        })

        chat_history[user_id] = history

        return jsonify({
            "reply": reply
        })

    except Exception as e:
        return jsonify({
            "reply": str(e)
        })
        @app.route("/history", methods=["POST"])
def history():
    data = request.get_json()

    user_id = data.get("user_id", "default")

    return jsonify(chat_history[user_id])


@app.route("/clear", methods=["POST"])
def clear_chat():
    data = request.get_json()

    user_id = data.get("user_id", "default")

    chat_history[user_id] = []

    return jsonify({
        "status": "success",
        "message": "Chat history cleared."
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "ai": "UtilityHub AI",
        "memory": True,
        "internet_search": bool(SERPER_API_KEY)
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
