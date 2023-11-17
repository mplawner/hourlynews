import argparse
import random
import json
import os
from datetime import datetime
from config_handler import read_model_param_seed_from_config, read_model_param_temp_from_config
from opml_parser import extract_rss_urls_from_opml
from rss_parser import gather_news_from_rss
from podcast_script_generator import generate_podcast_script
from tts_converter import text_to_speech
from telegram_sender import send_to_telegram
from podcast_publisher import publish_to_spreaker
from mastodon_publisher import post_status_with_audio
from headline_generator import generate_headlines

def read_file_content(filename):
    """Reads the entire content of a file if it exists, otherwise returns an empty string."""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        print(f"File not found: {filename}. Skipping this step.")
        return ""


def main(args):
    # Filename Prefix for all files associated with this report
    file_name_prefix = f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}"

    current_hour = datetime.now().hour
    if 5 <= current_hour < 23:
        model_name = "gpt-4-1106-preview"
    else:
        model_name = "gpt-3.5-turbo-1106"

    # Model Parameters
    temperature = read_model_param_temp_from_config() or 0.7  
    seed = read_model_param_seed_from_config() or random.randint(10000, 99999)  # 5-digit random integer

    # Save model parameters to a file
    model_params_file = f"{file_name_prefix}-model_params.txt"
    with open(model_params_file, 'w') as file:
        file.write(f"model={model_name}\n")
        file.write(f"temperature={temperature}\n")
        file.write(f"seed={seed}\n")

    # Reading RSS URLs from an OPML file or JSON file
    if args.news_items:
        with open(args.news_items, 'r') as file:
            news_items = json.load(file)
    else:
        rss_urls = extract_rss_urls_from_opml("subscriptions.opml")
        news_items = gather_news_from_rss(rss_urls, file_name_prefix)

    # Generate podcast script
    podcast_script = generate_podcast_script(news_items[:50], model_name, temperature, seed, file_name_prefix) 

    # Convert text to speech and get the audio filename
    if not args.no_audiofile:
        audio_filename = text_to_speech(podcast_script, file_name_prefix)

    # Generated Headlines
    headlines = generate_headlines(podcast_script, model_name, temperature, seed)
    podcast_description = f"{headlines}\n\n{podcast_script}"

    # Read the content of sources.txt and append it to the podcast description
    sources_content = read_file_content(f'{file_name_prefix}-sources.txt')
    podcast_description += f"\n\n{sources_content}"

    if not args.no_telegraph:
        send_to_telegram(audio_filename, podcast_description) 

    if not args.no_podcast:
        publish_to_spreaker(audio_filename, podcast_description) 

    if not args.no_mastodon:
        post_status_with_audio(audio_filename, headlines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Podcast Automation Script")
    parser.add_argument("--no-mastodon", action="store_true", help="Skip publishing to Mastodon")
    parser.add_argument("--no-podcast", action="store_true", help="Skip publishing to Spreaker")
    parser.add_argument("--no-telegraph", action="store_true", help="Skip publishing to Telegram")
    parser.add_argument("--no-publish", action="store_true", help="Skip publishing to Mastodon, Spreaker, and Telegram")
    parser.add_argument("--no-audiofile", action="store_true", help="Skip creating the TTS audio file")
    parser.add_argument("--news_items", type=str, help="Use news items from a specified JSON file")
    args = parser.parse_args()

    # If --no-publish is set, apply all individual no-publish flags
    if args.no_publish:
        args.no_mastodon = args.no_podcast = args.no_telegraph = True

    main(args)
