# Responsible for generating the podcast script from the gathered news.

#from re import I
from config_handler import read_openai_key_from_config
from config_handler import read_system_message_from_config
from config_handler import read_user_message_from_config
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

def save_response_to_json(response):
    # Convert the response to a dictionary
    data = response.to_dict()

    # Create a filename with the current timestamp
    filename = f"openai_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"OpenAI response saved to {filename}")

def read_replacements_from_file(filepath):
    replacements = {}
    with open(filepath, 'r') as file:
        for line in file:
            # Assuming each line contains "term to replace, replacement" format
            original, replacement = line.strip().split(',')
            replacements[original] = replacement
    return replacements

def perform_replacements(text, replacements):
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    return text

#def generate_podcast_script(news_items):
def generate_podcast_script(news_items, model_name, temperature, seed):

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
        "content": f"{user_message_content} {combined_news}"
    }

    # Call OpenAI API
    response = openai.ChatCompletion.create(
        model=model_name,
        temperature=temperature,
        seed=seed,
        messages=[message1, message2]
    )

    # Save the response to a JSON file
    save_response_to_json(response)

    news_report = response.choices[0].message['content'].strip()
    
    # Add the introduction with the current time in New York
    intro = f"The time is now {get_current_time_ny()} in New York, I'm Noa Levi and this is the latest 'Israel Today: Ongoing War Report'."
    
    # Define the outro
    outro = (f"Thank you for tuning in to this 'Israel Today: Ongoing War Report' update. Stay safe and informed. I'm Noa Levi. "
             f"Keep in mind that this AI-generated report may contain occasional inaccuracies, "
             f"so consult multiple sources for a comprehensive view. Find the code and more details in the podcast description.")
    
    full_script = f"{intro}\n\n{news_report}\n\n{outro}"
    
    # Replace "U.S." with "US"
    #full_script = full_script.replace("U.S.", "US")
 
    # Read replacements from file
    replacements = read_replacements_from_file('replacements.txt')
    
    # Perform replacements
    full_script = perform_replacements(full_script, replacements)


    return full_script
