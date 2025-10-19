from __future__ import annotations
import logging
import os
from datetime import datetime, timezone, timedelta
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import gspread
from google.oauth2.service_account import Credentials
import json

# Получаем переменные окружения из Replit Secrets
BOT_TOKEN = os.getenv('BOT_TOKEN', '8419017530:AAE5L-60pcl0xq77JMsHCczy_jC5ctP7Ta8')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '10nzYJJ0d8GU23hwWf_rzu6_GjgIFqegeJS_oMmVSm6o')

# Обработка Google Credentials
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS')
if GOOGLE_CREDENTIALS_JSON:
    # Используем credentials из переменной окружения
    credentials_info = json.loads(GOOGLE_CREDENTIALS_JSON)
    SERVICE_ACCOUNT_INFO = credentials_info
else:
    # Локальная разработка (если нужно)
    SERVICE_ACCOUNT_INFO = None

# Константы кнопок
BUTTON_CONSULT = "Запросить консультацию"
BUTTON_BOOK = "Заказать книгу с автографом"
BUTTON_QUESTION = "Другой вопрос"
CONTACT_TELEGRAM = "Telegram"
CONTACT_WHATSAPP = "WhatsApp"
YES = "Да"
NO = "Нет"
DELIVERY_CDEK = "СДЭК"
DELIVERY_YANDEX = "Яндекс.Маркет"
CDEK_URL = "https://www.cdek.ru"
YANDEX_MARKET_URL = "https://market.yandex.ru"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_moscow_time():
    moscow_tz = timezone(timedelta(hours=3))  # UTC+3 для Москвы
    return datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")

def get_google_sheets_client():
    """Создание клиента Google Sheets"""
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        
        if SERVICE_ACCOUNT_INFO:
            # Используем credentials из переменной окружения
            creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scopes)
        else:
            # Для локальной разработки (если нужно)
            creds = Credentials.from_service_account_file("angelic-tracer-465313-t9-27151af1e09d.json", scopes=scopes)
        
        return gspread.authorize(creds)
    except Exception as e:
        logger.error(f"Ошибка создания Google Sheets клиента: {e}")
        return None

def append_consultation_row(row: list):
    try:
        gc = get_google_sheets_client()
        if not gc:
            raise Exception("Не удалось создать клиент Google Sheets")
        
        sh = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sh.get_worksheet(0)
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info("Консультация записана в таблицу")
    except Exception as e:
        logger.error(f"Ошибка записи консультации: {e}")
        raise

def append_book_row(row: list):
    try:
        gc = get_google_sheets_client()
        if not gc:
            raise Exception("Не удалось создать клиент Google Sheets")
        
        sh = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sh.get_worksheet(1)
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info("Заказ книги записан в таблицу")
    except Exception as e:
        logger.error(f"Ошибка записи заказа книги: {e}")
        raise

def append_question_row(row: list):
    try:
        gc = get_google_sheets_client()
        if not gc:
            raise Exception("Не удалось создать клиент Google Sheets")
        
        sh = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sh.get_worksheet(2)
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info("Вопрос записан в таблицу")
    except Exception as e:
        logger.error(f"Ошибка записи вопроса: {e}")
        raise

def client_type_keyboard():
    return ReplyKeyboardMarkup(
        [[BUTTON_CONSULT], [BUTTON_BOOK], [BUTTON_QUESTION]], 
        resize_keyboard=True,
        one_time_keyboard=True
    )

CONTACT_KEYBOARD = ReplyKeyboardMarkup(
    [[CONTACT_TELEGRAM, CONTACT_WHATSAPP]], 
    resize_keyboard=True,
    one_time_keyboard=True
)

YES_NO_KEYBOARD = ReplyKeyboardMarkup(
    [[YES, NO]], 
    resize_keyboard=True, 
    one_time_keyboard=True
)

DELIVERY_KEYBOARD = ReplyKeyboardMarkup(
    [[DELIVERY_CDEK], [DELIVERY_YANDEX]], 
    resize_keyboard=True,
    one_time_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Здравствуйте! Выберите тему вашего обращения:",
        reply_markup=client_type_keyboard()
    )

