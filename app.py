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
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
SERPER_URL = "https://google.serper.dev/search"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
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
except Exception:
    return ""

# ==========================
# YOUTUBE LATEST VIDEO SEARCH
# ==========================

def search_latest_youtube_video(channel_name):

    if not YOUTUBE_API_KEY:
        return {
            "success": False,
            "error": "YouTube API key is missing."
        }

    params = {
        "part": "snippet",
        "q": channel_name,
        "type": "video",
        "order": "date",
        "maxResults": 5,
        "key": YOUTUBE_API_KEY
    }

    try:
        response = requests.get(
            YOUTUBE_SEARCH_URL,
            params=params,
            timeout=20
        )

        data = response.json()

        if response.status_code != 200:
            return {
                "success": False,
                "error": data
            }

        items = data.get("items", [])

        if not items:
            return {
                "success": False,
                "error": "No YouTube video found."
            }

        channel_words = channel_name.lower().split()
        selected_video = items[0]

        for item in items:
            result_channel = item["snippet"].get(
                "channelTitle", ""
            ).lower()

            if all(word in result_channel for word in channel_words):
                selected_video = item
                break

        video_id = selected_video["id"]["videoId"]
        snippet = selected_video["snippet"]

        return {
            "success": True,
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "published_at": snippet.get("publishedAt", ""),
            "description": snippet.get("description", ""),
            "thumbnail": snippet.get(
                "thumbnails", {}
            ).get("high", {}).get("url", ""),
            "video_url": f"https://www.youtube.com/watch?v={video_id}"
        }

    except requests.RequestException as error:
        return {
            "success": False,
            "error": str(error)
        }


# ==========================
# CHAT
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
youtube_context = ""

if "youtube" in message.lower() or "video" in message.lower():
    yt = search_latest_youtube_video(message)

    if yt["success"]:
        youtube_context = f"""
Latest YouTube Video

Title: {yt['title']}
Channel: {yt['channel']}
Published: {yt['published_at']}
Description: {yt['description']}
Video: {yt['video_url']}
"""
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

    if youtube_context:
        messages.append({
            "role": "system",
            "content": youtube_context
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
