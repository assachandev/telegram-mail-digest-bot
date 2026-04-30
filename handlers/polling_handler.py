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
            # Check if Ollama was down and is now back online
            if not state.is_ollama_available() and ollama.is_healthy():
                state.set_ollama_available(True)
                logger.info("Ollama is back online")
                await context.bot.send_message(
                    chat_id=user_id,
                    text="✅ Ollama is back online — resuming email processing.",
                )
            return

        summary = ollama.summarize_emails(new_emails)

        # Ollama was unavailable but is now working again
        if not state.is_ollama_available():
            state.set_ollama_available(True)
            logger.info("Ollama is back online")
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ Ollama is back online — resuming email processing.",
            )

        await context.bot.send_message(
            chat_id=user_id,
            text=f"📮 New emails\n\n{summary}",
        )

        state.add_history(summary, "Gmail")
        for e in new_emails:
            state.mark_processed(f"gmail_{e['id']}")

    except TimeoutError:
        logger.error("Ollama timeout while processing Gmail")
        state.set_ollama_available(False)
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ Ollama timed out — will retry on next cycle.",
        )
    except ConnectionError as e:
        logger.error(f"Ollama connection error: {e}")
        # Mark Ollama as unavailable
        if state.is_ollama_available():
            state.set_ollama_available(False)
            logger.warning("Ollama marked as unavailable")
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Cannot connect to Ollama at this moment. Will keep retrying...",
            )
    except Exception as e:
        logger.error(f"Polling error: {e}", exc_info=True)
