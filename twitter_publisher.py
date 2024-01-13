import logging
#import tweepy
from datetime import datetime
from requests_oauthlib import OAuth1Session
import os
import json

logger = logging.getLogger(__name__)

def truncate_text_to_limit(main_text, limit):
    if len(main_text) > limit:
        logging.info(f"Headlines was truncated due to being {len(main_text)} characters")
        truncated_text = main_text[:limit-3] + "..."
    else:
        logging.info("Headlines were not truncated")
        truncated_text = main_text
    return truncated_text

def post_to_twitter(headlines, 
                           consumer_key, consumer_secret, access_token, access_token_secret,
                           show_title, hashtags, embedded_url, podcast_url, 
                           podcast_apple, podcast_spotify, podcast_google, podcast_amazon):

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

    # Set up OAuth
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret
    )

    # Making the request
    payload = {"text": status_text}
    response = oauth.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
    )

    if response.status_code != 201:
        logger.error(f"Request returned an error: {response.status_code} {response.text}")
        return

    logger.info("Successfully posted to Twitter")
    json_response = response.json()
    #logger.info("Twitter API Response: %s", json.dumps(json_response, indent=4, sort_keys=True))
