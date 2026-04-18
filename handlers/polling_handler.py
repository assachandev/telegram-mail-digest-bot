import logging
from telegram.ext import CallbackContext

from services.gmail_service import GmailService
from services.ollama_service import OllamaService
from services.state_manager import StateManager

logger = logging.getLogger(__name__)


async def poll_emails(
    context: CallbackContext,
    gmail: GmailService,
    ollama: OllamaService,
    state: StateManager,
    user_id: int,
):
    if not state.is_polling_active():
        return

    state.update_last_poll_time()

    try:
        emails = gmail.fetch_unread_emails(limit=10)
        new_emails = [e for e in emails if not state.is_processed(f"gmail_{e['id']}")]

        if not new_emails:
            return

        summary = ollama.summarize_emails(new_emails)
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📮 New emails\n\n{summary}",
        )

        state.add_history(summary, "Gmail")
        for e in new_emails:
            state.mark_processed(f"gmail_{e['id']}")

    except TimeoutError:
        logger.error("Ollama timeout while processing Gmail")
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ Ollama timed out — skipping this cycle.",
        )
    except ConnectionError as e:
        logger.error(f"Ollama connection error: {e}")
    except Exception as e:
        logger.error(f"Polling error: {e}", exc_info=True)
