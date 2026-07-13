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

3. Remember previous messages from the current conversation.

4. If web search or YouTube results are provided,
use them before your own knowledge.

5. Never invent a latest video, date, news item, price, score, or link.

6. Be accurate, friendly, and helpful.
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
        response = requests.post(
            SERPER_URL,
            headers=headers,
            json=body,
            timeout=20
        )

        if response.status_code != 200:
            return ""

        data = response.json()
        results = []

        for item in data.get("organic", [])[:5]:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")

            results.append(
                f"Title: {title}\n"
                f"Snippet: {snippet}\n"
                f"Link: {link}"
            )

        return "\n\n".join(results)

    except requests.RequestException:
        return ""


# ==========================
# YOUTUBE SEARCH
# ==========================

def search_latest_youtube_video(search_query):
    if not YOUTUBE_API_KEY:
        return {
            "success": False,
            "error": "YouTube API key is missing."
        }

    params = {
        "part": "snippet",
        "q": search_query,
        "type": "video",
        "order": "date",
        "maxResults": 10,
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
            error_message = (
                data.get("error", {})
                .get("message", "YouTube API request failed.")
            )

            return {
                "success": False,
                "error": error_message
            }

        items = data.get("items", [])

        if not items:
            return {
                "success": False,
                "error": "No YouTube video found."
            }

        selected_video = items[0]

        video_id = selected_video.get("id", {}).get("videoId", "")
        snippet = selected_video.get("snippet", {})

        if not video_id:
            return {
                "success": False,
                "error": "Video ID was not found."
            }

        return {
            "success": True,
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "published_at": snippet.get("publishedAt", ""),
            "description": snippet.get("description", ""),
            "thumbnail": (
                snippet.get("thumbnails", {})
                .get("high", {})
                .get("url", "")
            ),
            "video_url": (
                f"https://www.youtube.com/watch?v={video_id}"
            )
        }

    except requests.RequestException as error:
        return {
            "success": False,
            "error": str(error)
        }
# ==========================
# CHAT API
# ==========================

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    message = data.get("message", "").strip()
    user_id = data.get("user_id", "default")

    if not message:
        return jsonify({
            "reply": "Please enter a message."
        }), 400

    if not GROQ_API_KEY:
        return jsonify({
            "reply": "Groq API key is missing."
        }), 500

    history = chat_history[user_id]

    history.append({
        "role": "user",
        "content": message
    })

    if len(history) > 12:
        history = history[-12:]
        chat_history[user_id] = history

    message_lower = message.lower()

    youtube_keywords = [
        "youtube",
        "latest video",
        "latest upload",
        "today video",
        "today's video",
        "video title",
        "video link",
        "aaj ka video",
        "aaj ki video",
        "लेटेस्ट वीडियो",
        "आज का वीडियो",
        "आज की वीडियो"
    ]

    web_keywords = [
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
        "आज",
        "अभी",
        "ताज़ा"
    ]

    youtube_context = ""
    web_context = ""

    if any(word in message_lower for word in youtube_keywords):
        youtube_result = search_latest_youtube_video(message)

        if youtube_result.get("success"):
            youtube_context = (
                "Verified latest YouTube result:\n"
                f"Title: {youtube_result.get('title', '')}\n"
                f"Channel: {youtube_result.get('channel', '')}\n"
                f"Published: {youtube_result.get('published_at', '')}\n"
                f"Description: {youtube_result.get('description', '')}\n"
                f"Video link: {youtube_result.get('video_url', '')}\n"
                f"Thumbnail: {youtube_result.get('thumbnail', '')}"
            )
        else:
            youtube_context = (
                "YouTube search failed: "
                + str(youtube_result.get("error", "Unknown error"))
            )

    elif any(word in message_lower for word in web_keywords):
        web_context = search_web(message)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    messages.extend(history)

    if youtube_context:
        messages.append({
            "role": "system",
            "content": youtube_context
        })

    if web_context:
        messages.append({
            "role": "system",
            "content": (
                "Verified web search results:\n\n"
                + web_context
            )
        })

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.4
    }

    try:
        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=body,
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({
                "reply": response.text
            }), response.status_code

        result = response.json()

        reply = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "No reply received.")
        )

        history.append({
            "role": "assistant",
            "content": reply
        })

        if len(history) > 12:
            history = history[-12:]

        chat_history[user_id] = history

        return jsonify({
            "reply": reply
        })

    except requests.RequestException as error:
        return jsonify({
            "reply": f"Network error: {str(error)}"
        }), 500

    except Exception as error:
        return jsonify({
            "reply": f"Server error: {str(error)}"
        }), 500


# ==========================
# CHAT HISTORY
# ==========================

@app.route("/history", methods=["POST"])
def history():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id", "default")

    return jsonify(chat_history[user_id])


# ==========================
# CLEAR CHAT
# ==========================

@app.route("/clear", methods=["POST"])
def clear_chat():
    data = request.get_json(silent=True) or {}
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
        "groq": bool(GROQ_API_KEY),
        "internet_search": bool(SERPER_API_KEY),
        "youtube_search": bool(YOUTUBE_API_KEY)
    })


# ==========================
# START SERVER
# ==========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
