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
        #"content": "You are a helpful assistant that generates the main body of podcast scripts based on recent news summaries, excluding intros and outros."
        #"content": "You are a news summarizer, providing concise and objective summaries of current events and important news stories from the ongoing war between Israel and Hamas. Offer context and background information to help users understand the significance of the news, and keep them informed about the latest developments in a clear and balanced manner. The response should not include emojis, markdown language, or abbreviations. "
    }

    message2 = {
        "role": "user",
        "content": f"{user_message_content} {combined_news}"
        #"content": f"Based on the following news from the last half hour, create the main body of a news report without any intros and outros:\n\n{combined_news}"
    }

    # Call OpenAI API
    #response = openai.ChatCompletion.create(
    #    model="gpt-3.5-turbo",
    #    messages=[message1, message2]
    #)
 
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
    outro = "That concludes this update of the 'Israel Today: Ongoing War Report'. Stay informed and stay safe. I'm Noa Levi, thank you for listening."
    
    #return f"{intro}\n\n{news_report}\n\n{outro}"
    full_script = f"{intro}\n\n{news_report}\n\n{outro}"

    # Replace "U.S." with "US"
    full_script = full_script.replace("U.S.", "US")

    return full_script
