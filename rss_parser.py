import feedparser
import pytz 
from datetime import datetime, timedelta
import tiktoken
import json
import re
import html
import logging
from bs4 import BeautifulSoup
import time
import requests
from requests.exceptions import HTTPError


logger = logging.getLogger(__name__)

# Initialize the tokenizer with the appropriate encoding for gpt-4
enc = tiktoken.encoding_for_model("gpt-4")

#MAX_TOKENS = 8000
MAX_TOKENS = 12000
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

def get_full_article(link):
    """Fetches and returns the full article content from the given link."""
    retries = 0
    max_retries=2
    wait_secs=15 
    while retries < max_retries:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            response = requests.get(link, headers=headers)
            response.raise_for_status()  # Ensure we notice bad responses
            soup = BeautifulSoup(response.content, 'html.parser')
            # This assumes that the main content of the article is within a <p> tag
            # You might need to adjust this based on the structure of your target webpages
            # More Generic Implementation:
            article_text = ' '.join(p.get_text() for p in soup.find_all('p'))
            if not article_text.strip():
                # If article_text is empty after stripping whitespace
                logger.error(f"Failed to parse the article content: {link}")
                return ''  # Return empty article

            logger.debug(f"Article content fetched: {link}")
            return article_text
            # More Specific Implementation:
            # article_body = soup.find('article') or soup.find('div', class_='post-content')
            # if article_body:
            #     article_text = article_body.get_text(strip=True, separator=' ')
            #     logger.debug(f"Article content fetched: {link}")
            # else:
            #     logger.error(f"Failed to parse the article content: {link}")
            #     article_text = '' # Return empty article
            # return article_text

        except HTTPError as e:
            if e.response.status_code == 429:
                # If it's a rate limit error, wait and then retry
                wait_time = int(e.response.headers.get('Retry-After', wait_secs))
                logger.warning(f"429 Client Error: Too Many Requests. Retrying after {wait_time} seconds.")
                time.sleep(wait_time)
                retries += 1
                continue
            else:
                logger.error(f"HTTP error occurred: {e}")
                return ""        
        except Exception as e:
            logger.error(f"Other error occurred: {e}")
            return ""

    logger.error("Max retries reached. Returning empty article.")
    return ""

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

        # Decode HTML entities in the title
        item["title"] = html.unescape(item["title"])

        # Remove newline and carriage return characters
        item["title"] = item["title"].replace('\n', ' ').replace('\r', ' ')

        # Strip the summary of non-text
        item["summary"] = re.sub(r'<[^>]+>', '', item["summary"])  # Remove HTML tags
        item["summary"] = emoji_pattern.sub(r'', item["summary"])  # Remove emojis

        # Decode HTML entities in the summary
        item["summary"] = html.unescape(item["summary"])

        # Remove newline and carriage return characters
        item["summary"] = item["summary"].replace('\n', ' ').replace('\r', ' ')

    return news_items

def gather_news_from_rss(urls, file_prefix, minutes):
    logger.info(f"Begin gathering news from RSS feeds for the last {minutes} minutes")
    all_news_items = []
    #period = datetime.utcnow() - timedelta(minutes)
    period = datetime.utcnow().replace(tzinfo=pytz.utc) - timedelta(minutes=minutes)
    logger.debug(f"Period: {period}")

    for url in urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            # Skip entries with titles starting with "WATCH:"
            if entry.title.startswith("WATCH:"):
                continue

            published_date = None
            if hasattr(entry, 'updated_parsed'):
                published_date = datetime(*entry.updated_parsed[:6]).replace(tzinfo=pytz.utc)
            elif hasattr(entry, 'published_parsed'):
                published_date = datetime(*entry.published_parsed[:6]).replace(tzinfo=pytz.utc)

            logger.debug(f"Published Date: {published_date}")

            if published_date and published_date > period:            
                full_article = get_full_article(entry.link)  # Fetch the full article

                # Skip the entry if full_article is blank
                # if not full_article.strip():
                #     continue
                # all_news_items.append({
                #     "title": entry.title,
                #     "summary": entry.summary,
                #     "article": full_article,
                #     "published": published_date,
                #     "link": entry.link
                # })

                # If the article comes back blank, use the title and summary only
                article_content = full_article if full_article.strip() else f"{entry.title}\n{entry.summary}"

                all_news_items.append({
                    "title": entry.title,
                    "summary": entry.summary,
                    "article": article_content,
                    "published": published_date,
                    "link": entry.link
                })
    logger.info(f"URLs Parsed")

    # Sorting all news items by published date (most recent first)
    all_news_items.sort(key=lambda x: x["published"], reverse=True)
    save_to_json(all_news_items, f'{file_prefix}-news_items-sorted.json') 
    logger.info(f"News sorted in reverse order and saved to file")

    # Clean the data
    all_news_items = clean_data(all_news_items)
    save_to_json(all_news_items, f'{file_prefix}-news_items-sorted-clean.json')
    logger.info(f"News items cleaned from non-readable characters and saved to file.")

    # Now, we will select news items until we hit the token limit
    news_items = []
    token_count = 0
    for item in all_news_items:
        item_token_count = count_tokens(item['article'])

        # Check if adding this item would exceed the token limit
        if token_count + item_token_count + OVERHEAD_TOKENS <= MAX_TOKENS:
            news_items.append(item)
            token_count += item_token_count
        # If the item would exceed the limit, skip it and check the next item
        else:
            continue

        # #new_token_count = token_count + count_tokens(item['title'] + "\n" + item['summary'])
        # new_token_count = token_count + count_tokens(item['article'])
                
        # # Stop adding news items if we're nearing the token limit
        # if new_token_count + OVERHEAD_TOKENS > MAX_TOKENS:
        #     break

        # news_items.append(item)
        # token_count = new_token_count
    logging.info(f"Max token count reached: {token_count}")

    # Save the sources to a text file
    save_sources_to_text(news_items, f'{file_prefix}-sources.txt')
    logging.info(f"Sources saved to file")

    # Save the final list of news items to a file
    save_to_json(news_items, f'{file_prefix}-news_items-final.json')
    logging.info(f"Final set of news items saved to file")

    logger.info(f"Complete gathering news from RSS feeds")
    return news_items
