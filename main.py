"""Main entry point for the Telegram Group Protector Bot."""

import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ChatMemberHandler,
)

# Import configuration and command modules
import config
from commands import protection, locks
from helpers import decorators # Although decorators are used within commands, importing here isn't strictly needed unless used directly

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    user = update.effective_user
    owner_info = f"Owner: {config.OWNER_USERNAME}"
    channel_info = f"Channel: {config.CHANNEL_USERNAME}"
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I am your group protection bot.

{owner_info}
{channel_info}

Use /help to see available commands.",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message when the /help command is issued."""
    help_text = (
        "**أوامر الحماية الأساسية (للمشرفين):**\n"
        "`/kick` [بالرد أو ID]: طرد عضو (يبقى في سجل المحظورين مؤقتاً). \n"
        "`/ban` [بالرد أو ID]: حظر عضو نهائياً.\n"
        "`/unban` [ID]: إلغاء حظر عضو.\n"
        "`/mute` [بالرد أو ID]: كتم عضو (منع من إرسال الرسائل).\n"
        "`/unmute` [بالرد أو ID]: إلغاء كتم عضو.\n"
        "\n**أوامر القفل (للمشرفين):**\n"
        "`/lock <type>`: قفل ميزة معينة (links, forward, bots, media, all).\n"
        "`/unlock <type>`: فتح ميزة معينة (links, forward, bots, media, all).\n"
        "\n**أوامر عامة:**\n"
        "`/start`: بدء تشغيل البوت.\n"
        "`/help`: عرض رسالة المساعدة هذه.\n"
        f"\n**مالك البوت:** {config.OWNER_USERNAME}\n"
        f"**قناة الدعم:** {config.CHANNEL_USERNAME}"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.error(f"Update \"{update}\" caused error \"{context.error}\"")
    # Optionally notify owner about critical errors
    # if config.OWNER_ID:
    #     await context.bot.send_message(chat_id=config.OWNER_ID, text=f"Bot Error: {context.error}")


def main() -> None:
    """Start the bot."""
    if not config.BOT_TOKEN:
        logger.error("Bot token not found in config.py!")
        return

    # Fetch OWNER_ID if not set (Requires the bot to interact with the owner once)
    # A better approach is to ask the user for their ID or have a command for the owner to register.
    # For now, we'll leave it as None if not manually set in config.py
    if not config.OWNER_ID:
        logger.warning("OWNER_ID not set in config.py. Some owner-specific features might not work.")

    application = Application.builder().token(config.BOT_TOKEN).build()

    # --- Register Command Handlers ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Protection Commands
    application.add_handler(CommandHandler("kick", protection.kick_user))
    application.add_handler(CommandHandler("ban", protection.ban_user))
    application.add_handler(CommandHandler("unban", protection.unban_user))
    application.add_handler(CommandHandler("mute", protection.mute_user))
    application.add_handler(CommandHandler("unmute", protection.unmute_user))

    # Lock Commands
    application.add_handler(CommandHandler("lock", locks.lock_command))
    application.add_handler(CommandHandler("unlock", locks.unlock_command))

    # --- Register Message Handlers ---
    # Handler for message content locks (links, forwards, media)
    # Needs to run on non-command messages in groups
    application.add_handler(MessageHandler(
        filters.ChatType.GROUPS & (~filters.COMMAND) & (filters.TEXT | filters.CAPTION | filters.FORWARDED | filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.DOCUMENT | filters.STICKER | filters.ANIMATION | filters.VOICE | filters.VIDEO_NOTE),
        locks.handle_message_locks
    ), group=1) # group=1 to run after potential command handlers

    # Handler for new members (anti-bot lock)
    application.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.StatusUpdate.NEW_CHAT_MEMBERS,
        locks.handle_new_members
    ), group=2)

    # --- Register Error Handler ---
    application.add_error_handler(error_handler)

    # --- Create requirements.txt ---
    try:
        with open("/home/ubuntu/group_protector_bot/requirements.txt", "w") as f:
            f.write("python-telegram-bot==22.1\n") # Pinning the version used
            f.write("httpx==0.28.1\n")
            f.write("httpcore==1.0.9\n")
        logger.info("Created requirements.txt")
    except Exception as e:
        logger.error(f"Failed to create requirements.txt: {e}")

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot...")
    application.run_polling()


if __name__ == "__main__":
    main()

