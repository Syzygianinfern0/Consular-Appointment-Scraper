<div align="center">

# 🇺🇸 Consular-Appointment-Scraper 🇺🇸

<samp> Reverse-engineering [`CheckVisaSlots`](https://checkvisaslots.com/)</samp>

</div>

## What? 👀

- Pro way to not waste your daily login and click quota on [CGI Federal](https://cgifederal.secure.force.com/).
- Runs 24/7 without interference.
- Checks for available VISA consular interview slots in Chennai from S3-buckets used by https://checkvisaslots.com.
- Notifies on Telegram whenever changes are detected along with relevant screenshots (searches for 'Chennai' in images
  using Tesseract-OCR).

## Why? 🤔

<div align="center">

<table>
<img src="https://c.tenor.com/zyQ7QpKF4OEAAAAM/typing-laptop.gif" alt="MEOW" width="200">
</table>

</div>

## How? 😯

DevTools Networks tab + Python + Tesseract + 🧠 = 💣

## Usage 👨‍💻

- Clone and create heroku app linked to this.
- Add [apt buildpack](https://elements.heroku.com/buildpacks/heroku/heroku-buildpack-apt) (we need to install `libgl1`
  to make cv2 work).
- `heroku config:set TESSDATA_PREFIX=/app/.apt/usr/share/tesseract-ocr/tessdata`
- Setup config vars of
    - `API_KEY`: From your https://checkvisaslots.com.
    - `BOT_TOKEN`: From BotFather in Telegram.
    - `CHAT_ID`: ID of group you want to run it in.
- Change the location (default Chennai) and checking interval (default 10 mins).

Some info on using the bot. 
- Monitoring start immediately - runs once every 10 mins. 
- Does not work in groups than the one you have authorized. 
- `/run` command to manually run a check

<div align="center">

# ●'◡'●

Please ~~like, share, and subscribe~~ star, fork, and follow if you found this useful.

</div>