async def handle_client_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data.clear()
    
    if text == BUTTON_CONSULT:
        context.user_data["client_type"] = "consult"
        context.user_data["consult_step"] = 1
        await update.message.reply_text("Выберите способ связи:", reply_markup=CONTACT_KEYBOARD)
    elif text == BUTTON_BOOK:
        context.user_data["client_type"] = "book"
        context.user_data["book_step"] = 1
        await update.message.reply_text("Вы проживаете в Москве?", reply_markup=YES_NO_KEYBOARD)
    elif text == BUTTON_QUESTION:
        context.user_data["client_type"] = "question"
        context.user_data["question_step"] = 1
        await update.message.reply_text("Какой способ связи предпочитаете?", reply_markup=CONTACT_KEYBOARD)

async def handle_contact_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    client_type = context.user_data.get("client_type")
    
    if client_type == "consult":
        context.user_data["contact_method"] = text
        context.user_data["consult_step"] = 2
        await update.message.reply_text("Введите номер телефона:", reply_markup=ReplyKeyboardRemove())
    elif client_type == "book":
        context.user_data["contact_method"] = text
        context.user_data["book_step"] = 3
        await update.message.reply_text("Введите номер телефона:", reply_markup=ReplyKeyboardRemove())
    elif client_type == "question":
        context.user_data["contact_method"] = text
        context.user_data["question_step"] = 2
        await update.message.reply_text("Введите номер телефона:", reply_markup=ReplyKeyboardRemove())

async def handle_yes_no_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if context.user_data.get("client_type") == "book" and context.user_data.get("book_step") == 1:
        is_moscow = (text == YES)
        context.user_data["in_moscow"] = is_moscow
        context.user_data["book_step"] = 2
        await update.message.reply_text("Какой способ связи предпочитаете?", reply_markup=CONTACT_KEYBOARD)

async def handle_delivery_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if context.user_data.get("client_type") == "book" and context.user_data.get("book_step") == 4:
        context.user_data["delivery_service"] = text
        ts = get_moscow_time()
        location = "Москва" if context.user_data.get("in_moscow") else "Не Москва"
        row = [
            ts,
            location,
            context.user_data.get("contact_method", ""),
            context.user_data.get("phone", ""),
            context.user_data.get("delivery_service", "")
        ]
        try:
            append_book_row(row)
            if text == DELIVERY_CDEK:
                url, name = CDEK_URL, "СДЭК"
            else:
                url, name = YANDEX_MARKET_URL, "Яндекс.Маркет"
            inline_kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"Перейти на сайт {name}", url=url)]])
            await update.message.reply_text("Спасибо! Ваш заказ зарегистрирован и сохранён.")
            await update.message.reply_text(
                f"Вы выбрали доставку: {name}. Хотите перейти на сайт {name}?",
                reply_markup=inline_kb
            )
        except Exception as e:
            logger.exception("Ошибка записи (book, Не Москва) в Google Sheets: %s", e)
            await update.message.reply_text("Произошла ошибка при сохранении данных. Попробуйте позже.")
        context.user_data.clear()
        await update.message.reply_text("Вы можете выбрать другие действия:", reply_markup=client_type_keyboard())

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    client_type = context.user_data.get("client_type")
    
    # Обработка ввода номера телефона
    if (context.user_data.get("consult_step") == 2 or 
        context.user_data.get("book_step") == 3 or 
        context.user_data.get("question_step") == 2):
        
        context.user_data["phone"] = text
        
        if client_type == "consult":
            context.user_data["consult_step"] = 3
            await update.message.reply_text("Напишите тему консультации — основные 3 вопроса, которые вас интересуют:")
        
        elif client_type == "book":
            if context.user_data.get("in_moscow"):
                ts = get_moscow_time()
                row = [
                    ts,
                    "Москва",
                    context.user_data.get("contact_method", ""),
                    context.user_data.get("phone", ""),
                    ""
                ]
                try:
                    append_book_row(row)
                    await update.message.reply_text(
                        "Спасибо! Ваш заказ зарегистрирован. Мы свяжемся с вами в ближайшее время.")
                except Exception as e:
                    logger.exception("Ошибка записи (book, Москва) в Google Sheets: %s", e)
                    await update.message.reply_text("Произошла ошибка при сохранении данных. Попробуйте позже.")
                context.user_data.clear()
                await update.message.reply_text("Вы можете выбрать другие действия:", reply_markup=client_type_keyboard())
            else:
                context.user_data["book_step"] = 4
                await update.message.reply_text("Выберите службу доставки, которая вам удобна:", reply_markup=DELIVERY_KEYBOARD)
        
        elif client_type == "question":
            context.user_data["question_step"] = 3
            await update.message.reply_text("Напишите ваш вопрос:")
    
    # Обработка темы консультации
    elif context.user_data.get("consult_step") == 3:
        context.user_data["topic"] = text
        ts = get_moscow_time()
        row = [
            ts,
            context.user_data.get("contact_method", ""),
            context.user_data.get("phone", ""),
            context.user_data.get("topic", "")
        ]
        try:
            append_consultation_row(row)
            await update.message.reply_text(
                "Спасибо! Ваша заявка сохранена. Ожидайте, с вами свяжутся в ближайшее время.")
        except Exception as e:
            logger.exception("Ошибка записи в Google Sheets: %s", e)
            await update.message.reply_text(
                "Произошла ошибка при сохранении данных. Мы попробуем ещё раз автоматически — пожалуйста, сохраните скрин информации на случай проблем.")
        context.user_data.clear()
        await update.message.reply_text("Вы можете выбрать другие действия:", reply_markup=client_type_keyboard())
    
    # Обработка вопроса
    elif context.user_data.get("question_step") == 3:
        context.user_data["question_text"] = text
        ts = get_moscow_time()
        row = [
            ts,
            context.user_data.get("contact_method", ""),
            context.user_data.get("phone", ""),
            context.user_data.get("question_text", "")
        ]
        try:
            append_question_row(row)
            await update.message.reply_text("Спасибо! Ваш вопрос сохранён. Мы свяжемся с вами в ближайшее время.")
        except Exception as e:
            logger.exception("Ошибка записи (question) в Google Sheets: %s", e)
            await update.message.reply_text(
                "Произошла ошибка при сохранении вашего вопроса. Попробуйте, пожалуйста, позже.")
        context.user_data.clear()
        await update.message.reply_text("Вы можете выбрать другие действия:", reply_markup=client_type_keyboard())

