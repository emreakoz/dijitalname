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

def scrape_hurriyet(all_links):
    op_ed = []
    for url in all_links:
        r = requests.get(url)
        # Parse HTML
        soup = BeautifulSoup(r.content, 'html.parser')

        title_element = soup.find('h1', class_='author-title news-detail-title')
        title = title_element.get_text(strip=True) if title_element else ''

        author_element = soup.find('span', class_='author-detail-title')
        author = author_element.get_text(strip=True) if author_element else ''
        
        date_element = soup.find('time', class_='author-date')
        date_irregular = date_element.get_text(strip=True) if author_element else ''
        month_map = get_month_map()
        date_str = date_irregular.split(',')[0][-2:] + '/' \
                   + month_map[date_irregular.split(',')[0][:-3]] + '/' \
                   + date_irregular.split(',')[1][1:5]
        date = datetime.strptime(date_str, "%d/%m/%Y").date()

        second_title_element = soup.find('h2', class_='author-spot')
        second_title = second_title_element.get_text(strip=True) if second_title_element else ''

        content_element = soup.find('div', class_='author-content readingTime')
        content = content_element.get_text(separator=' ', strip=True) if content_element else ''
        content = second_title + content.replace("Haberin Devamı", "").replace("*", "")

        op_ed.append(dict([['date', date]] + [['author', author]] + [['title', title]] + 
                        [['content', content]] + [['url', url]]))

    return pd.DataFrame(op_ed)

base_url, tag_type, search_str, exclude = "https://www.hurriyet.com.tr", "a", "author-box", ["sporarena", "tum-yazarlar", "internet-yazilari"]
all_links = get_writers_links(base_url, tag_type, search_str, exclude)
logging.info(f"Scraped {len(all_links)} number of op eds.")

df_today = scrape_hurriyet(all_links)
logging.info(f"Scraped info from {len(df_today)} op eds.")

db_path, table_name = os.getenv('HURRIYET_DB'), os.getenv('HURRIYET_TABLE_NAME')
update_db_with_articles(db_path, table_name, df_today)
logging.info(f"Updated the hurriyet db.")
