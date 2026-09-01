# Importing respective libraries below
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from flask import Flask, request, jsonify, render_template
from prompts import SYSTEM_PROMPT
import json


# Calling dot env to load the api key from env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Providing the api key to the LLM
client = genai.Client(api_key=api_key)

# giving model name to use
MODEL = "gemini-flash-latest"

# creating the flask app
app = Flask(__name__)

# Initialising Variables
chat_history = []

filled_fields = {
    "age_hair_loss_began": None,
    "duration": None,
    "family_history": None,
    "pattern": None,
    "diagnosed_conditions": None,
    "menstrual_cycle": None,
    "pregnancy_related": None,
    "adult_acne_oily_skin": None,
    "excess_body_facial_hair": None,
    "past_6_months": None,
    "habits": None,
    "products": None,
    "procedures": None,
    "past_treatment_side_effects": None,
    "sample_type": None,
    "consent": None
}

# Simple get call returns the webpage when it loads
@app.route("/")
def index():
    return render_template("index.html")

#  Post Call returns the user typed message in the textbox (received in JSON Format via JS)
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data["message"]
    chat_history.append(
        types.Content(role="user", parts=[types.Part(text=user_message)])
    )
    #  Gemini LLM Call below
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=chat_history,
            config={"system_instruction": SYSTEM_PROMPT}
        )
    except Exception as e:
        error_msg = str(e).lower()
        print("GEMINI ERROR:", str(e))
        if "high demand" in error_msg or "try again later" in error_msg or "temporarily" in error_msg or "429" in error_msg or "resource_exhausted" in error_msg or "quota" in error_msg:
            return jsonify({"reply": "GenoRoot's assistant is taking a short breather 🌿 — you've hit the free tier limit. Please wait a few seconds and try again.", "filled": 0})
        return jsonify({"reply": "Sorry, something went wrong. Please try again.", "filled": 0})

    llm_reply = response.text
    chat_history.append(
        types.Content(role="model", parts=[types.Part(text=llm_reply)])
    )
    if "[FIELDS]" in llm_reply:    
        parts = llm_reply.split("[FIELDS]")
        reply_text = parts[0].strip()
        fields_json = parts[1].replace("[/FIELDS]", "").strip()
        extracted = json.loads(fields_json)
        filled_fields.update({k: v for k, v in extracted.items() if v is not None and k in filled_fields})
        print("LLM Reply:", llm_reply)
        print("Filled fields:", filled_fields)
    else:
        reply_text = llm_reply
        print("LLM Reply:", llm_reply)
        print("Filled fields:", filled_fields)
    filled_count = sum(1 for v in filled_fields.values() if v is not None)
    return jsonify({"reply": reply_text, "filled": filled_count})
    
#  Post Call confirming that all details received
@app.route("/submit", methods=["POST"])
def submit():
    # Check for any fields still None before saving
    missing = [k for k, v in filled_fields.items() if v is None]
    if missing:
        return jsonify({
            "status": "incomplete",
            "missing_fields": missing,
            "reply": f"Apologies — it seems a few details didn't get captured properly. Could you help me out with these once more?"
        })
    # All fields filled — write to file
    with open("intake_result.json", "w") as f:
        json.dump(filled_fields, f, indent=2)
    return jsonify({"status": "saved", "filled_fields": filled_fields})

# Reset route — clears session state for a new conversation
@app.route("/reset", methods=["POST"])
def reset():
    global chat_history
    chat_history = []
    for key in filled_fields:
        filled_fields[key] = None
    return jsonify({"status": "reset"})

# run the app
if __name__ == "__main__":
    app.run(debug=True)
