import logging
import tweepy
from datetime import datetime
#from re import I

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
                           api_key, api_secret_key, access_token, access_token_secret,
                           show_title, hashtags, embedded_url, podcast_url, 
                           podcast_apple, podcast_spotify, podcast_google, podcast_amazon):

    # Authenticate to the Twitter API
    auth = tweepy.OAuthHandler(api_key, api_secret_key)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    # Check if authentication was successful
    try:
        api.verify_credentials()
        logging.info("Authentication to Twitter API successful")
    except:
        logging.error("Error during authentication")
        return

    # Prepare the status text
    hour = datetime.now().strftime('%I %p')  # Gets the current hour in 12-hour format with AM/PM

    status_base_text = (f"\nListen to the {hour} update of {show_title} here: {embedded_url}\n"
                        f"See show notes for the full transcript and links to sources.\n"
                        f"Listen and Subscribe: {podcast_apple}\n"
                        f"{hashtags}")

    # URL is fixed at 23 characters
    headline_limit = (280 - len(status_base_text) +
                             len(embedded_url) - 23 + 
                             len(podcast_apple) - 23)

    logging.info(f"Limiting headline to {headline_limit} characters.")

    headline_trunc = truncate_text_to_limit(headlines, headline_limit)   
    
    status_text = f"{headline_trunc}{status_base_text}"

    try:
        api.update_status(status_text)
        logging.info("Successfully posted to Twitter")
    except Exception as e:
        logging.error(f"Error posting to Twitter: {e}")
