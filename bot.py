import logging
import random
import threading
from datetime import datetime, timedelta
from urllib.request import urlopen

import cv2
import numpy as np
import pytesseract
import requests
from dotenv import dotenv_values
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler, Updater

SLOTS_URL = "https://app.checkvisaslots.com/slots"
SCREENSHOTS_URL = "https://app.checkvisaslots.com/retrieve/v1"
SCREENSHOTS_FILE_URL = "https://cvs-all-files.s3.amazonaws.com"

API_KEYS = open("keys.txt").read().splitlines()
CHAT_ID = dotenv_values("config.env").get("CHAT_ID")
BOT_TOKEN = dotenv_values("config.env").get("BOT_TOKEN")
SEND_DUPES = eval(dotenv_values("config.env").get("SEND_DUPES"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def get_slot_header(api_key):
    return {
        "origin": "chrome-extension://beepaenfejnphdgnkmccjcfiieihhogl",
        "x-api-key": api_key,
    }


def get_screenshots_header(api_key):
    return {
        "origin": "https://checkvisaslots.com",
        "x-api-key": api_key,
    }


def url_to_image(url):
    resp = urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return image


def image_to_bytes(img):
    _, bts = cv2.imencode(".jpg", img)
    bts = bts.tobytes()
    return bts


def check_chennai_consulate(results):
    return [[each["slots"], each["createdon"]] for each in results if each["visa_location"] == "CHENNAI"][0]


def get_chennai_screenshots(results):
    screenshot_urls = [(each["img_url"], each["createdon"]) for each in results if "CHENNAI" in each["img_url"]]
    screenshots = []
    for url, timestamp in screenshot_urls:
        screenshots.append([url_to_image(SCREENSHOTS_FILE_URL + url), timestamp])
    return screenshots


def gmt_to_ist(time_in_gmt):
    return time_in_gmt + timedelta(hours=5, minutes=30)


def run_once(bot, chat_id, old_log_text=None, old_log_pics=None, api_key=None, send_dupes=SEND_DUPES):
    if old_log_pics is None:
        old_log_pics = []
    if api_key is None:
        api_key = random.choice(API_KEYS)
    response = requests.get(SLOTS_URL, headers=get_slot_header(api_key))
    results = eval(response.text)
    slots = check_chennai_consulate(results)

    gmt_time = datetime.strptime(slots[1], "%a, %d %b %Y %H:%M:%S %Z")
    ist_time = gmt_to_ist(gmt_time)
    log_text = f'{slots[0]} slots available at {datetime.strftime(ist_time, "%I:%M:%S %p")}'
    logger.info(log_text)
    if send_dupes or log_text != old_log_text:
        if slots[0] > 0:
            bot.send_message(chat_id=chat_id, text=f"🤯🤯🤯 {log_text} ({api_key}) @Syzygianinfern0 @M_N_Sathish")
        else:
            bot.send_message(chat_id=chat_id, text=f"{log_text} ({api_key})")
    log_pics = []
    if slots[0] > -1:
        response = requests.get(SCREENSHOTS_URL, headers=get_screenshots_header(api_key))
        results = eval(response.text)
        screenshots = get_chennai_screenshots(results)
        for screenshot, timestamp in screenshots:
            text = pytesseract.image_to_string(screenshot)
            if "consular" in text.lower():
                gmt_time = datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %Z")
                ist_time = gmt_to_ist(gmt_time)
                if send_dupes or not any(np.array_equal(screenshot, each) for each in old_log_pics):
                    bot.send_photo(
                        chat_id=chat_id,
                        photo=image_to_bytes(screenshot),
                        caption=datetime.strftime(ist_time, "%I:%M:%S %p") + " @Syzygianinfern0 @M_N_Sathish",
                    )
                log_pics.append(screenshot)

    return log_text, log_pics


def monitor(bot, chat_id, old_log_text=None, old_log_pics=None):
    if old_log_pics is None:
        old_log_pics = []
    if old_log_text is None:
        bot.send_message(chat_id=CHAT_ID, text="<b>Monitoring Started!</b>", parse_mode=ParseMode.HTML)
        logger.info("Monitoring started!")
    log_text, log_pics = run_once(bot, chat_id, old_log_text, old_log_pics)
    threading.Timer(
        60 * 5,
        monitor,
        kwargs={
            "bot": bot,
            "chat_id": chat_id,
            "old_log_text": log_text,
            "old_log_pics": log_pics,
        },
    ).start()


def start_handler(update: Update, context: CallbackContext):
    if str(update.effective_chat.id) == CHAT_ID:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Hello!")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Unauthorized!")


def run_once_handler(update: Update, context: CallbackContext):
    if str(update.effective_chat.id) == CHAT_ID:
        run_once(context.bot, update.effective_chat.id)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Unauthorized!")


def main():
    # Start bot
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    bot = updater.bot

    # Welcome message
    bot.send_message(
        chat_id=CHAT_ID, text="<b>Bot Started!</b> ) @Syzygianinfern0 @M_N_Sathish", parse_mode=ParseMode.HTML
    )
    logger.info("Bot started!")

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start_handler))
    dispatcher.add_handler(CommandHandler("run", run_once_handler))

    # Start monitoring service
    threading.Thread(target=monitor, kwargs={"bot": bot, "chat_id": CHAT_ID}).start()

    # Start bot handler services
    updater.start_polling()


if __name__ == "__main__":
    main()
