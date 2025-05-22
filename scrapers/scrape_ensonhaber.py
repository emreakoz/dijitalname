import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from helper import get_writers_links, update_db_with_articles
from dotenv import load_dotenv
import os
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

def scrape_ensonhaber(all_links):
    op_ed = []
    for url in all_links:
        r = requests.get(url)
        # Parse HTML
        soup = BeautifulSoup(r.content, 'html.parser')

        title_element = soup.find('div', class_='article-title')
        title = title_element.get_text(strip=True) if title_element else ''

        date_element = soup.find('time')
        date_str = date_element.get_text(strip=True) if date_element else ''
        date = datetime.strptime(date_str[:10], "%d.%m.%Y").date()

        # Find the div by class name
        author_element = soup.find('div', class_='name')
        author = author_element.get_text(strip=True) if author_element else ''

        content_element = soup.find('div', class_='article-content')
        content = content_element.get_text(separator=' ', strip=True)

        op_ed.append(dict([['date', date]] + [['author', author]] + [['title', title]]
                        + [['content', content]] + [['link', url]]))

    return pd.DataFrame(op_ed)


base_url, tag_type, search_str, exclude = "https://www.ensonhaber.com", "a", "article", []
all_links = get_writers_links(base_url, tag_type, search_str, exclude)
logging.info(f"Scraped {len(all_links)} number of op eds.")

df_today = scrape_ensonhaber(all_links)
logging.info(f"Scraped info from {len(df_today)} op eds.")

db_path, table_name = os.getenv('ENSONHABER_DB'), os.getenv('ENSONHABER_TABLE_NAME')
update_db_with_articles(db_path, table_name, df_today)
logging.info(f"Updated the ensonhaber db.")
