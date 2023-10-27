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

if __name__ == "__main__":
    # Reading RSS URLs from an OPML file
    rss_urls = extract_rss_urls_from_opml("subscriptions.opml")

    # Gathering news
    news_items = gather_news_from_rss(rss_urls)

    # Generate podcast script
    podcast_script = generate_podcast_script(news_items[:50])  # Considering top 10 news items for the script
    print(podcast_script)

    # Convert text to speech and get the audio filename
    audio_filename = text_to_speech(podcast_script)

    # Play the generated audio
    # play_audio(audio_filename)  <-- Commented out as you had it commented

    # Derive the podcast script filename from the audio filename
    script_filename = audio_filename.replace(".mp3", ".txt")

    # Save the script to a file
    with open(script_filename, "w") as f:
        f.write(podcast_script)

    # Send the audio and script to the Telegram channel
    send_to_telegram(audio_filename, podcast_script)  # <-- Call the function to send the files to Telegram

    # Generated Headlines
    headlines = generate_headlines(podcast_script)

    # Publish the audio to Spreaker
    podcast_description = f"{headlines}\n\n{podcast_script}"
    publish_to_spreaker(audio_filename, podcast_description)  # <-- Call the function to publish the audio to Spreaker

    # Publish to Mastodon
    post_status_with_audio(audio_filename)
