import os
import time
import csv
import datetime
import pendulum
import sys
import redis
import re
import html
import json
import logging
import traceback
from telegram import * 
from telegram.ext import *
from app.models import *
from . import bolt, uklon, uber
from scripts.driversrating import DriversRatingMixin
import traceback
import hashlib

PORT = int(os.environ.get('PORT', '8443'))
DEVELOPER_CHAT_ID = 803129892

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

processed_files = []


def update_db(update, context):
    """Pushing data to database from weekly_csv files"""
    # getting and opening files
    directory = '../app'
    files = os.listdir(directory)

    UberPaymentsOrder.download_weekly_report()
    UklonPaymentsOrder.download_weekly_report()
    BoltPaymentsOrder.download_weekly_report()

    files = os.listdir(directory)
    files_csv = filter(lambda x: x.endswith('.csv'), files)
    list_new_files = list(set(files_csv)-set(processed_files))

    if len(list_new_files) == 0:
        update.message.reply_text('No new updates yet')
    else:
        update.message.reply_text('Please wait')
        for name_file in list_new_files:
            processed_files.append(name_file)
            with open(f'{directory}/{name_file}', encoding='utf8') as file:
                if 'Куцко - Income_' in name_file:
                    UklonPaymentsOrder.parse_and_save_weekly_report_to_database(file=file)
                elif '-payments_driver-___.csv' in name_file:
                    UberPaymentsOrder.parse_and_save_weekly_report_to_database(file=file)
                elif 'Kyiv Fleet 03_232 park Universal-auto.csv' in name_file:
                    BoltPaymentsOrder.parse_and_save_weekly_report_to_database(file=file)

        FileNameProcessed.save_filename_to_db(processed_files)
        list_new_files.clear()
        update.message.reply_text('Database updated')


def code(update: Update, context: CallbackContext):
    r = redis.Redis.from_url(os.environ["REDIS_URL"])
    r.publish('code', update.message.text)
    update.message.reply_text('Generating a report...')
    context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
    # chat_id = update.message.chat.id
    # user = User.get_by_chat_id(chat_id)
    # if user.email == "null":
    #     regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    #     email = update.message.text
    #     if re.fullmatch(regex, email):
    #         user.email = email
    #         user.save()
    #     else:
    #         update.message.reply_text('Your email is incorrect, please write again')
    # else:
    #     aut_handler(update, context)


def save_reports(update, context):
    wrf = WeeklyReportFile()
    wrf.save_weekly_reports_to_db()
    update.message.reply_text("Reports have been saved")


def error_handler(update: object, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )

    # Finally, send the message
    context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML)


def get_owner_today_report(update, context) -> str:
    pass


def get_driver_today_report(update, context) -> str:
    driver_first_name = Users.objects.filter(user_id = {update.message.chat.id})
    driver_ident = PaymentsOrder.objects.filter(driver_uuid='')
    if user.type == 0:
        data = PaymentsOrder.objects.filter(transaction_time = date.today(), driver_uuid = {driver_ident} )
        update.message.reply_text(f'Hi {update.message.chat.username} driver')
        update.message.reply_text(text = data)


def get_driver_week_report(update, context) -> str:
    pass


def choice_driver_option(update, context) -> list:
        update.message.reply_text(f'Hi {update.message.chat.username} driver')
        buttons = [[KeyboardButton('Get today statistic')], [KeyboardButton('Choice week number')],[KeyboardButton('Update report')]]
        context.bot.send_message(chat_id=update.effective_chat.id, text='choice option',
        reply_markup=ReplyKeyboardMarkup(buttons))


def get_manager_today_report(update, context) -> str:
    if user.type == 1:
        data = PaymentsOrder.objects.filter(transaction_time = date.today())
        update.message.reply_text(text=data)
    else:
        error_handler()


def get_stat_for_manager(update, context) -> list:
        update.message.reply_text(f'Hi {update.message.chat.username} manager')
        buttons = [[KeyboardButton('Get all today statistic')]]
        context.bot.send_message(chat_id=update.effective_chat.id, text='choice option',
        reply_markup=ReplyKeyboardMarkup(buttons))


def drivers_rating(context):
    text = 'Drivers Rating\n\n'
    for fleet in DriversRatingMixin().get_rating():
        text += fleet['fleet'] + '\n'
        for period in fleet['rating']:
            text += f"{period['start']:%d.%m.%Y} - {period['end']:%d.%m.%Y}" + '\n'
            text += '\n'.join([f"{item['num']} {item['driver']} {item['trips'] if item['trips']>0 else ''}" for item in period['rating']]) + '\n\n'


def get_number(update, context):
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    if not user:
        phone_number = update.message.contact.phone_number
        custom_user = User(email="null", phone_number=phone_number, chat_id=chat_id)
        custom_user.save()
        update.message.reply_text("Enter your email:")


