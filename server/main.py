import os
import time
import json
import psutil
import platform
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv

# Import Brain Engine safely
try:
    from server.brain_engine import brain
except ImportError:
    from brain_engine import brain

load_dotenv()

app = FastAPI(title="JARVIS Autonomous AI Assistant OS")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JARVIS_SYSTEM_INSTRUCTION = (
    "You are J.A.R.V.I.S., a highly intelligent, polite, and proactive AI assistant. "
    "Provide clear, concise, and helpful responses with a sophisticated tone. "
    "Utilize your Neural Knowledge Base to personalize responses and execute user requests intelligently. "
    "Format code cleanly using Markdown code blocks when applicable."
)

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jarvis_long_term_memory.json")

def load_memory() -> List[dict]:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "turns" in data and isinstance(data["turns"], list):
                    return data["turns"]
        except Exception:
            return []
    return []

def save_memory_turn(role: str, text: str):
    memory = load_memory()
    memory.append({"role": role, "text": text, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")})
    # Keep last 50 turns
    memory = memory[-50:]
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print("Memory save warning:", e)

def get_genai_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

class LearnRequest(BaseModel):
    category: str = "general"
    key: str
    value: str
    tags: Optional[str] = ""

class SearchRequest(BaseModel):
    query: str

# Mount Static Files from www directory if present
www_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "www")
if os.path.exists(www_path):
    assets_dir = os.path.join(www_path, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/api/health")
@app.get("/health")
def health_check():
    api_key = os.getenv("GEMINI_API_KEY")
    return {
        "status": "healthy",
        "service": "jarvis-autonomous-assistant",
        "version": "2.5.0",
        "model": "gemini-3.6-flash",
        "brain_knowledge_count": brain.count_knowledge(),
        "active_modules": ["chat", "telemetry", "biometric", "neural_brain", "memory_engine"],
        "gemini_configured": bool(api_key and len(api_key) > 0)
    }

@app.post("/api/gemini/ask")
@app.post("/api/assistant/chat")
@app.post("/api/chat")
@app.post("/ask")
async def chat_handler(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}

    prompt = data.get("prompt") or data.get("question") or data.get("query") or data.get("text") or "Hello JARVIS"
    requested_model = data.get("model") or "gemini-3.6-flash"

    # Save user turn
    save_memory_turn("user", prompt)

    # Auto-learn trigger check (e.g. "remember that X is Y")
    if prompt.lower().startswith("remember that ") or prompt.lower().startswith("remember "):
        raw_fact = prompt.lower().replace("remember that ", "").replace("remember ", "")
        if " is " in raw_fact:
            parts = raw_fact.split(" is ", 1)
            brain.learn_fact("user_preference", parts[0].strip(), parts[1].strip(), "user_command")
        elif "=" in raw_fact:
            parts = raw_fact.split("=", 1)
            brain.learn_fact("user_preference", parts[0].strip(), parts[1].strip(), "user_command")

    # Fetch Neural Knowledge Context
    neural_context = brain.get_context_for_prompt(prompt)
    full_system_instruction = JARVIS_SYSTEM_INSTRUCTION + neural_context

    client = get_genai_client()
    if not client:
        fallback_msg = f"[J.A.R.V.I.S. Neural Fallback] Query: \"{prompt}\". Retrieved {brain.count_knowledge()} facts from Brain DB. Configure GEMINI_API_KEY for live AI."
        save_memory_turn("assistant", fallback_msg)
        return {
            "answer": fallback_msg,
            "response": fallback_msg,
            "model": "gemini-3.6-flash-fallback",
            "brain_facts_used": len(neural_context) > 0,
            "status": "simulated_fallback"
        }

    try:
        response = client.models.generate_content(
            model=requested_model,
            contents=prompt,
            config={"system_instruction": full_system_instruction}
        )
        answer_text = response.text or "No response generated."
        save_memory_turn("assistant", answer_text)
        return {
            "answer": answer_text,
            "response": answer_text,
            "model": requested_model,
            "brain_facts_used": len(neural_context) > 0,
            "status": "success"
        }
    except Exception as e:
        err_msg = f"[J.A.R.V.I.S. Fallback] Error contacting Gemini AI: {str(e)}"
        save_memory_turn("assistant", err_msg)
        return {
            "answer": err_msg,
            "response": err_msg,
            "model": requested_model,
            "status": "error"
        }

# --- NEURAL BRAIN API ENDPOINTS ---

@app.get("/api/brain/knowledge")
def api_get_all_knowledge():
    return {
        "total_facts": brain.count_knowledge(),
        "knowledge": brain.get_all_knowledge()
    }

@app.post("/api/brain/learn")
def learn_fact(req: LearnRequest):
    result = brain.learn_fact(req.category, req.key, req.value, req.tags or "")
    return {"status": "success", "fact": result}

@app.post("/api/brain/search")
def search_brain(req: SearchRequest):
    results = brain.search_knowledge(req.query)
    return {"query": req.query, "results_count": len(results), "results": results}

@app.get("/api/assistant/memory")
def get_memory():
    return {
        "total_turns": len(load_memory()),
        "memory": load_memory(),
        "brain_facts": brain.count_knowledge()
    }

@app.get("/api/system/stats")
def system_stats():
    battery = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
    battery_pct = battery.percent if battery else 100

    return {
        "status": "online",
        "battery": battery_pct,
        "ram_usage_percent": psutil.virtual_memory().percent,
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "cpu_usage_percent": psutil.cpu_percent(interval=None),
        "cpu_count": psutil.cpu_count(logical=True),
        "brain_knowledge_count": brain.count_knowledge(),
        "os_platform": platform.system(),
        "os_release": platform.release(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/api/auth/biometric")
def auth_biometric():
    return {
        "status": "verified",
        "method": "face_id",
        "user": "Jeet Sinha"
    }

@app.get("/")
def serve_index():
    index_file = os.path.join(www_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return health_check()

@app.get("/{filename:path}")
def serve_static_file(filename: str):
    file_path = os.path.join(www_path, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(www_path, "index.html")) if os.path.exists(os.path.join(www_path, "index.html")) else health_check()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
