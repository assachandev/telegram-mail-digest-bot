import json
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StateManager:
    def __init__(self, state_file="state.json"):
        self.state_file = state_file
        self.state = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"State file corrupted, resetting: {e}")
        return {
            "processed_emails": [],
            "polling_active": True,
            "snoozed_until": None,
            "last_poll_time": None,
            "history": [],
        }

    def _save(self):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    # ── Processed emails ──────────────────────────────────────────────────────

    def is_processed(self, email_id: str) -> bool:
        return email_id in self.state["processed_emails"]

    def mark_processed(self, email_id: str):
        if email_id not in self.state["processed_emails"]:
            self.state["processed_emails"].append(email_id)
            self.state["processed_emails"] = self.state["processed_emails"][-1000:]
            self._save()

    # ── Polling state ─────────────────────────────────────────────────────────

    def is_polling_active(self) -> bool:
        snoozed_until = self.state.get("snoozed_until")
        if snoozed_until:
            if datetime.now() < datetime.fromisoformat(snoozed_until):
                return False
            else:
                self.state["snoozed_until"] = None
                self._save()
        return self.state.get("polling_active", True)

    def set_polling_active(self, active: bool):
        self.state["polling_active"] = active
        self.state["snoozed_until"] = None
        self._save()

    def snooze(self, hours: int):
        self.state["snoozed_until"] = (datetime.now() + timedelta(hours=hours)).isoformat()
        self._save()

    def get_snoozed_until(self) -> str | None:
        snoozed = self.state.get("snoozed_until")
        if not snoozed:
            return None
        if datetime.now() >= datetime.fromisoformat(snoozed):
            self.state["snoozed_until"] = None
            self._save()
            return None
        dt = datetime.fromisoformat(snoozed)
        return dt.strftime("%d/%m %H:%M")

    # ── Poll time ─────────────────────────────────────────────────────────────

    def update_last_poll_time(self):
        self.state["last_poll_time"] = datetime.now().isoformat()
        self._save()

    def get_last_poll_time(self) -> str | None:
        t = self.state.get("last_poll_time")
        if not t:
            return None
        return datetime.fromisoformat(t).strftime("%d/%m %H:%M")

    # ── History ───────────────────────────────────────────────────────────────

    def add_history(self, summary: str, source: str):
        self.state["history"].append({
            "time": datetime.now().isoformat(),
            "source": source,
            "summary": summary,
        })
        self.state["history"] = self.state["history"][-20:]
        self._save()

    def get_history(self, limit=5) -> list[dict]:
        return self.state["history"][-limit:]

    def clear_history(self):
        self.state["history"] = []
        self._save()
