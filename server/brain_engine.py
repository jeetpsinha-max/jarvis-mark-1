import sqlite3
import os
import time
import json
from typing import List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jarvis_knowledge.db")

class BrainEngine:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT NOT NULL,
                    tags TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

        # Seed initial core knowledge if empty
        if self.count_knowledge() == 0:
            self.seed_defaults()

    def seed_defaults(self):
        defaults = [
            ("user_profile", "user_name", "Jeet Sinha", "identity,user"),
            ("user_profile", "role", "Principal Engineer & AI Architect", "identity,role"),
            ("system_rules", "assistant_name", "J.A.R.V.I.S.", "identity,ai"),
            ("system_rules", "creator", "Jeet Sinha / Google AI Studio", "identity,creator"),
            ("project_info", "workspace_location", "d:\\MyProfile\\Desktop", "workspace,config"),
            ("project_info", "ai_model", "Google Gemini 3.6 Flash", "ai,model"),
            ("capabilities", "voice_recognition", "Enabled via Web Speech API & Python SpeechEngine", "feature,voice"),
            ("capabilities", "biometrics", "Enabled via OpenCV Face ID Authentication", "feature,security"),
            ("capabilities", "telemetry", "Real-time CPU, RAM, Battery, and Neural Memory HUD", "feature,telemetry")
        ]
        for cat, key, val, tags in defaults:
            self.learn_fact(cat, key, val, tags)

    def learn_fact(self, category: str, key: str, value: str, tags: str = "") -> Dict[str, Any]:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO knowledge (category, key, value, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    category=excluded.category,
                    value=excluded.value,
                    tags=excluded.tags,
                    updated_at=excluded.updated_at
            """, (category, key, value, tags, now, now))
            conn.commit()
        return {"category": category, "key": key, "value": value, "status": "remembered"}

    def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_str = f"%{query.lower()}%"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, key, value, tags, updated_at FROM knowledge
                WHERE LOWER(key) LIKE ? OR LOWER(value) LIKE ? OR LOWER(category) LIKE ? OR LOWER(tags) LIKE ?
                ORDER BY updated_at DESC LIMIT ?
            """, (query_str, query_str, query_str, query_str, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_all_knowledge(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, category, key, value, tags, updated_at FROM knowledge ORDER BY id ASC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def count_knowledge(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM knowledge")
            return cursor.fetchone()[0]

    def get_context_for_prompt(self, prompt: str) -> str:
        results = self.search_knowledge(prompt, limit=4)
        if not results:
            # Fallback to general user profile facts
            results = self.search_knowledge("user", limit=3)

        if not results:
            return ""

        facts_str = "\n".join([f"- [{r['category'].upper()}] {r['key']}: {r['value']}" for r in results])
        return f"\n\n[J.A.R.V.I.S. NEURAL KNOWLEDGE RETRIEVAL]:\n{facts_str}\n"

brain = BrainEngine()
