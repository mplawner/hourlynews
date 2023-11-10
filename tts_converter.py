import os
from re import I
from config_handler import read_openai_key_from_config
import regex as re
import requests
from pydub import AudioSegment
import urllib.parse
import random
import string
import subprocess
from datetime import datetime
import tempfile
import eyed3
import openai

def random_string(length=10):
    """Generate a random string of given length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def fetch_audio_from_festival(sentence):
    """Converts text to speech using Festival and returns the audio segment."""
    print(f"Generating audio for: {sentence}")  # Log the sentence for debugging purposes
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
        subprocess.run(["text2wave", "-o", temp_wav.name], input=sentence, encoding="utf-8", check=True)
        return AudioSegment.from_wav(temp_wav.name)

def fetch_audio_from_piper(sentence):
    """Converts text to speech using Piper and returns the audio segment."""
    print(f"Generating audio for: {sentence}")  # Log the sentence for debugging purposes
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
        # Using a subprocess pipeline to pass the sentence to the Piper command
        with open(temp_wav.name, 'w') as f:
            proc1 = subprocess.Popen(['echo', sentence], stdout=subprocess.PIPE)  # Echo the sentence
            proc2 = subprocess.Popen(['piper', '--model', 'en_US-lessac-medium', '--output_file', temp_wav.name], stdin=proc1.stdout)
            proc1.stdout.close()  # Ensure that proc1 will receive a SIGPIPE if proc2 exits
            proc2.communicate()  # Wait for the second process to complete
        
        return AudioSegment.from_wav(temp_wav.name)

def fetch_audio_from_edge_tts(sentence):
    """Fetch audio from Edge TTS."""
    if len(sentence) > 280:  # If the sentence length is over 280 characters, send it to Festival
        #return fetch_audio_from_festival(sentence)
        return fetch_audio_from_piper(sentence)

    print(f"Fetching audio for: {sentence}")  # Log the sentence for debugging purposes
    
    temp_filename = f"/tmp/{random_string()}.mp3"
    
    try:
        subprocess.run(
            ["edge-tts", "--voice", "en-US-MichelleNeural", "--text", sentence, "--write-media", temp_filename],
            check=True,
            stdout=subprocess.DEVNULL,  # Redirects stdout to nowhere
            stderr=subprocess.DEVNULL  # Optionally, redirects stderr as well
        )
        segment = AudioSegment.from_mp3(temp_filename)
    except Exception as e:
        raise Exception(f"Error processing MP3 data from edge-tts: {str(e)}")
    finally:
        os.remove(temp_filename)
        
    return segment


def fetch_audio_from_google(sentence):
    """Fetch audio from Google TTS."""
    if len(sentence) > 200:
        return fetch_audio_from_festival(sentence)

    print(f"Fetching audio for: {sentence}")  # Log the sentence for debugging purposes

    tts_url = f"http://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q={urllib.parse.quote(sentence)}&tl=en"
    response = requests.get(tts_url, headers={"User-Agent": "Mozilla/5.0"})
    
    if response.status_code != 200:
        print(f"Failed for sentence: {sentence}")  # Log the problematic sentence
        raise Exception(f"Failed to fetch audio from Google. HTTP Status Code: {response.status_code}. Content: {response.content}")
    
    temp_filename = f"/tmp/{random_string()}.mp3"
    with open(temp_filename, 'wb') as temp_mp3:
        temp_mp3.write(response.content)
        
    try:
        segment = AudioSegment.from_mp3(temp_filename)
    except Exception as e:
        raise Exception(f"Error processing MP3 data: {str(e)}")
    finally:
        os.remove(temp_filename)
        
    return segment

def split_into_sentences(tts):
    """Splits the text into sentences using regular expressions."""
    #return [s.strip() for s in re.split(r'(?<!Mr|Mrs|Dr|Ms|St|Ave|Rd|Blvd|etc|e\.g|i\.e|et al|vs|Prof|Gen|Capt|Lt|Sr|Jr|Ph\.D|M\.D|B\.A|M\.A|D\.D\.S|[\d])[.!?]', tts) if s]
    return [s.strip() for s in re.split(r'(?<!Mr|Mrs|Dr|Ms|St|Ave|Rd|Blvd|etc|e\.g|i\.e|et al|vs|Prof|Gen|Capt|Lt|Sr|Jr|Ph\.D|M\.D|B\.A|M\.A|D\.D\.S|[\d]|U\.S)[.!?]', tts) if s]
    #return [s.strip() for s in re.split(r'(?<!Mr|Mrs|Dr|Ms|St|Ave|Rd|Blvd|etc|e\.g|i\.e|et al|vs|Prof|Gen|Capt|Lt|Sr|Jr|Ph\.D|M\.D|B\.A|M\.A|D\.D\.S|[\d]|U\.S)[.!?,]', tts) if s]

def add_id3_tags(filename):
    """Adds ID3 tags to the provided mp3 file."""
    # Load the mp3 file using eyed3
    audiofile = eyed3.load(filename)

    # Set ID3 tags
    audiofile.tag.title = f"Israel Today: Ongoing War Report - Update from {datetime.now().strftime('%Y-%m-%d')} at {datetime.now().strftime('%H:%M')}"
    audiofile.tag.artist = "Noa Levi"
    description_text = "This is an hourly update podcast covering the Israel-Hamas war. For more updates, tune in hourly."
    audiofile.tag.comments.set(description_text)
    # Add cover art
    # with open("cover.jpeg", "rb") as cover_art:
    #    audiofile.tag.images.set(3, cover_art.read(), "image/jpeg")

    # Save the changes to the file
    audiofile.tag.save()

def transliterate_names(text):
    """
    Uses OpenAI's GPT model to transliterate Hebrew and Arabic names and places.
    """
    # Initialize OpenAI API from the config file
    openai.api_key = read_openai_key_from_config()

    # Construct a conversation with the model
    message1 = {
        "role": "system",
        "content": "Your task is to directly replace names and places in a script with their transliterated versions, using Israeli dialect for Hebrew names and Palestinian dialect for Arabic names. Do not add any explanations or additional text."
    }

    message2 = {
        "role": "user",
        "content": f"Here is the script: '{text}'. Identify all Hebrew and Arabic names and places other than commonly known names and places to an English-speaking audience (like Israel or Gaza), and directly replace them with their transliterated versions according to Israeli and Palestinian pronunciations."
    }

    try:
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            #temperature=temperature,
            #seed=seed,
            messages=[message1, message2]
        )

        # Extract the transliterated text from the response
        # Ensuring that the response is parsed correctly
        transliterated_text = response.choices[0].message['content'].strip() if response.choices[0].message else text

        print(transliterated_text)

        return transliterated_text
    except Exception as e:
        print(f"An error occurred while attempting to transliterate: {e}")
        return text

def text_to_speech(text, file_name_prefix):
    """Converts a given text to speech and returns the audio filename."""

    #text = transliterate_names(text)  # Transliterate names and places before splitting

    sentences = split_into_sentences(text)
    
    combined_audio = None
    for sentence in sentences:
        #segment = fetch_audio_from_google(sentence)
        segment = fetch_audio_from_edge_tts(sentence)  # Use Edge TTS instead of Google TTS
        if combined_audio is None:
            combined_audio = segment
        else:
            combined_audio += segment

    # Speed up the audio by 1.25 times
    #sped_up_audio = combined_audio.speedup(playback_speed=1.25)

    # Load intro and outro music
    intro_music = AudioSegment.from_wav("61322__mansardian__news-end-signature-shorter.wav")
    outro_music = AudioSegment.from_wav("460424__jay_you__jingle-news.wav")

    # Combine audio: intro + sped up speech + outro
    #final_audio = intro_music + sped_up_audio + outro_music
    final_audio = intro_music + combined_audio + outro_music
    
    #filename_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-hourly.mp3")
    filename_timestamp = f"{file_name_prefix}-audio.mp3"
    final_audio.export(filename_timestamp, format="mp3")
    
    # Add ID3 tags to the mp3
    add_id3_tags(filename_timestamp)

    return filename_timestamp
