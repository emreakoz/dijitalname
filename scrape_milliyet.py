import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from helper import get_writers_links, update_db_with_articles, get_month_map
from dotenv import load_dotenv
import os
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

def scrape_milliyet(all_links):
    op_ed = []
    for url in all_links:
        r = requests.get(url)
        # Parse HTML
        soup = BeautifulSoup(r.content, 'html.parser')

        title_element = soup.find('h1', attrs={'data-page': 'news'})
        title = title_element.get_text(strip=True) if title_element else ''

        date_element = soup.find('time', class_='text-faded content-date')
        date_irregular = date_element.get_text(strip=True) if date_element else ''
        month_map = get_month_map()
        date_str = date_irregular[:2] + '/' + month_map[date_irregular[3:-5]] + '/' + date_irregular[-4:]
        date = datetime.strptime(date_str, "%d/%m/%Y").date()
        
        # Find the div by class name
        author_element = soup.find('h2', class_='author-name')
        author = author_element.get_text(strip=True) if author_element else ''

        content_element = soup.find('div', class_='author-content news-content readingTime')
        content = content_element.get_text(separator=' ', strip=True).replace("Haberin Devamı", "").replace("*", "")

        op_ed.append(dict([['date', date]] + [['author', author]] + [['title', title]] + 
                        [['content', content]] + [['url', url]]))

    return pd.DataFrame(op_ed)


base_url, tag_type, search_str, exclude = "https://www.milliyet.com.tr", "a", "card-listing__link", ["skorer"]
all_links = get_writers_links(base_url, tag_type, search_str, exclude)
logging.info(f"Scraped {len(all_links)} number of op eds.")

df_today = scrape_milliyet(all_links)
logging.info(f"Scraped info from {len(df_today)} op eds.")

db_path, table_name = os.getenv('MILLIYET_DB'), os.getenv('MILLIYET_TABLE_NAME')
update_db_with_articles(db_path, table_name, df_today)
logging.info(f"Updated the milliyet db.")

