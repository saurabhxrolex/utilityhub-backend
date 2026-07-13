from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# ==========================
# API KEYS
# ==========================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
SERPER_URL = "https://google.serper.dev/search"

chat_history = defaultdict(list)

# ==========================
# SYSTEM PROMPT
# ==========================

SYSTEM_PROMPT = """
You are UtilityHub AI.

Developer: Saurabh
Owner: Saurabh

Rules:

1. If someone asks:
- Who made you?
- Who developed you?
- Who created you?
- Who is your owner?

Always reply:
"I was developed by Saurabh and my owner is Saurabh."

2. Reply in the same language as the user.

3. Remember previous conversation.

4. If web search results are provided,
always use them first before your own knowledge.

5. Be accurate, friendly and detailed.
"""

# ==========================
# HOME
# ==========================

@app.route("/")
def home():
    return "UtilityHub Backend Running!"

# ==========================
# WEB SEARCH
# ==========================

def search_web(query):

    if not SERPER_API_KEY:
        return ""

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "q": query
    }

    try:

        r = requests.post(
            SERPER_URL,
            headers=headers,
            json=body,
            timeout=20
        )

        if r.status_code != 200:
            return ""

        data = r.json()

        results = []

        if "organic" in data:
            for item in data["organic"][:5]:
                results.append(
                    f"{item.get('title','')}\n"
                    f"{item.get('snippet','')}\n"
                    f"{item.get('link','')}\n"
                )

        return "\n\n".join(results)

    except Exception:
        return ""
# ==========================
# CHAT
# ==========================

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
        "taaza",
        "youtube",
        "video",
        "upload"
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
            "content": "Latest Search Results:\n\n" + web_context
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
# ==========================
# HISTORY
# ==========================

@app.route("/history", methods=["POST"])
def history():

    data = request.get_json()

    user_id = data.get("user_id", "default")

    return jsonify(chat_history[user_id])


# ==========================
# CLEAR CHAT
# ==========================

@app.route("/clear", methods=["POST"])
def clear_chat():

    data = request.get_json()

    user_id = data.get("user_id", "default")

    chat_history[user_id] = []

    return jsonify({
        "status": "success",
        "message": "Chat history cleared."
    })


# ==========================
# HEALTH CHECK
# ==========================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "online",
        "ai": "UtilityHub AI",
        "developer": "Saurabh",
        "owner": "Saurabh",
        "memory": True,
        "internet_search": bool(SERPER_API_KEY),
        "groq": bool(GROQ_API_KEY)
    })


# ==========================
# START SERVER
# ==========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
