import os
import logging
import telegram
import gspread

from dotenv import load_dotenv
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    CallbackQueryHandler,
    Application,
    CommandHandler,
    ContextTypes
)
from gspread import Client, Spreadsheet


load_dotenv()

SPREADSHEET_URL = os.getenv('SPREADSHEET_URL')
TOKEN = os.getenv('TOKEN')
MANAGER_CHAT_ID = os.getenv('MANAGER_CHAT_ID')

bot = telegram.Bot(token=TOKEN)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


def get_worksheet():
    gs_client: Client = gspread.service_account('credentials.json')
    sheet: Spreadsheet = gs_client.open_by_url(SPREADSHEET_URL)
    return sheet.sheet1


async def send_message(chat_id, text, reply_markup=None):
    await bot.send_message(
        chat_id=chat_id, text=text, reply_markup=reply_markup
    )


async def send_remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ws = get_worksheet()
    keyboard = [
        [InlineKeyboardButton("Выполнено", callback_data='done')],
        [InlineKeyboardButton("Не сделано", callback_data='not_done')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    reminders = ws.get_all_records()
    for reminder in reminders:
        tel_id, text, date, time, answer_time = reminder.values()
        message = 'Напоминание:\n%s\nДата: %s\nВремя: %s' % (text, date, time)
        await send_message(tel_id, message, reply_markup=reply_markup)
        context.job_queue.run_once(
            reminder_callback, answer_time, user_id=tel_id)


async def reminder_callback(context):
    tel_id = context.job.user_id
    await send_message(MANAGER_CHAT_ID, "%s не ответил." % tel_id)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    answer = query.data
    await send_message(MANAGER_CHAT_ID, '%s - %s' % (user_id, answer))
    await query.answer()
    await query.edit_message_text(text=f"Selected option: {answer}")


def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("remind", send_remind))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
