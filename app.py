"""
NovaChat - A simple AI Chatbot Web Application
Backend: Flask (Python)

This uses a lightweight rule-based / pattern-matching engine as a base,
with an optional Hugging Face API call for smarter replies. Set the
HF_API_TOKEN environment variable to enable it — see README.md.
"""

import os
import random
import re
from datetime import datetime
from dotenv import load_dotenv

from flask import Flask, render_template, request, jsonify, session
# from langchain_huggingface import ChathuggingFace, HuggingFaceEndpoint

load_dotenv()

app = Flask(__name__)
app.secret_key = "novachat-dev-secret-change-me"  # needed for session-based chat history

# ---------------------------------------------------------------------------
# Hugging Face setup (optional)
# ---------------------------------------------------------------------------
# 1. Create a free account at https://huggingface.co
# 2. Go to https://huggingface.co/settings/tokens and create a token
#    ("fine-grained" type, with "Make calls to Inference Providers" checked)
# 3. Set it as an environment variable named HUGGINGFACEHUB_ACCESS_TOKEN (don't paste it
#    directly into this file if you plan to share or commit your code)
# 4. pip install huggingface_hub
#
# Windows (PowerShell):   $env:HUGGINGFACEHUB_ACCESS_TOKEN = "hf_your_token_here"
# Windows (cmd.exe):      set HUGGINGFACEHUB_ACCESS_TOKEN=hf_your_token_here
# macOS/Linux:            export HUGGINGFACEHUB_ACCESS_TOKEN=hf_your_token_here

HF_API_TOKEN = os.environ.get("HUGGINGFACEHUB_ACCESS_TOKEN")
HF_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

# hf_client = None
if HF_API_TOKEN:
    try:
        from huggingface_hub import InferenceClient
        hf_client = InferenceClient(api_key=HF_API_TOKEN)
    except ImportError:
        print("huggingface_hub not installed — run: pip install huggingface_hub")


# ---------------------------------------------------------------------------
# Chatbot "brain" — simple pattern matching.
# Swap this out for a real API call (OpenAI, etc.) if you want smarter answers.
# ---------------------------------------------------------------------------
RULES = [
    (r"\b(hi|hello|hey|yo|sup)\b", [
        "Hey there! 👋 How can I help you today?",
        "Hello! What's on your mind?",
        "Hi! I'm NovaChat. Ask me anything.",
    ]),
    (r"\b(how are you|how's it going|how r u)\b", [
        "I'm just a bunch of code, but I'm running smoothly! How about you?",
        "Doing great, thanks for asking! What can I do for you?",
    ]),
    (r"\b(your name|who are you)\b", [
        "I'm NovaChat, a simple AI chatbot built with Flask and JavaScript.",
        "You can call me NovaChat! Nice to meet you.",
    ]),
    (r"\b(bye|goodbye|see you|exit|quit)\b", [
        "Goodbye! Come back anytime. 👋",
        "See you later! Have a great day.",
    ]),
    (r"\b(thank|thanks|thx)\b", [
        "You're welcome! 😊",
        "Anytime! Let me know if you need anything else.",
    ]),
    (r"\b(joke|funny)\b", [
        "Why do programmers prefer dark mode? Because light attracts bugs. 🐛",
        "I told my computer I needed a break, and now it won't stop sending me KitKats.",
    ]),
    (r"\b(time)\b", [
        f"I don't track real time yet, but right now the server thinks it's {datetime.now().strftime('%H:%M')}.",
    ]),
    (r"\b(help|what can you do)\b", [
        "I can chat with you, tell a joke, or just keep you company. Try saying 'joke' or 'hello'!",
    ]),
    (r"\b(flask|python|backend)\b", [
        "This app's backend is built with Python and Flask, serving replies over a simple API.",
    ]),
]

FALLBACKS = [
    "That's interesting — tell me more!",
    "I'm not sure I follow, but I'm listening.",
    "Hmm, can you rephrase that?",
    "Got it. What else is on your mind?",
    "I'm still learning — could you say that differently?",
]


def get_hf_reply(user_message: str) -> str | None:
    """Ask the Hugging Face Inference API for a reply. Returns None on failure."""
    if not hf_client:
        return None
    try:
        completion = hf_client.chat.completions.create(
            model=HF_MODEL,
            messages=[
                {"role": "system", "content": "You are NovaChat, a friendly, concise chatbot."},
                {"role": "user", "content": user_message},
            ],
            max_tokens=120,
        )
        return completion.choices[0].message.content
    except Exception as exc:  # noqa: BLE001 - want to fall back on any API issue
        print(f"Hugging Face API error: {exc}")
        return None


def get_bot_reply(user_message: str) -> str:
    text = user_message.lower().strip()

    # Quick built-in replies for common small talk (fast, no API call needed)
    for pattern, responses in RULES:
        if re.search(pattern, text):
            return random.choice(responses)

    # If a Hugging Face token is configured, let the AI model answer
    hf_reply = get_hf_reply(user_message)
    if hf_reply:
        return hf_reply

    # Otherwise fall back to a generic response
    return random.choice(FALLBACKS)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat")
def chat_page():
    return render_template("chat.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    bot_reply = get_bot_reply(user_message)

    # keep a lightweight server-side history (per browser session)
    history = session.get("history", [])
    history.append({"role": "user", "text": user_message})
    history.append({"role": "bot", "text": bot_reply})
    session["history"] = history[-40:]  # cap history length

    return jsonify({"reply": bot_reply})


@app.route("/api/history")
def api_history():
    return jsonify({"history": session.get("history", [])})


@app.route("/api/history/clear", methods=["POST"])
def api_history_clear():
    session["history"] = []
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True)
