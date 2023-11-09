import feedparser
from datetime import datetime, timedelta
import tiktoken
import json
import re

# Initialize the tokenizer with the appropriate encoding for gpt-4
enc = tiktoken.encoding_for_model("gpt-4")

MAX_TOKENS = 4000
OVERHEAD_TOKENS = 200  # Tokens reserved for other usages (e.g., title formatting, transitions, etc.)

def count_tokens(text):
    # Count the tokens in a text string using tiktoken's tokenizer.
    return len(enc.encode(text))

def save_to_json(data, filename):
    """Saves the given data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=str)

def save_sources_to_text(news_items, filename):
    """Saves the links from the news items to a text file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("SOURCES\n")
        for item in news_items:
            f.write(item['link'] + "\n")

def clean_data(news_items):
    """Cleans the data of news items by performing various tasks."""
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F700-\U0001F77F"  # alchemical symbols
                               u"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
                               u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                               u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                               u"\U0001FA00-\U0001FA6F"  # Chess Symbols
                               u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                               u"\U00002702-\U000027B0"  # Dingbats
                               "]+", flags=re.UNICODE)
    
    for item in news_items:
        # Remove the published date
        if "published" in item:
            del item["published"]
        
        # Remove emojis from the title
        item["title"] = emoji_pattern.sub(r'', item["title"])

        # Strip the summary of non-text
        item["summary"] = re.sub(r'<[^>]+>', '', item["summary"])  # Remove HTML tags
        item["summary"] = emoji_pattern.sub(r'', item["summary"])  # Remove emojis

    return news_items

def gather_news_from_rss(urls, file_prefix):
    all_news_items = []
    period = datetime.utcnow() - timedelta(minutes=60)

    for url in urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            # First, try getting the date from 'updated_parsed' (corresponding to <pubDate>)
            published_date = entry.updated_parsed if hasattr(entry, 'updated_parsed') else None

            # If not found, then fallback to 'published_parsed'
            if not published_date:
                published_date = entry.published_parsed if hasattr(entry, 'published_parsed') else None

            # Check if the published date exists and is within the last period
            if published_date and datetime(*published_date[:6]) > period:
                all_news_items.append({
                    "title": entry.title,
                    "summary": entry.summary,
                    "published": published_date,
                    "link": entry.link
                })

    # Sorting all news items by published date (most recent first)
    all_news_items.sort(key=lambda x: x["published"], reverse=True)

    # Save the sorted list of all news items to a file
    save_to_json(all_news_items, f'{file_prefix}-news_items-sorted.json') 

    # Clean the data
    all_news_items = clean_data(all_news_items)
    save_to_json(all_news_items, f'{file_prefix}-news_items-sorted-clean.json')

    # Now, we will select news items until we hit the token limit
    news_items = []
    token_count = 0
    for item in all_news_items:
        new_token_count = token_count + count_tokens(item['title'] + "\n" + item['summary'])
                
        # Stop adding news items if we're nearing the token limit
        if new_token_count + OVERHEAD_TOKENS > MAX_TOKENS:
            break

        news_items.append(item)
        token_count = new_token_count

    # Save the sources to a text file
    save_sources_to_text(news_items, f'{file_prefix}-sources.txt')

    # Save the final list of news items to a file
    save_to_json(news_items, f'{file_prefix}-news_items-final.json')

    return news_items
