# Responsible for generating the podcast script from the gathered news.

from config_handler import read_openai_key_from_config
from config_handler import read_system_message_from_config
from config_handler import read_user_message_from_config
from datetime import datetime
import openai
import pytz  # Make sure you have this library installed

def get_current_time_ny():
    # Get the current time in New York timezone
    ny_timezone = pytz.timezone('America/New_York')
    current_time = datetime.now(ny_timezone)
    formatted_time = current_time.strftime('%I:%M %p')
    return formatted_time

def format_to_bulleted_list(headlines):
    # Removing the numbering and converting to bulleted list
    bulleted_list = ["- " + headline.split('. ', 1)[-1] for headline in headlines]
    return '\n'.join(bulleted_list)

def generate_headlines(podcast_script, model_name, temperature, seed):
    """
    Generate a bullet list of headlines from a podcast script using gpt-3.5-turbo.
    
    Args:
        podcast_script (str): The script of the news podcast.
    
    Returns:
        list: A list of headlines.
    """
    # Initialize OpenAI API from the config file
    openai.api_key = read_openai_key_from_config()

    # Construct a conversation with the model
    message1 = {
        "role": "system",
        "content": "You are a news headline generator, providing concise and objective headlines."
    }

    message2 = {
        "role": "user",
        "content": f"Given the news report: '{podcast_script}', provide a succinct bullet list of headlines:"
    }

    # Call OpenAI API
    response = openai.ChatCompletion.create(
        model=model_name,
        temperature=temperature,
        seed=seed,
        messages=[message1, message2]
    )

    # Extract headlines from the response
    # This assumes the model responds with headlines separated by new lines.
    headlines = response.choices[0].message['content'].strip().split('\n')

    formatted_headlines = format_to_bulleted_list(headlines)


    #current_hour = datetime.now().hour

    # Add the introduction with the current time in New York
    intro = f"Headlines from the news at {get_current_time_ny()} in New York."

    return f"{intro}\n\n{formatted_headlines}"

