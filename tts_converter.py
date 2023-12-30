import os
from re import I
import logging
import regex as re
# import requests
from pydub import AudioSegment
# import urllib.parse
import random
import string
import subprocess
from datetime import datetime
import tempfile
import eyed3
from podcast_script_generator import read_replacements_from_file, perform_replacements
# from ad_generator import create_ads

logger = logging.getLogger(__name__)

def random_string(length=10):
    """Generate a random string of given length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

# def fetch_audio_from_festival(sentence):
#     """Converts text to speech using Festival and returns the audio segment."""
#     print(f"Generating audio for: {sentence}")  # Log the sentence for debugging purposes
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
#         subprocess.run(["text2wave", "-o", temp_wav.name], input=sentence, encoding="utf-8", check=True)
#         return AudioSegment.from_wav(temp_wav.name)

def fetch_audio_from_piper(sentence):
    """Converts text to speech using Piper and returns the audio segment."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
        # Using a subprocess pipeline to pass the sentence to the Piper command
        with open(temp_wav.name, 'w') as f:
            proc1 = subprocess.Popen(['echo', sentence], stdout=subprocess.PIPE)  # Echo the sentence
            proc2 = subprocess.Popen(['piper', '--model', 'en_US-lessac-medium', '--output_file', temp_wav.name], stdin=proc1.stdout)
            proc1.stdout.close()  # Ensure that proc1 will receive a SIGPIPE if proc2 exits
            proc2.communicate()  # Wait for the second process to complete
        
        return AudioSegment.from_wav(temp_wav.name)

def fetch_audio_from_edge_tts(sentence, voice="en-US-MichelleNeural", rate="+0%"):
    """Fetch audio from Edge TTS."""
    if len(sentence) > 280: 
        logging.info(f"Sentence length exceeded 280 characters ({len(sentence)} characters), processing TTS locally with Piper")
        return fetch_audio_from_piper(sentence)

    temp_filename = f"/tmp/{random_string()}.mp3"
    
    try:
        subprocess.run(
            ["edge-tts", "--voice", voice, "--rate", rate, "--text", sentence, "--write-media", temp_filename],
            check=True,
            stdout=subprocess.DEVNULL,  # Redirects stdout to nowhere
            stderr=subprocess.DEVNULL  # Optionally, redirects stderr as well
        )
        segment = AudioSegment.from_mp3(temp_filename)
    except Exception as e:
        logger.exception(f"Error processing MP3 data from edge-tts: {str(e)}")
        raise e
    finally:
        os.remove(temp_filename)

    return segment

# def fetch_audio_from_google(sentence):
#     """Fetch audio from Google TTS."""
#     if len(sentence) > 200:
#         return fetch_audio_from_festival(sentence)

#     tts_url = f"http://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q={urllib.parse.quote(sentence)}&tl=en"
#     response = requests.get(tts_url, headers={"User-Agent": "Mozilla/5.0"})
    
#     if response.status_code != 200:
#         print(f"Failed for sentence: {sentence}")  # Log the problematic sentence
#         raise Exception(f"Failed to fetch audio from Google. HTTP Status Code: {response.status_code}. Content: {response.content}")
    
#     temp_filename = f"/tmp/{random_string()}.mp3"
#     with open(temp_filename, 'wb') as temp_mp3:
#         temp_mp3.write(response.content)
        
#     try:
#         segment = AudioSegment.from_mp3(temp_filename)
#     except Exception as e:
#         raise Exception(f"Error processing MP3 data: {str(e)}")
#     finally:
#         os.remove(temp_filename)
        
#     return segment

def split_into_sentences(tts):
    """Splits the text into sentences while preserving original punctuation."""
    # Use a regex pattern that splits at [.!?] but keeps the punctuation with the sentence
    sentences = re.split(r'(?<!Mr|Mrs|Dr|Ms|St|Ave|Rd|Blvd|etc|e\.g|i\.e|et al|vs|Prof|Gen|Capt|Lt|Sr|Jr|Ph\.D|M\.D|B\.A|M\.A|D\.D\.S|[\d]|U\.S)([.!?])', tts)
    
    # Reattach the punctuation to the sentences and return non-empty sentences
    return [sentence + next_punctuation for sentence, next_punctuation in zip(sentences[::2], sentences[1::2]) if sentence.strip()]

def add_id3_tags(filename, host, show_title, show_description):
    """Adds ID3 tags to the provided mp3 file."""
    # Load the mp3 file using eyed3
    audiofile = eyed3.load(filename)

    # Set ID3 tags
    audiofile.tag.title = f"{show_title} - Update from {datetime.now().strftime('%Y-%m-%d')} at {datetime.now().strftime('%H:%M')}"
    audiofile.tag.artist = host
    audiofile.tag.comments.set(show_description)
    # Add cover art
    # with open("cover.jpeg", "rb") as cover_art:
    #    audiofile.tag.images.set(3, cover_art.read(), "image/jpeg")

    # Save the changes to the file
    audiofile.tag.save()

def text_to_speech(text, file_name_prefix, 
                   intro_music_file, outro_music_file,
                   host, host_voice, show_title, show_description):
    """Converts a given text to speech and returns the audio filename."""
    logging.info("Begin text to speech process")

    pronunciations = read_replacements_from_file('pronounce.txt')
    text = perform_replacements(text, pronunciations)
    logging.info("Completed pronounciation text replacements")

    # Using EDGE TTS requires splitting sentences to avoid going over limit number of characters
    sentences = split_into_sentences(text)
    logging.info("Script split into sentences")

    combined_audio = None
    for sentence in sentences:
        segment = fetch_audio_from_edge_tts(sentence, host_voice, rate="+0%")
        if combined_audio is None:
            combined_audio = segment
        else:
            combined_audio += segment
    logging.info("Main script audio complete")

    # Speed up the audio by 1.25 times
    #sped_up_audio = combined_audio.speedup(playback_speed=1.25)

    # Load intro and outro music
    intro_music = AudioSegment.from_wav(intro_music_file)
    outro_music = AudioSegment.from_wav(outro_music_file)

    # Combine main podcast content
    final_audio = intro_music + combined_audio + outro_music
    logging.info("Added intro and outro music")

    # # Generate ad copies and convert them to audio
    # ad_copies = create_ads(file_name_prefix)

    # for ad_copy in ad_copies:
    #     # Split each ad copy into sentences
    #     ad_sentences = split_into_sentences(ad_copy)

    #     # Convert each sentence in the ad copy to audio and append to final audio
    #     for sentence in ad_sentences:
    #         ad_audio_segment = fetch_audio_from_edge_tts(sentence, voice="en-GB-LibbyNeural", rate="+15%")
    #         final_audio += ad_audio_segment
    
    filename_timestamp = f"{file_name_prefix}-audio.mp3"
    final_audio.export(filename_timestamp, format="mp3")
    logging.info(f"Written audio file {filename_timestamp}")

    # Add ID3 tags to the mp3
    add_id3_tags(filename_timestamp, host, show_title, show_description)
    logging.info(f"ID3 tags added to audio file")

    logging.info("Completed text to speech process")
    return filename_timestamp
