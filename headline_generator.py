# Responsible for generating the podcast script from the gathered news.
import openai
import logging

logger = logging.getLogger(__name__)

def format_to_bulleted_list(headlines):
    bulleted_list = [headline.split('. ', 1)[-1] for headline in headlines]
    return '\n'.join(bulleted_list)

def generate_headlines(podcast_script, model_name, temperature, seed, key):
    logging.info("Begin generating headlines")

    # Initialize OpenAI API from the config file
    openai.api_key = key

    # Construct a conversation with the model
    message1 = {
        "role": "system",
        #"content": "You are a news headline generator, providing concise and objective headlines."
        "content": "You are a news headline generator, providing concise, attention grabbing headlines."
    }

    message2 = {
        "role": "user",
        #"content": f"Given the news report: '{podcast_script}', provide a succinct bullet list of headlines:"
        "content": f"Given the news report: '{podcast_script}', provide a succinct, attention grabbing, bulleted list of the top 3 headlines."
    }

    # Call OpenAI API
    response = openai.ChatCompletion.create(
        model=model_name,
        temperature=temperature,
        seed=seed,
        messages=[message1, message2]
    )

    # Extract headlines from the response
    headlines = response.choices[0].message['content'].strip().split('\n')

    formatted_headlines = format_to_bulleted_list(headlines)
    
    # Add the introduction
    #intro = f"Generated with: GPT Model {model_name} | Temperature {temperature} | Seed {seed}\n\nHEADLINES"
    intro = "HEADLINES"

    logging.info("Completed generating headlines")
    return f"{intro}\n{formatted_headlines}\n"
