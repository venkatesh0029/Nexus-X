import sqlite3
import json
import os
import logging

class PlanStore:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "..", "plan_store.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS plan_store
                         (request TEXT PRIMARY KEY, plan_json TEXT)''')
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Failed to initialize PlanStore DB: {e}")

    def get_plan(self, request: str):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            # Exact match, ignore case/whitespace
            c.execute("SELECT plan_json FROM plan_store WHERE request = ?", (request.strip().lower(),))
            row = c.fetchone()
            conn.close()
            if row:
                logging.info(f"PlanStore hit for request: '{request}'")
                return json.loads(row[0])
        except Exception as e:
            logging.error(f"Plan store read error: {e}")
        return None

    def save_plan(self, request: str, plan: list):
        if not plan:
            return
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO plan_store (request, plan_json) VALUES (?, ?)", 
                      (request.strip().lower(), json.dumps(plan)))
            conn.commit()
            conn.close()
            logging.info(f"PlanStore saved plan for request: '{request}'")
        except Exception as e:
            logging.error(f"Plan store write error: {e}")

plan_store = PlanStore()
