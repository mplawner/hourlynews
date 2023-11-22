from re import I
from config_handler import read_openai_key_from_config,read_model_param_seed_from_config, read_model_param_temp_from_config
from rss_parser import save_to_json
import openai
import pytz 
import json
import csv
import os
import random

def generate_random_text():
    """Generates a random string for product name, value proposition, or tone."""
    texts = ['Amazing', 'Revolutionary', 'Innovative', 'Unique', 'Exclusive', 'Eco-friendly', 'State-of-the-art']
    return random.choice(texts)

def read_ads_file(file_path):
    """Reads the ads file and returns a list of ad details."""
    if not os.path.exists(file_path):
        return []

    ads = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            ad_product, ad_valueprop, ad_tone = row
            ad_product = ad_product if ad_product != 'NA' else "a fictitious product"
            ad_valueprop = ad_valueprop if ad_valueprop != 'NA' else "value"
            ad_tone = ad_tone if ad_tone != 'NA' else "appropriate for the fictitious product"
            ads.append((ad_product, ad_valueprop, ad_tone))
    return ads

def generate_ad_script(ad_product,ad_valueprop,ad_tone, model_name, temperature, seed, file_prefix):

    # Initialize OpenAI API from the config file
    openai.api_key = read_openai_key_from_config()

    # Construct a conversation with the model
    message1 = {
        "role": "system",
        "content": "You create the text for 15 second radio advertisement given a product, the product's value proposition, and the tone of the advertisement. You only provide the text of the ad. No intro, no stage direction, etc."
        #"content": "You create the text for 15 second radio advertisement in the style of the show Rick and Morty's Interdimensional Cable network, given a product, the product's value proposition, and the tone of the advertisement. You only provide the text of the ad. No intro, no stage direction, etc."
    }

    message2 = {
        "role": "user",
        "content": f"Create the text for a 15 second radio advertisement for {ad_product} that delivers {ad_valueprop}. The tone of the ad should be {ad_tone}. Only provide the ad text. Do not include an intro, stage direction, or anything other than the ad text."
        #"content": f"Create the text for a 15 second radio advertisement in the style of the show Rick and Morty's Interdimensional Cable network for {ad_product} that delivers {ad_valueprop}. The tone of the ad should be {ad_tone}. Only provide the text of the ad. No intro, no stage direction, etc."
    }

    # Call OpenAI API
    response = openai.ChatCompletion.create(
        model=model_name,
        #temperature=temperature,
        #seed=seed,
        messages=[message1, message2]
    )

    messages_to_save = [message1, message2]
    save_to_json(messages_to_save, f"{file_prefix}-ad_messages.json")

    # Save the response to a JSON file
    response_data = response.to_dict()  # Convert the OpenAI response to a dictionary
    save_to_json(response_data, f"{file_prefix}-ad_openai_response.json")

    ad_copy = response.choices[0].message['content'].strip()
    return ad_copy

def create_ads(file_prefix):

    model_name = "gpt-4-1106-preview"
    temperature = read_model_param_temp_from_config()
    seed = read_model_param_seed_from_config()

    ads = read_ads_file('ads.txt')
    if not ads:  # If the ads file is missing or empty, create a dummy ad
        ads = [("a fictitious product", "value", "appropriate for the fictitious product")]
        #ads = [(generate_random_text(), generate_random_text(), generate_random_text())]

    all_ad_copies = []
    for ad_product, ad_valueprop, ad_tone in ads:
        ad_copy = generate_ad_script(ad_product, ad_valueprop, ad_tone, model_name, temperature, seed, file_prefix)
        all_ad_copies.append(ad_copy)

    ad_filename = f"{file_prefix}-all_ads.txt"
    with open(ad_filename, 'w') as f:
        f.write('\n\n'.join(all_ad_copies))

    return all_ad_copies
