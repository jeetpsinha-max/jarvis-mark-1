# Jarvis AI Assistant

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)
![Gemini Live API](https://img.shields.io/badge/Gemini-Live_API-blueviolet)
![OpenCV](https://img.shields.io/badge/OpenCV-Enabled-green)
![Biometric Auth](https://img.shields.io/badge/Auth-Biometric-red)
![PyAudio](https://img.shields.io/badge/Audio-PyAudio-yellow)

## Summary
Advanced AI Virtual Assistant with voice recognition, facial authentication, phone integration, adaptive memory, and system automation.

## Core Features
*   **FastAPI Backend Server:** Robust web backend providing REST APIs for chat, telemetry, and biometrics.
*   **Voice VAD interface:** Real-time voice activity detection and interaction.
*   **Face ID login:** Biometric facial authentication for secure access.
*   **Adaptive Memory:** Context-aware memory system (`adaptive_memory.json`).
*   **Gemini Live API streaming:** Powerful conversational AI with real-time streaming capabilities.
*   **System automation:** Battery reports and system automation scripts.

## Setup Guide
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
2. Activate the environment and install dependencies:
   ```bash
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Set up environment variables in a `.env` file (e.g., Gemini API keys).
4. Run the main script to start Jarvis.
