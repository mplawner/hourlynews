from mastodon import Mastodon
from datetime import datetime
from config_handler import (
    read_mastodon_instance_url_from_config,
    read_mastodon_client_id_from_config,
    read_mastodon_client_secret_from_config,
    read_mastodon_access_token_from_config
)
import time

def post_status_with_audio(audio_path, headlines):
    # Read configuration values from config.txt
    instance_url = read_mastodon_instance_url_from_config()
    client_id = read_mastodon_client_id_from_config()
    client_secret = read_mastodon_client_secret_from_config()
    access_token = read_mastodon_access_token_from_config()

    # Initialize the Mastodon API client with the retrieved configurations
    mastodon = Mastodon(
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        api_base_url=instance_url
    )

    # Prepare the status text
    hour = datetime.now().strftime('%I %p')  # Gets the current hour in 12-hour format with AM/PM
    status_text = (f"The {hour} update from Israel Today: Ongoing War Report brought to you by Noa Levi on the ongoing war "
                   f"between Israel and Hamas following the October 7th massacre of Israeli civilians.\n\n"
                   f"{headlines}\n\n"
                   f"Podcast Details: https://www.spreaker.com/show/israel-today-ongoing-war-report \n\n"
                   f"Listen and Subscribe on your favorite podcast app.\n\n#Israel #Hamas #Gaza #Palestine")

    # Post audio with status
    media = mastodon.media_post(audio_path, mime_type='audio/mpeg')
    time.sleep(15)  # wait for 15 seconds to ensure the media has been processed
    mastodon.status_post(status_text, media_ids=media['id'])
