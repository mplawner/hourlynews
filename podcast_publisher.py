import requests
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import os
import random
import eyed3
import string

logger = logging.getLogger(__name__)

# Constants
SPREAKER_API_ENDPOINT = "https://api.spreaker.com/v2"
TOKEN_URL = "https://api.spreaker.com/oauth2/token"
AUTH_URL = "https://www.spreaker.com/oauth2/authorize"
REFRESH_TOKEN_FILE = "refresh_token.txt"

# Global variables
access_token = None
refresh_token = None
oauth_code = None

def get_id3_metadata(audio_file_path):
    audiofile = eyed3.load(audio_file_path)
    title = audiofile.tag.title if audiofile.tag.title else "Automated Podcast Episode"
    description = audiofile.tag.comments.get("") if audiofile.tag.comments else "Automated podcast description."  # Assuming the default description frame
    return title, description

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global oauth_code
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        query = self.path.split('?', 1)[-1]
        parameters = parse_qs(query)
        if 'code' in parameters:
            oauth_code = parameters['code'][0]
            self.wfile.write(b"Authenticated successfully! You can close this window/tab.")
        else:
            self.wfile.write(b"Failed to authenticate. Please try again.")

def start_local_server():
    server_address = ('0.0.0.0', 8080)
    httpd = HTTPServer(server_address, OAuthHandler)
    logging.info("Starting local server...")
    httpd.handle_request()  # Only handle one request and then exit

def save_refresh_token(token):
    with open(REFRESH_TOKEN_FILE, 'w') as file:
        file.write(token)

def load_refresh_token():
    if os.path.exists(REFRESH_TOKEN_FILE):
        with open(REFRESH_TOKEN_FILE, 'r') as file:
            return file.read().strip()
    return None

def generate_random_string(length=32):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def get_spreaker_access_token(spreaker_client_id, spreaker_client_secret, show_id, spreaker_redirect_uri):
    global access_token
    global refresh_token

    # If access_token exists, just return it
    if access_token:
        logging.info("Access token exists")
        return access_token

    # If refresh_token exists, try to get a new access_token
    if not refresh_token:
        logging.info("Refresh token exists, attempting to get a new access token")
        refresh_token = load_refresh_token()

    if refresh_token:
        payload = {
            'client_id': spreaker_client_id,
            'client_secret': spreaker_client_secret, 
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        response = requests.post(TOKEN_URL, data=payload)
        if response.status_code == 200:
            data = response.json()
            access_token = data['access_token']
            refresh_token = data.get('refresh_token', refresh_token)  # Update if present
            save_refresh_token(refresh_token)
            return access_token

    # User intervention
    logging.info("User intervention required")
    state = generate_random_string()
    print("Please visit the following URL in a browser to authenticate:")
    auth_url = f"{AUTH_URL}?client_id={spreaker_client_id}&response_type=code&state={state}&scope=basic&redirect_uri={spreaker_redirect_uri}"
    print(auth_url)

    # Start the local server to catch the callback
    start_local_server()

    # Check if the global `oauth_code` variable has been set
    if not oauth_code:
        logger.error("Failed to retrieve the OAuth code from the callback.")
        raise Exception("Failed to retrieve the OAuth code from the callback.")

    # Exchange the code for an access_token and refresh_token
    payload = {
        'client_id': spreaker_client_id,
        'client_secret': spreaker_client_secret,
        'code': oauth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': spreaker_redirect_uri
    }
    response = requests.post(TOKEN_URL, data=payload)
    if response.status_code == 200:
        data = response.json()
        access_token = data['access_token']
        refresh_token = data['refresh_token']
        save_refresh_token(refresh_token)
        return access_token
    else:
        logger.error("Failed to obtain access token. Status code: %s, Response: %s", response.status_code, response.text)
        raise Exception("Failed to obtain access token.")

def publish_to_spreaker(audio_file_path, podcast_script, spreaker_client_id, spreaker_client_secret, show_id, spreaker_redirect_uri):
    token = get_spreaker_access_token(spreaker_client_id, spreaker_client_secret, show_id, spreaker_redirect_uri)

    title, _ = get_id3_metadata(audio_file_path) 

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Upload the episode
    with open(audio_file_path, 'rb') as audio_file:
        data = {
            'show_id': show_id,
            'title': title,  # use extracted title
            'description': podcast_script,  # use the provided podcast script as description
            'type': 'audio/mpeg'
        }
        files = {
            'media_file': audio_file
        }
        upload_response = requests.post(f"{SPREAKER_API_ENDPOINT}/shows/{show_id}/episodes", headers=headers, data=data, files=files)
        upload_response.raise_for_status()

        episode_info = upload_response.json()
        return episode_info['response']['episode']['episode_id']
