import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)

def extract_rss_urls_from_opml(opml_file):
    logger.info(f"Begin extraction from {opml_file}")
    tree = ET.parse(opml_file)
    root = tree.getroot()

    # Extract RSS URLs
    rss_urls = []
    for outline in root.findall(".//outline"):
        url = outline.get("xmlUrl")
        if url:
            rss_urls.append(url)

    logger.info(f"Extraction complete")
    return rss_urls

