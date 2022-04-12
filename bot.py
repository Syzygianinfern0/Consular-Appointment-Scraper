import logging
import os
import threading
from datetime import datetime, timedelta
from urllib.request import urlopen

import cv2
import numpy as np
import pytesseract
import requests
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler, Updater

SLOTS_URL = "https://app.checkvisaslots.com/slots"
SCREENSHOTS_URL = "https://app.checkvisaslots.com/retrieve/v1"
SCREENSHOTS_FILE_URL = "https://cvs-all-files.s3.amazonaws.com"
API_KEY = os.environ["API_KEY"]
CHAT_ID = os.environ["CHAT_ID"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

SLOTS_HEADERS = {
    "origin": "chrome-extension://beepaenfejnphdgnkmccjcfiieihhogl",
    "x-api-key": API_KEY,
}
SCREENSHOTS_HEADERS = {
    "origin": "https://checkvisaslots.com",
    "x-api-key": API_KEY,
}


def url_to_image(url):
    resp = urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return image


def image_to_bytes(img):
    _, bts = cv2.imencode(".jpg", img)
    bts = bts.tostring()
    return bts


def check_chennai_consulate(results):
    return [[each["slots"], each["createdon"]] for each in results if each["visa_location"] == "CHENNAI"][0]


def get_chennai_screenshot(results):
    screenshot_urls = [(each["img_url"], each["createdon"]) for each in results if "CHENNAI" in each["img_url"]]
    screenshots = []
    for url, timestamp in screenshot_urls:
        screenshots.append([url_to_image(SCREENSHOTS_FILE_URL + url), timestamp])
    return screenshots


def gmt_to_ist(time_in_gmt):
    return time_in_gmt + timedelta(hours=5, minutes=30)
    # return time_in_gmt.replace(tzinfo=tz.gettz("GMT")).astimezone(tz=tz.gettz("IST"))


def run_once(bot, chat_id, old_log_text=None, old_log_pics=[], send_dupes=False):
    response = requests.get(SLOTS_URL, headers=SLOTS_HEADERS)
    results = eval(response.text)
    slots = check_chennai_consulate(results)

    gmt_time = datetime.strptime(slots[1], "%a, %d %b %Y %H:%M:%S %Z")
    ist_time = gmt_to_ist(gmt_time)
    log_text = f'{slots[0]} slots available at {datetime.strftime(ist_time, "%I:%M %p")}'
    logger.info(log_text)
    if send_dupes or log_text != old_log_text:
        bot.send_message(chat_id=chat_id, text=log_text)

    log_pics = []
    if slots[0] > -1:
        response = requests.get(SCREENSHOTS_URL, headers=SCREENSHOTS_HEADERS)
        results = eval(response.text)
        screenshots = get_chennai_screenshot(results)
        for screenshot, timestamp in screenshots:
            text = pytesseract.image_to_string(screenshot)
            if "consular" in text.lower():
                gmt_time = datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %Z")
                ist_time = gmt_to_ist(gmt_time)
                if send_dupes or any(np.array_equal(screenshot, each) for each in old_log_pics):
                    bot.send_photo(
                        chat_id=chat_id,
                        photo=image_to_bytes(screenshot),
                        caption=datetime.strftime(ist_time, "%I:%M %p"),
                    )
                log_pics.append(screenshot)

    return log_text, log_pics


def monitor(bot, chat_id, old_log_text=None, old_log_pics=[], send_dupes=False):
    if old_log_text is None:
        bot.send_message(chat_id=CHAT_ID, text="<b>Monitoring Started!</b>", parse_mode=ParseMode.HTML)
        logger.info("Monitoring started!")
    log_text, log_pics = run_once(bot, chat_id, old_log_text, old_log_pics, send_dupes)
    threading.Timer(
        # 60 * 10,
        10,
        monitor,
        kwargs={
            "bot": bot,
            "chat_id": chat_id,
            "old_log_text": log_text,
            "old_log_pics": log_pics,
            "send_dupes": True,
        },
    ).start()  # every 10 mins


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
    updater = Updater(token=BOT_TOKEN, use_context=True)

    dispatcher = updater.dispatcher
    bot = updater.bot
    bot.send_message(chat_id=CHAT_ID, text="<b>Bot Started!</b>", parse_mode=ParseMode.HTML)
    logger.info("Bot started!")
    dispatcher.add_handler(CommandHandler("start", start_handler))
    dispatcher.add_handler(CommandHandler("run", run_once_handler))

    threading.Thread(target=monitor, kwargs={"bot": bot, "chat_id": CHAT_ID}).start()
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
