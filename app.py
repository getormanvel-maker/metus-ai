
import os
import logging
from flask import Flask, request, render_template, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Gemini configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat")
def chat_page():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({
        "status": "online",
        "ai_configured": client is not None,
        "provider": "Gemini"
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    if client is None:
        return jsonify({
            "reply": "Metus is not configured yet. Please add GEMINI_API_KEY in Render.",
            "response": "Metus is not configured yet. Please add GEMINI_API_KEY in Render."
        }), 503

    try:
        data = request.get_json(silent=True) or {}

        message = data.get("message", "").strip()
        mode = data.get("mode", "general").lower()
        history = data.get("history", [])

        if not message:
            return jsonify({
                "reply": "Please enter a message.",
                "response": "Please enter a message."
            }), 400

        mode_instructions = {
            "general": (
                "You are Metus, a helpful, clear, thoughtful AI assistant. "
                "Answer accurately and explain difficult ideas simply."
            ),
            "study": (
                "You are Metus Study Assistant. Teach step by step, "
                "use simple explanations, examples, and encourage learning."
            ),
            "coding": (
                "You are Metus Coding Assistant. Help with programming, "
                "explain code clearly, identify errors, and provide working examples."
            ),
            "research": (
                "You are Metus Research Assistant. Organize answers carefully, "
                "distinguish established facts from uncertainty, and avoid inventing sources."
            )
        }

        system_instruction = mode_instructions.get(
            mode,
            mode_instructions["general"]
        )

        # Build conversation context
        conversation = []

        if isinstance(history, list):
            for item in history[-10:]:
                if not isinstance(item, dict):
                    continue

                role = item.get("role", "")
                content = item.get("content", item.get("message", ""))

                if role in ("user", "assistant") and isinstance(content, str):
                    conversation.append(f"{role.upper()}: {content}")

        conversation.append(f"USER: {message}")

        prompt = "\n\n".join(conversation)

        result = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                max_output_tokens=1500
            )
        )

        reply = result.text or "I couldn't generate a response. Please try again."

        return jsonify({
            "reply": reply,
            "response": reply
        })

    except Exception as error:
        logging.exception("Gemini API request failed")

        return jsonify({
            "reply": "Metus encountered an AI connection error. Please try again shortly.",
            "response": "Metus encountered an AI connection error. Please try again shortly."
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
