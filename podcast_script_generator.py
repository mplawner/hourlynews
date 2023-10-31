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

def generate_podcast_script(news_items):
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

    current_hour = datetime.now().hour

    # Decide the model based on the hour
    if 6 <= current_hour < 16: 
        model_name = "gpt-4"
    else:
        model_name = "gpt-3.5-turbo"

    # Call OpenAI API
    response = openai.ChatCompletion.create(
        model=model_name,
        messages=[message1, message2]
    )

    news_report = response.choices[0].message['content'].strip()
    
    # Add the introduction with the current time in New York
    intro = f"The time is now {get_current_time_ny()} in New York, I'm Noa Levi and this is the latest 'Israel Today: Ongoing War Report'."
    
    # Define the outro
    outro = (f"That concludes this update of the 'Israel Today: Ongoing War Report'. "
            f"Thank you for joining us for this hour's update. As events continue to unfold, we're committed to bringing "
            f"you timely, accurate, and in-depth coverage. Please subscribe and follow us wherever you listen to your podcasts to stay up to date. "
            f"This news report was generated on a Raspberry Pi 3b using OpenAI's {model_name} model "
            f"and both Microsoft and Piper text-to-speech engines. Both intro and outro music is used "
            f"under the Creative Commons 4.0 Attribution license from Code Box and Mansardian, respectively. "
            f"The code for generating this podcast is available under the MIT license and can be found "
            f"in Github. See the Podcast description for the link to the repository. "
            f"As this is an AI-generated report, there may be occasional inaccuracies or errors. We always recommend "
            f"checking multiple sources to get the most accurate picture of any situation. "
            f"Stay informed and stay safe. I'm Noa Levi, thank you for listening.")
    
    full_script = f"{intro}\n\n{news_report}\n\n{outro}"
    
    # Replace "U.S." with "US"
    full_script = full_script.replace("U.S.", "US")

    return full_script
