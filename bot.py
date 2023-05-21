import logging
import random
import threading
import traceback
from datetime import datetime, timedelta
from urllib.request import urlopen
from urllib.parse import quote
import re

import cv2
import numpy as np
import pytesseract
import requests
from dotenv import dotenv_values
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler, Updater
from thefuzz import fuzz, process

SLOTS_URL = "https://app.checkvisaslots.com/slots/v1"
SCREENSHOTS_URL = "https://app.checkvisaslots.com/retrieve/v1"
SCREENSHOTS_FILE_URL = "https://cvs-all-files.s3.amazonaws.com"

API_KEYS = open("keys.txt").read().splitlines()
CHAT_ID = dotenv_values("config.env").get("CHAT_ID")
BOT_TOKEN = dotenv_values("config.env").get("BOT_TOKEN")
SEND_DUPES = eval(dotenv_values("config.env").get("SEND_DUPES"))
YEAR = dotenv_values("config.env").get("YEAR")
MONTHS = dotenv_values("config.env").get("MONTHS").split(',')

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def get_slot_header(api_key):
    return {
        'authority': 'app.checkvisaslots.com',
        'origin': 'chrome-extension://beepaenfejnphdgnkmccjcfiieihhogl',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'x-api-key': api_key,
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


def check_NEWDELHI_consulate(results):
    return [[each["slots"], each["createdon"]] for each in results['slotDetails'] if each["visa_location"] == "NEW DELHI VAC"][0]


def get_NEWDELHI_screenshots(results):
    screenshot_urls = [(each["img_url"], each["createdon"]) for each in results if quote("NEW DELHI VAC") in each["img_url"]]
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
    # commenting this request because we're making double calls to api and exhausting api calls faster(1st is this call, 2nd being screenshot call)
    # response = requests.get(SLOTS_URL, headers=get_slot_header(api_key)) 
    # mockRespText = '{"slotDetails":[{"img_id":7602746,"visa_location":"CHENNAI","slots":0,"createdon":"Sat, 29 Apr 2023 17:10:46 GMT"},{"img_id":7602836,"visa_location":"CHENNAI VAC","slots":1,"createdon":"Sat, 29 Apr 2023 17:21:03 GMT"},{"img_id":7602748,"visa_location":"HYDERABAD","slots":0,"createdon":"Sat, 29 Apr 2023 17:10:49 GMT"},{"img_id":7602839,"visa_location":"HYDERABAD VAC","slots":6,"createdon":"Sat, 29 Apr 2023 17:21:11 GMT"},{"img_id":7602640,"visa_location":"KOLKATA","slots":0,"createdon":"Sat, 29 Apr 2023 16:58:24 GMT"},{"img_id":7602785,"visa_location":"KOLKATA VAC","slots":4,"createdon":"Sat, 29 Apr 2023 17:17:35 GMT"},{"img_id":7602765,"visa_location":"MUMBAI","slots":0,"createdon":"Sat, 29 Apr 2023 17:14:19 GMT"},{"img_id":7602830,"visa_location":"MUMBAI VAC","slots":30,"createdon":"Sat, 29 Apr 2023 17:20:48 GMT"},{"img_id":7602766,"visa_location":"NEW DELHI","slots":0,"createdon":"Sat, 29 Apr 2023 17:14:22 GMT"},{"img_id":7602831,"visa_location":"NEW DELHI VAC","slots":6,"createdon":"Sat, 29 Apr 2023 17:20:49 GMT"}],"userDetails":{"visa_type":"B1/B2","appointment_type":"Regular","subscription":"FREE"}}\n'
    # results = eval(mockRespText)
    # results = eval(response.text)
    # slots = check_NEWDELHI_consulate(results)

    # gmt_time = datetime.strptime(slots[1], "%a, %d %b %Y %H:%M:%S %Z")
    # ist_time = gmt_to_ist(gmt_time)
    # log_text = f'{slots[0]} slots available at {datetime.strftime(ist_time, "%I:%M:%S %p")}'
    log_text = "running now"
    logger.info(log_text)
    # if send_dupes or log_text != old_log_text:
    #     if slots[0] > 0:
    #         bot.send_message(chat_id=chat_id, text=f"🤯🤯🤯 {log_text} ({api_key}) ")
    #     else:
    #         bot.send_message(chat_id=chat_id, text=f"{log_text} ({api_key})")
    log_pics = []
    # if slots[0] > 0:
    response = requests.get(SCREENSHOTS_URL, headers=get_screenshots_header(api_key))
    results = eval(response.text)
    screenshots = get_NEWDELHI_screenshots(results)
    for screenshot, timestamp in screenshots:
        text = pytesseract.image_to_string(screenshot)
        # if "consular" in text.lower():

        # remove line with 'current appointment' in it
        fuzzyMatch = process.extractOne('current appointment', text.splitlines(), scorer=fuzz.partial_ratio)
        matchThreshold = 80
        if fuzzyMatch is not None and fuzzyMatch[1] > matchThreshold:
            text = ''.join(text.split(fuzzyMatch[0]))
        if YEAR in text.lower() and len([month for month in MONTHS if month.lower() in text.lower()]) > 0:
            text_with_dates = [re.sub(r"[^a-zA-Z0-9 ]", "", line) for line in text.splitlines() if YEAR in line]
            gmt_time = datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %Z")
            ist_time = gmt_to_ist(gmt_time)
            if send_dupes or not any(np.array_equal(screenshot, each) for each in old_log_pics):
                bot.send_message(chat_id=CHAT_ID, text="<b>"+'\n\n'.join(text_with_dates)+"</b>", parse_mode=ParseMode.HTML)
                bot.send_photo(
                    chat_id=chat_id,
                    photo=image_to_bytes(screenshot),
                    caption=datetime.strftime(ist_time, "%I:%M:%S %p") + "",
                )
            log_pics.append(screenshot)

    return log_text, log_pics


def monitor(bot, chat_id, old_log_text=None, old_log_pics=None):
    if old_log_pics is None:
        old_log_pics = []
    if old_log_text is None:
        bot.send_message(chat_id=CHAT_ID, text="<b>Monitoring Started!</b>", parse_mode=ParseMode.HTML)
        logger.info("Monitoring started!")
    try:
        log_text, log_pics = run_once(bot, chat_id, old_log_text, old_log_pics)
        minutes = 5
    except Exception as e:
        logger.error(e)
        bot.send_message(chat_id=CHAT_ID, text=f"Bot Crashed : {e}\n{traceback.format_exc()}")
        log_text, log_pics = old_log_text, old_log_pics
        minutes = 1

    threading.Timer(
        60 * minutes,
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
        try:
            run_once(context.bot, update.effective_chat.id)
        except Exception as e:
            logger.error(e)
            context.bot.send_message(
                chat_id=update.effective_chat.id, text=f"Bot Crashed : {e}\n{traceback.format_exc()}"
            )
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Unauthorized!")


def main():
    # Start bot
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    bot = updater.bot

    # Welcome message
    bot.send_message(
        chat_id=CHAT_ID, text="<b>Bot Started!</b>", parse_mode=ParseMode.HTML
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
