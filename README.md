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
- Setup config vars of
    - `API_KEY`: From your https://checkvisaslots.com.
    - `BOT_TOKEN`: From BotFather in Telegram.
    - `CHAT_ID`: ID of group you want to run it in.
- Change the location (default Chennai) and checking interval (default).

<div align="center">

# ●'◡'●

Please ~~like, share, and subscribe~~ star, fork, and follow if you found this useful.

</div>