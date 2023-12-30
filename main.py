import argparse
import random
import json
import os
from datetime import datetime
import configparser
import logging
from re import I
from opml_parser import extract_rss_urls_from_opml
from rss_parser import gather_news_from_rss
from podcast_script_generator import generate_podcast_script
from tts_converter import text_to_speech
from telegram_sender import send_to_telegram
from podcast_publisher import publish_to_spreaker
from mastodon_publisher import post_status_with_audio
from headline_generator import generate_headlines

# Configure logging
log_file = 'app.log'
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(log_file, 'a', 'utf-8'), 
                              logging.StreamHandler()])
logger = logging.getLogger(__name__)

def read_file_content(filename):
    """Reads the entire content of a file if it exists, otherwise returns an empty string."""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        logger.warning(f"File not found: {filename}. Skipping this step.")
        return ""

def read_config(config_file):
    """Read configuration from an INI file."""
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def main(args):
    # Filename Prefix for all files associated with this report
    file_name_prefix = f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}"
    logger.info(f"**** Start of Run: {file_name_prefix} ****")

    config = read_config(args.config_file)

    # Set Model Parameters
    current_hour = datetime.now().hour
    day_start = config.getint('OpenAI', 'day_start')
    day_end = config.getint('OpenAI', 'day_end')
    if day_start <= current_hour < day_end:
        logging.info(f"After {day_start}, using daytime model")
        model_name = config.get('OpenAI', 'model_day')
    else:
        logging.info(f"After {day_end}, using nighttime model")
        model_name = config.get('OpenAI', 'model_night')
    temperature = float(config.get('OpenAI', 'temperature', fallback=0.7))
    seed = config.getint('OpenAI', 'seed', fallback=random.randint(10000, 99999))
    key = config.get('OpenAI', 'openai')
    system_message = config.get('OpenAI', 'system_message')
    user_message = config.get('OpenAI', 'user_message')
    logger.info(f"Model: {model_name}")
    logger.info(f"Temperature: {temperature}")
    logger.info(f"Seed: {seed}")
    logger.info(f"OpenAI Key: {key}")
    logger.info(f"System Message: {system_message}")
    logger.info(f"User Message: {user_message}")

    # Reading RSS URLs from an OPML file or JSON file
    if args.news_items:
        logger.info(f"Reading news items from JSON file {args.news_items}")
        with open(args.news_items, 'r') as file:
            news_items = json.load(file)
    else:
        opml_file = config.get('News', 'opml', fallback="subscription.opml")
        timeframe_minutes = config.getint('News', 'period', fallback=60)
        logger.info(f"Reading news for last {timeframe_minutes} minutes items from RSS feeds in {opml_file}")
        rss_urls = extract_rss_urls_from_opml(opml_file)
        news_items = gather_news_from_rss(rss_urls, file_name_prefix, timeframe_minutes)

    # Generate podcast script
    show_title = config.get('News', 'show_title')
    host = config.get('News', 'host')
    host_tagline = config.get('News', 'host_tagline')
    disclaimer = config.get('News', 'disclaimer')
    podcast_script = generate_podcast_script(news_items[:50], model_name, temperature, seed,
                                             file_name_prefix, key, system_message, user_message,
                                             show_title, host, host_tagline, disclaimer) 

    # Convert text to speech and get the audio filename
    if not args.no_audiofile:
        intro_music_file = config.get('Branding', 'intro_music')
        outro_music_file = config.get('Branding', 'outro_music')
        host_voice = config.get('News', 'host_voice')
        show_description = config.get('News', 'show_description')
        audio_filename = text_to_speech(podcast_script, file_name_prefix,
                                        intro_music_file, outro_music_file,
                                        host, host_voice, show_title, show_description)
    else:
        logger.info("No audio being generated")

    # Generated Headlines
    headlines = generate_headlines(podcast_script, model_name, temperature, seed, key)
    podcast_description = f"{headlines}\n{podcast_script}"

    # Read the content of sources.txt and append it to the podcast description
    sources_content = read_file_content(f'{file_name_prefix}-sources.txt')
    podcast_description += f"\n\n{sources_content}"
    logging.info("Headlines and sources appended")

    if not args.no_podcast:
        logging.info("Publishing to Spreaker")
        # from config_handler import read_spreaker_client_id_from_config, read_spreaker_client_secret_from_config, read_spreaker_redirect_uri_from_config, read_key_from_config
        spreaker_client_id = config.get('Spreaker', 'client_id')
        spreaker_client_secret = config.get('Spreaker', 'client_secret')
        spreaker_show_id = config.get('Spreaker', 'show_id')
        spreaker_redirect_uri = config.get('Spreaker', 'redirect_uri')
        publish_to_spreaker(audio_filename, podcast_description, spreaker_client_id, spreaker_client_secret, spreaker_show_id, spreaker_redirect_uri) 

    if not args.no_mastodon:
        logging.info("Publishing to Mastodon")
        mastodon_instance_url = config.get('Mastodon', 'instance_url')
        mastodon_client_id = config.get('Mastodon', 'client_id')
        mastodon_client_secret = config.get('Mastodon', 'client_secret')
        mastodon_access_token = config.get('Mastodon', 'access_token')
        hashtags = config.get('Mastodon', 'hashtags')
        embedded_url = config.get('Spreaker', 'embedded_url')
        podcast_url = config.get('Spreaker', 'podcast_url')
        podcast_apple = config.get('Spreaker', 'podcast_apple')
        podcast_spotify = config.get('Spreaker', 'podcast_spotify')
        podcast_google = config.get('Spreaker', 'podcast_google')
        podcast_amazon = config.get('Spreaker', 'podcast_amazon')
        post_status_with_audio(headlines, 
                               mastodon_instance_url, mastodon_client_id, mastodon_client_secret, mastodon_access_token, 
                               show_title, hashtags, embedded_url, podcast_url,
                               podcast_apple, podcast_spotify, podcast_google, podcast_amazon)

    if not args.no_telegraph:
        logging.info("Publishing to Telegram")
        telegram_token = config.get('Telegram', 'token')
        telegram_channel_id = config.get('Telegram', 'channel_id')
        send_to_telegram(podcast_description, telegram_token, telegram_channel_id) 

    logger.info(f"**** End of Run: {file_name_prefix} ****")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Podcast Automation Script")
    parser.add_argument("--no-mastodon", action="store_true", help="Skip publishing to Mastodon")
    parser.add_argument("--no-podcast", action="store_true", help="Skip publishing to Spreaker")
    parser.add_argument("--no-telegraph", action="store_true", help="Skip publishing to Telegram")
    parser.add_argument("--no-publish", action="store_true", help="Skip publishing to Mastodon, Spreaker, and Telegram")
    parser.add_argument("--no-audiofile", action="store_true", help="Skip creating the TTS audio file")
    parser.add_argument("--news_items", type=str, help="Use news items from a specified JSON file")
    parser.add_argument('--config_file', type=str, default='config.ini', help='Path to the config file (default: config.ini)')
    args = parser.parse_args()

    # If --no-publish is set, apply all individual no-publish flags
    if args.no_publish:
        args.no_mastodon = args.no_podcast = args.no_telegraph = True

    for arg in vars(args):
        logger.info("Argument %s: %r", arg, getattr(args, arg))

    main(args)
