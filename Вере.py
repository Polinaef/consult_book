from __future__ import annotations
import logging
import os
from datetime import datetime, timezone, timedelta
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import gspread
from google.oauth2.service_account import Credentials
import json

# Получаем переменные окружения
BOT_TOKEN = os.getenv('BOT_TOKEN', '8419017530:AAE5L-60pcl0xq77JMsHCczy_jC5ctP7Ta8')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '10nzYJJ0d8GU23hwWf_rzu6_GjgIFqegeJS_oMmVSm6o')

# Если есть переменная окружения с credentials, используем её
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS')
if GOOGLE_CREDENTIALS_JSON:
    # Создаем временный файл из переменной окружения
    with open('temp_credentials.json', 'w') as f:
        f.write(GOOGLE_CREDENTIALS_JSON)
    SERVICE_ACCOUNT_FILE = 'temp_credentials.json'
else:
    SERVICE_ACCOUNT_FILE = "angelic-tracer-465313-t9-27151af1e09d.json"

# ... остальной код без изменений ...

def main():
    # Настройка логирования для облака
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting bot...")
    
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Добавление обработчиков
        app.add_handler(MessageHandler(filters.Regex(f"^({BUTTON_CONSULT}|{BUTTON_BOOK}|{BUTTON_QUESTION})$"), handle_client_type_selection))
        app.add_handler(MessageHandler(filters.Regex(f"^({CONTACT_TELEGRAM}|{CONTACT_WHATSAPP})$"), handle_contact_selection))
        app.add_handler(MessageHandler(filters.Regex(f"^({YES}|{NO})$"), handle_yes_no_selection))
        app.add_handler(MessageHandler(filters.Regex(f"^({DELIVERY_CDEK}|{DELIVERY_YANDEX})$"), handle_delivery_selection))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message))

        # Запуск бота
        logger.info("Bot is running...")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == "__main__":
    main()
