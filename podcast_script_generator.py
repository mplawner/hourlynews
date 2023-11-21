# Responsible for generating the podcast script from the gathered news.

#from re import I
from re import I
from config_handler import read_openai_key_from_config
from config_handler import read_system_message_from_config
from config_handler import read_user_message_from_config
from rss_parser import save_to_json
from datetime import datetime
import openai
import pytz 
import json

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
                print(f"Invalid replacement format in line: {line}")
    return replacements

def perform_replacements(text, replacements):
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    return text

#def generate_podcast_script(news_items):
def generate_podcast_script(news_items, model_name, temperature, seed, file_prefix):

    # Initialize OpenAI API from the config file
    openai.api_key = read_openai_key_from_config()

    # Combine all news items into a single coherent input
    combined_news = "; ".join([f"{item['title']} {item['summary']}" for item in news_items])

    # Retrieve system and user messages from the config file
    system_message_content = read_system_message_from_config()
    user_message_content = read_user_message_from_config()

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
    response_data = response.to_dict()  # Convert the OpenAI response to a dictionary
    save_to_json(response_data, f"{file_prefix}-openai_response.json")

    news_report = response.choices[0].message['content'].strip()
    
    # Add the introduction with the current time in New York
    intro = f"The time is now {get_current_time_ny()} in New York, I'm Noa Levi and this is the latest 'Israel Today: Ongoing War Report'."
    
    # Define the outro
    outro = (f"Thank you for tuning in to this 'Israel Today: Ongoing War Report' update. Stay safe and informed. I'm Noa Levi. "
             f"Keep in mind that this AI-generated report may contain occasional inaccuracies, "
             f"so consult multiple sources for a comprehensive view. Find the code and more details in the podcast description.")
    
    full_script = f"{intro}\n\n{news_report}\n\n{outro}"
    
    # Read replacements from file
    replacements = read_replacements_from_file('replacements.txt')
    
    # Perform replacements
    full_script = perform_replacements(full_script, replacements)

    script_filename = f"{file_prefix}-podcast_script.txt"
    with open(script_filename, 'w') as f:
        f.write(full_script)

    return full_script
