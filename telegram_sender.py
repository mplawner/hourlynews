import requests
import config_handler
import logging

# Set up basic logging
logging.basicConfig(filename='telegram_sender.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

class TelegramSender:
    BASE_URL = "https://api.telegram.org"
    MAX_MESSAGE_LENGTH = 4096

    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = channel_id
        self.url = f"{self.BASE_URL}/bot{self.token}"

    def send_message(self, text):
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

def send_to_telegram(audio_filename, podcast_description):
    TOKEN = config_handler.read_telegram_token_from_config()
    CHANNEL_ID = config_handler.read_telegram_chat_id_from_config()

    telegram = TelegramSender(TOKEN, CHANNEL_ID)

    # Send the script as a message
    telegram.send_message(podcast_description)

    # Send the audio file
    telegram.send_audio(audio_filename, caption="Hourly News Update")
