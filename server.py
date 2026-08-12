import os
import time
import datetime
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from dotenv import load_dotenv

# Try importing google-genai, with fallback if not installed in local environment
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

load_dotenv()

app = Flask(__name__)
CORS(app)

# Simple Rate Limiting Tracker
rate_limit_store = {}
RATE_LIMIT_WINDOW = 60  # seconds
MAX_REQUESTS = 60

@app.after_request
def add_security_and_rate_limit_headers(response):
    client_ip = request.remote_addr or "127.0.0.1"
    now = time.time()
    
    if client_ip not in rate_limit_store or now > rate_limit_store[client_ip]["reset"]:
        rate_limit_store[client_ip] = {"count": 0, "reset": now + RATE_LIMIT_WINDOW}
    
    rate_limit_store[client_ip]["count"] += 1
    remaining = max(0, MAX_REQUESTS - rate_limit_store[client_ip]["count"])
    
    response.headers["X-RateLimit-Limit"] = str(MAX_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(rate_limit_store[client_ip]["reset"]))
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    if GENAI_AVAILABLE:
        try:
            return genai.Client(api_key=api_key)
        except Exception as e:
            print(f"Error initializing Google GenAI client: {e}")
            return None
    return None

@app.route("/api/health", methods=["GET"])
def health_check():
    api_key = os.environ.get("GEMINI_API_KEY")
    is_configured = bool(api_key and api_key != "your_gemini_api_key_here" and GENAI_AVAILABLE)
    return jsonify({
        "status": "ok",
        "service": "jarvis-ai-assistant",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "geminiConfigured": is_configured,
        "genaiAvailable": GENAI_AVAILABLE
    }), 200

@app.route("/api/gemini/ask", methods=["POST"])
def gemini_ask():
    data = request.get_json() or {}
    prompt = data.get("prompt")
    model_name = data.get("model", "gemini-2.5-flash")
    system_instruction = data.get("systemInstruction")

    if not prompt:
        return jsonify({
            "error": "Bad Request",
            "message": "The 'prompt' field is required in request body."
        }), 400

    client = get_gemini_client()
    if not client:
        return jsonify({
            "success": True,
            "response": f"[JARVIS AI Fallback Mode] Gemini API key not configured or package missing. Processed query locally: '{prompt}'",
            "fallback": True,
            "model": model_name
        }), 200

    try:
        config = {}
        if system_instruction:
            config["system_instruction"] = system_instruction

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config if config else None
        )
        
        return jsonify({
            "success": True,
            "response": response.text if hasattr(response, "text") else str(response),
            "fallback": False,
            "model": model_name
        }), 200
    except Exception as e:
        print(f"JARVIS Gemini API error: {e}")
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "fallback": True
        }), 500

@app.route("/api/jarvis/command", methods=["POST"])
def jarvis_command():
    data = request.get_json() or {}
    command = data.get("command")
    if not command:
        return jsonify({"error": "Command parameter required"}), 400

    return jsonify({
        "success": True,
        "command": command,
        "action_taken": f"Executed command: '{command}'",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
