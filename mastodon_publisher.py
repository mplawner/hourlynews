import logging
from re import I
from mastodon import Mastodon
from datetime import datetime

logger = logging.getLogger(__name__)

def truncate_text_to_limit(main_text, limit):
    if len(main_text) > limit:
        logging.info(f"Headlines was truncated due to being {len(main_text)} characters")
        truncated_text = main_text[:limit-3] + "..."
    else:
        logging.info("Headlines were not truncated")
        truncated_text = main_text
    return truncated_text

def post_status_with_audio(headlines, 
                           instance_url, client_id, client_secret, access_token, 
                           show_title, hashtags, embedded_url, podcast_url, 
                           podcast_apple, podcast_spotify, podcast_google, podcast_amazon):

    # Initialize the Mastodon API client with the retrieved configurations
    mastodon = Mastodon(
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        api_base_url=instance_url
    )

    # Prepare the status text
    hour = datetime.now().strftime('%I %p')  # Gets the current hour in 12-hour format with AM/PM

    status_base_text = (f"\nListen to the {hour} update of {show_title} here: {embedded_url}\n"
                        f"Click on the (i) for the full transcript and links to sources.\n\n"
                        f"Listen and Subscribe on your favorite podcast app:\n"
                        f"- On Apple Podcasts: {podcast_apple}\n"
                        f"- On Spotify: {podcast_spotify}\n"
                        f"- On Amazon Music/Audible: {podcast_amazon}\n"
                        f"- On Google Music: {podcast_google}\n\n"
                        f"Podcast Details: {podcast_url}\n"
                        f"{hashtags}")

    #full_text = f"{status_base_text}\n{headlines}"
    #print(full_text)    
    
    # URL is fixed at 23 characters
    headline_limit = (1008 - len(status_base_text) +
                             len(embedded_url) - 23 + 
                             len(podcast_apple) - 23 + 
                             len(podcast_spotify) - 23 + 
                             len(podcast_amazon) - 23 + 
                             len(podcast_google) - 23 + 
                             len(podcast_url) - 23) 

    logging.info(f"Limiting headline to {headline_limit} characters.")

    headline_trunc = truncate_text_to_limit(headlines, headline_limit)   
    
    status_text = f"{headline_trunc}{status_base_text}"
    #print(status_text)

    # Post audio with status
    #media = mastodon.media_post(audio_path, mime_type='audio/mpeg')
    #time.sleep(15)  # wait for 15 seconds to ensure the media has been processed
    #mastodon.status_post(status_text, media_ids=media['id'])
    mastodon.status_post(status_text)
