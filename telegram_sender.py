import requests
import logging

logger = logging.getLogger(__name__)

class TelegramSender:
    BASE_URL = "https://api.telegram.org"
    MAX_MESSAGE_LENGTH = 4096

    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = channel_id
        self.url = f"{self.BASE_URL}/bot{self.token}"

    def send_message(self, text):
        link = "https://widget.spreaker.com/player?show_id=5985229&theme=dark&playlist=false&playlist-continuous=false&chapters-image=true&episode_image_position=right&hide-logo=false&hide-likes=false&hide-comments=false&hide-sharing=false&hide-download=true"
        text = link + "\n\n" + text
        endpoint = f"{self.url}/sendMessage"
        if len(text) > self.MAX_MESSAGE_LENGTH:
            text = text[:self.MAX_MESSAGE_LENGTH]  # Truncate text to fit the limit
            logging.warning("Text truncated due to length exceeding Telegram's limit.")

        payload = {
            "chat_id": self.channel_id,
            "text": text
        }
        response = requests.post(endpoint, data=payload)
        if not response.ok:
            logging.error(f"Failed to send message: {response.text}")
        return response.json()

    def send_audio(self, audio_path, caption=None):
        endpoint = f"{self.url}/sendAudio"
        with open(audio_path, 'rb') as audio_file:
            files = {"audio": audio_file}
            payload = {
                "chat_id": self.channel_id,
                "caption": caption[:self.MAX_MESSAGE_LENGTH] if caption else None
            }
            response = requests.post(endpoint, data=payload, files=files)
            if not response.ok:
                logging.error(f"Failed to send audio: {response.text}")
            return response.json()

def send_to_telegram(podcast_description, token, channel_id):

    telegram = TelegramSender(token, channel_id)

    # Send the script as a message
    telegram.send_message(podcast_description)

    # Send the audio file
    # telegram.send_audio(audio_filename, caption="Hourly News Update")