def aut_handler(update, context) -> list:
    if 'Get autorizate' in update.message.text:
        if user.type == 0:
            choice_driver_option(update, context)
        elif user.type == 2:
            get_owner_today_report(update, context)
        elif user.type == 1:
            get_stat_for_manager(update, context)
        else:
            get_number()


def get_update_report(update, context):
    user = User.get_by_chat_id(chat_id)
    if user in uklon_drivers_list:
        update.message.reply_text("Enter you Uklon OTP code from SMS:")
        uklon.run()
        aut_handler(update, context)
    elif username in bolt_drivers_list:
        update.message.reply_text("Enter you Bolt OTP code from SMS:")
        bolt.run()
        aut_handler(update, context)
    elif username in uber_drivers_list:
        update.message.reply_text("Enter you Uber OTP code from SMS:")
        uber.run()
        aut_handler(update, context)
def location(update: Update, context: CallbackContext):
    user = update.effective_user
    msg_type = 0
    current_pos = (update.message.location.latitude, update.message.location.longitude)
    # phone_number = update.message.contact.phone_number
    context.bot.send_message(user.id, current_pos)
    # context.bot.send_message(user.id, phone_number)
    if update.edited_message:
        message = update.edited_message
    else:
        message = update.message

    if message["edit_date"] is not None:
        msg_type += 1
    if message["location"]["live_period"] is not None:
        msg_type += 1 << 1

    if msg_type == 0:
        context.bot.send_message(user.id, "Single (non-live) location update.")
    elif msg_type == 1:
        context.bot.send_message(user.id, "End of live period.")
    elif msg_type == 2:
        context.bot.send_message(user.id, "Start of live period")
    elif msg_type == 3:
        context.bot.send_message(user.id, "Live location update.")

def location1(update,context):
    location(update, context)


def start(update, context):
    update.message.reply_text('Hi!')
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Give phone number", request_contact=True),
             ],
        ],
        resize_keyboard=True,
    )
    if user:
        update.message.reply_text("You are already started bot")
        aut_handler(update, context)
    else:
        update.message.reply_text("Please give your number to start bot", reply_markup=reply_markup, )


def report(update, context):
    update.message.reply_text("Enter you Uber OTP code from SMS:")
    update.message.reply_text(get_report())


def get_help(update, context) -> str:
    update.message.reply_text('''For first step make registration by, or autorizate by /start command, if already registered.
    after all you can update your report, or pull statistic for choice''')


def status(update, context):
    buttons = [[KeyboardButton('Free')], [KeyboardButton('With client')], [KeyboardButton('Waiting for a client')], [KeyboardButton('Offline')]]

    context.bot.send_message(chat_id=update.effective_chat.id, text='Choice your status',
                             reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))


def get_status_driver_and_change(update, context):
    status = update.message.text
    chat_id = update.message.chat.id
    Driver.get_by_chat_id(chat_id=chat_id)
    if driver.role == 'Driver':
        driver[driver_status] = status
        driver.save()
        update.message.reply_text('Your status has been changed')
    else:
        try:
            driver = Driver.objects.get(driver_status=status)
            return update.message.reply_text(driver)
        except Driver.DoesNotExist:
            return update.message.reply_text('There are currently no drivers with this status')


def main():
    updater = Updater(os.environ['TELEGRAM_TOKEN'], use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("help", get_help))
    dp.add_handler(CommandHandler("start",  start))
    dp.add_handler(CommandHandler("report", report, run_async=True))
    dp.add_handler(CommandHandler('update', update_db, run_async=True))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("save_reports", save_reports))
    dp.add_handler(MessageHandler(Filters.text, code))
    dp.add_handler(MessageHandler(Filters.text('Get all today statistic'), get_manager_today_report))
    dp.add_handler(MessageHandler(Filters.text('Get today statistic'), get_driver_today_report))
    dp.add_handler(MessageHandler(Filters.text('Choice week number'), get_driver_week_report))
    dp.add_handler(MessageHandler(Filters.text('Update report'), get_update_report))
    dp.add_handler(MessageHandler(Filters.text('Free'), get_status_driver_and_change))
    dp.add_handler(MessageHandler(Filters.text('With client'), get_status_driver_and_change))
    dp.add_handler(MessageHandler(Filters.text('Waiting for a client'), get_status_driver_and_change))
    dp.add_handler(MessageHandler(Filters.text('Offline'), get_status_driver_and_change))
    dp.add_handler(MessageHandler(Filters.contact, get_number))
    dp.add_error_handler(error_handler)
    updater.job_queue.run_daily(drivers_rating, time=datetime.time(6, 0, 0), days=(0,))
    updater.job_queue.run_repeating(drivers_rating, interval=120, first=1)
    updater.start_polling()
    updater.idle()


def run():
    main()
