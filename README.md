# HourlyNews

Script to automatically create an hourly audio podcast based on RSS feeds, written by OpenAI, read by an AI TTS reporter. Publishing to Telegram and Mastodon.

This is the script behind the *Israel Today: Ongoing War Report* by Noa Levi.

- **Podcast**: [https://www.spreaker.com/show/israel-today-ongoing-war-report](https://www.spreaker.com/show/israel-today-ongoing-war-report)
- **Mastodon**: [https://babka.social/@noalevi](https://babka.social/@noalevi)
- **Telegram**: [https://t.me/ILWarReport](https://t.me/ILWarReport)

## Why?

I was trying to keep up with the overwhelming amount of information being published in Telegram channels. It was coming fast, and in Hebrew. My phone, my watch, my computer were all buzzing all the time. It was too much!

I wrote a script to aggregate the various news feeds every hour and used OpenAI to write a consolidated report. And then, my inner nerd took over:

- I had it read to me from the little speaker on the Raspberry Pi 3b it's running on...
- Then posted it to a Telegram channel...
- Then added music and published it as a podcast...
- Then started distributing it on Mastodon...

**I welcome any contributions!**

## Installation
Install the requirements

```pip3 install requirements.txt```

Configure the config.txt with:
- OpenAI API from [https://platform.openai.com](https://platform.openai.com)
- Mastodon API details from your Profile -> Development -> New Application page
- Telegram API details - see: [https://core.telegram.org/](https://core.telegram.org/)
- Spreaker API details from your Settings -> Developers -> Create a new application
 - For your Redirect URL, you can leave it as localhost if you are going to be authenticating from the same machine you're running the script. Otherwise, you'll need an FQDN (apparently it doesn't allow IP addresses)

Run it:
From within the directory, simply run:

```python3 ./main.py```

## Optional Parameters for main.py

- `--no-mastodon`: Skip publishing to Mastodon.
- `--no-podcast`: Skip publishing to Spreaker.
- `--no-telegram`: Skip publishing to Telegram.
- `--no-publish`: Skip publishing to Mastodon, Spreaker, and Telegram.
- `--no-audiofile`: Skip creating the TTS audio file.
- `--news_items {json file}`: Use a specific JSON file for news items instead of fetching from RSS feeds.

If you want it to run on the hour, you can cronjob it, or run the script from within the directory:

```sh ./run.sh```