async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("client_type"):
        client_type = context.user_data.get("client_type")
        if client_type == "consult":
            step = context.user_data.get("consult_step")
            if step == 1:
                await update.message.reply_text("Пожалуйста, выберите способ связи, используя кнопки ниже:", reply_markup=CONTACT_KEYBOARD)
                return
        elif client_type == "book":
            step = context.user_data.get("book_step")
            if step == 1:
                await update.message.reply_text("Пожалуйста, выберите ответ, используя кнопки ниже:", reply_markup=YES_NO_KEYBOARD)
                return
            elif step == 2:
                await update.message.reply_text("Пожалуйста, выберите способ связи, используя кнопки ниже:", reply_markup=CONTACT_KEYBOARD)
                return
            elif step == 4:
                await update.message.reply_text("Пожалуйста, выберите службу доставки, используя кнопки ниже:", reply_markup=DELIVERY_KEYBOARD)
                return
        elif client_type == "question":
            step = context.user_data.get("question_step")
            if step == 1:
                await update.message.reply_text("Пожалуйста, выберите способ связи, используя кнопки ниже:", reply_markup=CONTACT_KEYBOARD)
                return
    
    await update.message.reply_text("Пожалуйста, выберите один из вариантов:", reply_markup=client_type_keyboard())

def main():
    logger.info("Starting bot...")
    
    # Проверяем наличие необходимых переменных окружения
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен!")
        return
    
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Добавление обработчиков
        app.add_handler(MessageHandler(
            filters.Regex(f"^({BUTTON_CONSULT}|{BUTTON_BOOK}|{BUTTON_QUESTION})$"), 
            handle_client_type_selection
        ))
        app.add_handler(MessageHandler(
            filters.Regex(f"^({CONTACT_TELEGRAM}|{CONTACT_WHATSAPP})$"), 
            handle_contact_selection
        ))
        app.add_handler(MessageHandler(
            filters.Regex(f"^({YES}|{NO})$"), 
            handle_yes_no_selection
        ))
        app.add_handler(MessageHandler(
            filters.Regex(f"^({DELIVERY_CDEK}|{DELIVERY_YANDEX})$"), 
            handle_delivery_selection
        ))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message))

        logger.info("Bot is running...")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == "__main__":
    main()
