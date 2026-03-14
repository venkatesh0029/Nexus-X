import sqlite3
import json
import os
import time
from typing import Dict, Any

class AuditLogger:
    """
    Structured JSON logger for all agent actions, tool calls, and security events.
    Appends to SQLite in WAL mode.
    """
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "..", "audit.db")
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS global_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                severity TEXT,
                payload JSON
            )
        ''')
        cursor.execute('PRAGMA journal_mode=WAL;')
        conn.commit()
        conn.close()

    def log_event(self, event_type: str, severity: str, payload: Dict[str, Any]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO global_audit (event_type, severity, payload) VALUES (?, ?, ?)',
            (event_type, severity, json.dumps(payload))
        )
        conn.commit()
        conn.close()

# Global singleton for ease of use
audit_logger = AuditLogger()
