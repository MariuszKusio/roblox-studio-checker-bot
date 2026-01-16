import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from evaluator import evaluate_hardware


# =========================
# KONFIGURACJA
# =========================

TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8080))

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set")
if not WEBHOOK_URL:
    raise RuntimeError("WEBHOOK_URL is not set")


# =========================
# TEKSTY
# =========================

MAIN_MENU = (
    "📋 *Menu główne*\n\n"
    "Wpisz numer wybranej pozycji:\n\n"
    "1️⃣ Sprawdź specyfikację komputera pod Roblox Studio\n"
    "2️⃣ Jak dokładnie sprawdzić wymagania?\n"
    "3️⃣ Specyficzne przypadki (macOS, ChromeOS)"
)

HELP_TEXT = (
    "🤖 *Pomoc*\n\n"
    "Komendy:\n"
    "• /start – uruchom bota\n"
    "• /menu – pokaż menu\n"
    "• /help – pomoc\n"
)

CHECK_PROMPT = (
    "🖥️ *Sprawdzanie sprzętu*\n\n"
    "Podaj model procesora i ilość RAM.\n"
    "Przykład:\n"
    "`i5-10400F, 8GB RAM`"
)

OS_MENU = (
    "💻 *Wybierz system operacyjny:*\n\n"
    "1️⃣ Windows\n"
    "2️⃣ macOS"
)

SPECIFIC_INFO = (
    "ℹ️ *Specyficzne przypadki:*\n\n"
    "• Tablety nie nadają się do Roblox Studio\n"
    "• ChromeOS nie obsługuje Roblox Studio\n"
    "• Wymagany jest system desktopowy\n"
)


# =========================
# KOMENDY
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(MAIN_MENU, parse_mode="Markdown")


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(MAIN_MENU, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


# =========================
# WIADOMOŚCI
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get("mode")

    if mode == "check_hardware":
        result = evaluate_hardware(text)
        context.user_data.clear()
        await update.message.reply_text(result)
        await update.message.reply_text(MAIN_MENU, parse_mode="Markdown")
        return

    if mode == "choose_os":
        if text == "1":
            await update.message.reply_text(
                "🪟 *Windows*\n\nRoblox Studio działa na Windows 10 i 11.",
                parse_mode="Markdown",
            )
        elif text == "2":
            await update.message.reply_text(
                "🍎 *macOS*\n\nRoblox Studio działa na macOS (Intel / Apple Silicon).",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text("❌ Wybierz 1 lub 2.")
            return

        context.user_data.clear()
        await update.message.reply_text(MAIN_MENU, parse_mode="Markdown")
        return

    if text == "1":
        context.user_data["mode"] = "check_hardware"
        await update.message.reply_text(CHECK_PROMPT, parse_mode="Markdown")
        return

    if text == "2":
        context.user_data["mode"] = "choose_os"
        await update.message.reply_text(OS_MENU, parse_mode="Markdown")
        return

    if text == "3":
        await update.message.reply_text(SPECIFIC_INFO, parse_mode="Markdown")
        await update.message.reply_text(MAIN_MENU, parse_mode="Markdown")
        return

    await update.message.reply_text(
        "❓ Nie rozumiem.\nWpisz /menu, aby zobaczyć opcje.",
        parse_mode="Markdown",
    )


# =========================
# APLIKACJA
# =========================

application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("menu", menu))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


if __name__ == "__main__":
    print("🤖 Bot uruchomiony (webhook)")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=f"{WEBHOOK_URL}/webhook",
    )
