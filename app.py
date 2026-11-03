import os
from flask import Flask, render_template, request, jsonify
from groq import Groq

app = Flask(__name__)

APP_NAME = os.getenv("APP_NAME", "Metus")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


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
        "app": APP_NAME,
        "ai_configured": client is not None
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    if client is None:
        return jsonify({
            "error": "Metus is not configured yet. Add the GROQ_API_KEY in Render."
        }), 503

    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    if len(message) > 12000:
        return jsonify({"error": "Your message is too long."}), 400

    mode = data.get("mode", "general")

    mode_instructions = {
        "general": "You are Metus, a helpful and thoughtful AI assistant.",
        "study": "You are Metus, a patient study coach. Explain concepts clearly and help the student learn.",
        "coding": "You are Metus, a careful programming assistant. Explain code and help debug it.",
        "research": "You are Metus, a research assistant. Be accurate and clearly distinguish facts from uncertainty."
    }

    system_prompt = mode_instructions.get(
        mode,
        mode_instructions["general"]
    )

    try:
        result = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        reply = result.choices[0].message.content

        return jsonify({"reply": reply})

    except Exception as error:
        app.logger.exception("Metus AI request failed")
        return jsonify({
            "error": "Metus couldn't get a response. Please try again."
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=False
    )