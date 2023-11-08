# Main script to tie everything together

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
import random

if __name__ == "__main__":
    # Filename Prefix for all files associated with this report
    file_name_prefix = f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}"

    current_hour = datetime.now().hour
    if 6 <= current_hour < 18:
        model_name = "gpt-4-1106-preview"
    else:
        model_name = "gpt-3.5-turbo-1106"

    # Model Parameters
    temperature = 0.7  
    seed = random.randint(10000, 99999)  # 5-digit random integer

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
    #news_items = gather_news_from_rss(rss_urls)
    news_items = gather_news_from_rss(rss_urls, file_name_prefix)

    # Generate podcast script
    podcast_script = generate_podcast_script(news_items[:50], model_name, temperature, seed, file_name_prefix) 
    print(podcast_script)

    # Convert text to speech and get the audio filename
    audio_filename = text_to_speech(podcast_script, file_name_prefix)

    # Play the generated audio
    # play_audio(audio_filename) 

    # Derive the podcast script filename from the audio filename
    #script_filename = audio_filename.replace(".mp3", ".txt")

    # Save the script to a file
    #with open(script_filename, "w") as f:
    #    f.write(podcast_script)

    # Send the audio and script to the Telegram channel
    send_to_telegram(audio_filename, podcast_script)  # <-- Call the function to send the files to Telegram

    # Generated Headlines
    headlines = generate_headlines(podcast_script, model_name, temperature, seed)

    # Publish the audio to Spreaker
    podcast_description = f"{headlines}\n\n{podcast_script}"
    publish_to_spreaker(audio_filename, podcast_description)  # <-- Call the function to publish the audio to Spreaker

    # Publish to Mastodon
    #post_status_with_audio(audio_filename)
    post_status_with_audio(audio_filename, headlines)
