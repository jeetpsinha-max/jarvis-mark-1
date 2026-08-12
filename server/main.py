import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Jarvis AI Assistant Backend")

# Initialize Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "DUMMY_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

class ChatRequest(BaseModel):
    prompt: str

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "active_modules": ["chat", "telemetry", "biometric"],
        "model_status": "loaded"
    }

@app.post("/api/assistant/chat")
def chat(request: ChatRequest):
    try:
        response = model.generate_content(request.prompt)
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/stats")
def system_stats():
    return {
        "battery": 85,
        "ram": "16GB",
        "cpu": "Intel Core i7",
        "cpu_usage": "15%"
    }

@app.post("/api/auth/biometric")
def auth_biometric():
    return {
        "status": "verified",
        "method": "face_id"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
