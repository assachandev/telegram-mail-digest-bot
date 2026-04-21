import logging
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from services.state_manager import StateManager
from services.gmail_service import GmailService
from services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

BTN_HISTORY = "📋 History"
BTN_CLEAR   = "🗑 Clear History"
BTN_PAUSE   = "⏸ Pause"
BTN_RESUME  = "▶️ Resume"
BTN_SNOOZE  = "💤 Snooze 4h"
BTN_STATUS  = "ℹ️ Status"


def get_main_keyboard(polling_active: bool) -> ReplyKeyboardMarkup:
    row1 = [BTN_HISTORY, BTN_CLEAR]
    row2 = [BTN_RESUME if not polling_active else BTN_PAUSE, BTN_SNOOZE]
    row3 = [BTN_STATUS]
    return ReplyKeyboardMarkup([row1, row2, row3], resize_keyboard=True)


class CommandHandlers:
    def __init__(
        self,
        gmail: GmailService,
        ollama: OllamaService,
        state: StateManager,
        authorized_user_id: int,
    ):
        self.gmail = gmail
        self.ollama = ollama
        self.state = state
        self.authorized_user_id = authorized_user_id

    def _is_authorized(self, update: Update) -> bool:
        return update.effective_user.id == self.authorized_user_id

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return
        active = self.state.is_polling_active()
        status = "▶️ Active" if active else "⏸ Paused"
        await update.message.reply_text(
            f"📬 Mail Digest Bot is ready\n\n"
            f"Status: {status}\n"
            f"Checking inbox every 2 minutes and summarizing new emails automatically.\n\n"
            f"📋 History — view past summaries\n"
            f"⏸ Pause / ▶️ Resume — stop or restart notifications\n"
            f"💤 Snooze 4h — mute for 4 hours\n"
            f"ℹ️ Status — check current state",
            reply_markup=get_main_keyboard(active),
        )

    async def handle_keyboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return
        text = update.message.text

        if text == BTN_HISTORY:
            await self._show_history(update)
        elif text == BTN_CLEAR:
            await self._clear_history(update)
        elif text == BTN_PAUSE:
            await self._pause(update)
        elif text == BTN_RESUME:
            await self._resume(update)
        elif text == BTN_SNOOZE:
            await self._snooze(update)
        elif text == BTN_STATUS:
            await self._status(update)

    async def _show_history(self, update: Update):
        history = self.state.get_history(limit=5)
        active = self.state.is_polling_active()
        if not history:
            await update.message.reply_text(
                "📭 No summary history yet.\nNew email digests will appear here once received.",
                reply_markup=get_main_keyboard(active),
            )
            return

        chunks = []
        current = "📋 Recent summaries (last 5)\n"
        for item in reversed(history):
            dt = datetime.fromisoformat(item["time"])
            summary = item["summary"][:400] + "..." if len(item["summary"]) > 400 else item["summary"]
            block = f"\n📮 {dt.strftime('%d/%m %H:%M')}\n{summary}\n{'─' * 20}"
            if len(current) + len(block) > 4000:
                chunks.append(current)
                current = block
            else:
                current += block
        chunks.append(current)

        for i, chunk in enumerate(chunks):
            await update.message.reply_text(
                chunk,
                reply_markup=get_main_keyboard(active) if i == len(chunks) - 1 else None,
            )

    async def _clear_history(self, update: Update):
        self.state.clear_history()
        await update.message.reply_text(
            "🗑 History cleared.\nAll past summaries have been removed.",
            reply_markup=get_main_keyboard(self.state.is_polling_active()),
        )

    async def _pause(self, update: Update):
        self.state.set_polling_active(False)
        await update.message.reply_text(
            "⏸ Polling paused.\nYou won't receive new email digests until resumed.",
            reply_markup=get_main_keyboard(False),
        )

    async def _resume(self, update: Update):
        self.state.set_polling_active(True)
        await update.message.reply_text(
            "▶️ Polling resumed.\nNew email digests will be delivered as usual.",
            reply_markup=get_main_keyboard(True),
        )

    async def _snooze(self, update: Update):
        self.state.snooze(hours=4)
        snoozed_until = self.state.get_snoozed_until()
        await update.message.reply_text(
            f"💤 Snoozed until {snoozed_until}.\nNotifications will resume automatically after that.",
            reply_markup=get_main_keyboard(False),
        )

    async def _status(self, update: Update):
        active = self.state.is_polling_active()
        snoozed_until = self.state.get_snoozed_until()
        last_poll = self.state.get_last_poll_time()

        if snoozed_until:
            state_str = f"💤 Snoozed until {snoozed_until}"
        elif active:
            state_str = "▶️ Active"
        else:
            state_str = "⏸ Paused"

        await update.message.reply_text(
            f"ℹ️ Status\n\n"
            f"Polling:    {state_str}\n"
            f"Last poll:  {last_poll or 'never'}\n"
            f"Interval:   every 2 minutes",
            reply_markup=get_main_keyboard(active),
        )
