def read_key_from_config(key, filename='config.txt'):
    with open(filename, 'r') as file:
        for line in file:
            if line.startswith(f"{key}="):
                return line.split('=')[1].strip()
    return None  # Changed from raising an error to returning None
    # raise ValueError(f"{key} not found in config file!")

def read_openai_key_from_config(filename='config.txt'):
    return read_key_from_config("openai", filename)

def read_telegram_token_from_config(filename='config.txt'):
    return read_key_from_config("telegram_token", filename)

def read_telegram_chat_id_from_config(filename='config.txt'):
    return read_key_from_config("telegram_channel_id", filename)

def read_spreaker_client_id_from_config(filename='config.txt'):
    return read_key_from_config("spreaker_client_id", filename)

def read_spreaker_client_secret_from_config(filename='config.txt'):
    return read_key_from_config("spreaker_client_secret", filename)

def read_spreaker_show_id_from_config(filename='config.txt'):
    return read_key_from_config("spreaker_show_id", filename)

def read_spreaker_redirect_uri_from_config(filename='config.txt'):
    return read_key_from_config("spreaker_redirect_uri", filename)

def read_system_message_from_config(filename='config.txt'):
    return read_key_from_config("system_message", filename)

def read_user_message_from_config(filename='config.txt'):
    return read_key_from_config("user_message", filename)

def read_mastodon_instance_url_from_config(filename='config.txt'):
    return read_key_from_config("mastodon_instance_url", filename)

def read_mastodon_client_id_from_config(filename='config.txt'):
    return read_key_from_config("mastodon_client_id", filename)

def read_mastodon_client_secret_from_config(filename='config.txt'):
    return read_key_from_config("mastodon_client_secret", filename)

def read_mastodon_access_token_from_config(filename='config.txt'):
    return read_key_from_config("mastodon_access_token", filename)

def read_model_param_seed_from_config(filename='config.txt'):
    seed = read_key_from_config("model_param_seed", filename)
    return int(seed) if seed and seed.strip() else None

def read_model_param_temp_from_config(filename='config.txt'):
    temp = read_key_from_config("model_param_temperature", filename)
    return float(temp) if temp and temp.strip() else None
