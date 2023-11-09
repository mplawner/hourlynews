# Main script to tie everything together

from re import I
from rss_parser import gather_news_from_rss
from play_audio import play_audio
from podcast_script_generator import generate_podcast_script
from opml_parser import extract_rss_urls_from_opml
from tts_converter import text_to_speech
from telegram_sender import send_to_telegram 
from podcast_publisher import publish_to_spreaker  
from mastodon_publisher import post_status_with_audio  
from headline_generator import generate_headlines
from datetime import datetime
from config_handler import read_model_param_seed_from_config, read_model_param_temp_from_config
import random

def read_file_content(filename):
    """Reads the entire content of a file and returns it."""
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()

if __name__ == "__main__":
    # Filename Prefix for all files associated with this report
    file_name_prefix = f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}"

    current_hour = datetime.now().hour
    if 4 <= current_hour < 20:
        model_name = "gpt-4-1106-preview"
    else:
        model_name = "gpt-3.5-turbo-1106"

    # Model Parameters
    temperature = read_model_param_temp_from_config() or 0.7  
    seed = read_model_param_seed_from_config() or random.randint(10000, 99999)  # 5-digit random integer

    # Save model parameters to a file
    model_params_file = f"{file_name_prefix}-model_params.txt"

    # Save the generated seed to a file
    with open(model_params_file, 'w') as file:
        file.write(f"model={model_name}\n")
        file.write(f"temperature={temperature}\n")
        file.write(f"seed={seed}\n")

    # Reading RSS URLs from an OPML file
    rss_urls = extract_rss_urls_from_opml("subscriptions.opml")

    # Gathering news
    news_items = gather_news_from_rss(rss_urls, file_name_prefix)

    # Generate podcast script
    podcast_script = generate_podcast_script(news_items[:50], model_name, temperature, seed, file_name_prefix) 
    #print(podcast_script)

    # Convert text to speech and get the audio filename
    audio_filename = text_to_speech(podcast_script, file_name_prefix)

    # Play the generated audio
    # play_audio(audio_filename) 

    # Generated Headlines
    headlines = generate_headlines(podcast_script, model_name, temperature, seed)
    podcast_description = f"{headlines}\n\n{podcast_script}"

    # Read the content of sources.txt and append it to the podcast description
    sources_content = read_file_content(f'{file_name_prefix}-sources.txt')
    podcast_description += f"\n\n{sources_content}"
    #print(podcast_description)

    # Send the audio and script to the Telegram channel
    send_to_telegram(audio_filename, podcast_description) 

    # Publish the audio to Spreaker
    publish_to_spreaker(audio_filename, podcast_description) 

    # Publish to Mastodon
    post_status_with_audio(audio_filename, headlines)
