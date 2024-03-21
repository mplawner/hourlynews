# Responsible for generating the podcast script from the gathered news.

from re import I
import logging
from rss_parser import save_to_json
from datetime import datetime
import openai
import pytz 
import json

logger = logging.getLogger(__name__)

def get_current_time_ny():
    # Get the current time in New York timezone
    ny_timezone = pytz.timezone('America/New_York')
    current_time = datetime.now(ny_timezone)
    formatted_time = current_time.strftime('%I:%M %p')
    return formatted_time

def read_replacements_from_file(filepath):
    replacements = {}
    with open(filepath, 'r') as file:
        for line in file:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                # Join back all parts except the first one, allowing for replacements with commas
                original, replacement = parts[0], ','.join(parts[1:]).strip()
                replacements[original] = replacement
            else:
                logger.warning(f"Invalid replacement format in line: {line}")
    return replacements

def perform_replacements(text, replacements):
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    return text

#def generate_podcast_script(news_items):
def generate_podcast_script(news_items, model_name, temperature, seed, 
                            file_prefix, key, system_message_content, user_message_content,
                            show_title, host, host_tagline, disclaimer):
    logger.info("Podcast script generation started")
    openai.api_key = key

    # Combine all news items into a single coherent input
    #combined_news = "; ".join([f"{item['title']} {item['summary']}" for item in news_items])
    #combined_news = "; ".join([f"{item['summary']} " for item in news_items])
    combined_news = "; ".join([f"{item['title']} {item['summary']} {item['article']}" for item in news_items])

    # Construct a conversation with the model
    message1 = {
        "role": "system",
        "content": system_message_content
    }

    message2 = {
        "role": "user",
        "content": f"The current time is {get_current_time_ny()}. {user_message_content} {combined_news}"
    }

    # Call OpenAI API
    response = openai.ChatCompletion.create(
        model=model_name,
        temperature=temperature,
        seed=seed,
        messages=[message1, message2]
    )

    # Save the message to a JSON file
    messages_to_save = [message1, message2]
    save_to_json(messages_to_save, f"{file_prefix}-messages.json")

    # Save the response to a JSON file
    response_data = response.to_dict() 
    save_to_json(response_data, f"{file_prefix}-openai_response.json")

    news_report = response.choices[0].message['content'].strip()
    
    # Add the introduction with the current time in New York
    intro = f"The time is now {get_current_time_ny()} in New York, I'm {host} and this is the latest {show_title}."
    
    # Define the outro
    outro = (f"Thank you for tuning in to this {show_title} update.\nI'm {host}. {host_tagline}\n{disclaimer}")
    
    full_script = f"{intro}\n\n{news_report}\n\n{outro}"
    
    # Read replacements from file
    replacements = read_replacements_from_file('replacements.txt')
    
    # Perform replacements
    full_script = perform_replacements(full_script, replacements)

    script_filename = f"{file_prefix}-podcast_script.txt"
    with open(script_filename, 'w') as f:
        f.write(full_script)

    logger.info("Podcast script generation completed")
    return full_script
