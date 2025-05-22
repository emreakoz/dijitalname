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

def scrape_sabah(all_links):
    op_ed = []
    for url in all_links:
        r = requests.get(url)
        # Parse HTML
        soup = BeautifulSoup(r.content, 'html.parser')
        
        date_element = soup.find('span', class_='postInfo')
        date_irregular = date_element.get_text(strip=True) if date_element else ''
        month_map = get_month_map()
        date_str = date_irregular.split(',')[0][:2] + '/' + month_map[date_irregular.split(',')[0][3:-5]] \
                   + '/' + date_irregular.split(',')[0][-4:]
        date = datetime.strptime(date_str, "%d/%m/%Y").date()
        
        author_element = soup.find('strong', class_='postTitle')
        author = author_element.get_text(strip=True) if author_element else ''
        
        title_element = soup.find('h1', class_='postCaption')
        title = title_element.get_text(strip=True) if title_element else ''

        content_element = soup.find('div', class_='newsBox')
        content = content_element.get_text(separator=' ', strip=True)
        
        op_ed.append(dict([['date', date]] + [['author', author]] + [['title', title]] + 
                        [['content', content]] + [['url', url]]))
    
    return pd.DataFrame(op_ed)

base_url, tag_type, search_str, exclude = "https://www.sabah.com.tr", "div", "div.col-sm-12.view20 figcaption a[href]", ["getall", "spor", "gunaydin", "pazar"]
all_links = get_writers_links(base_url, tag_type, search_str, exclude)
logging.info(f"Scraped {len(all_links)} number of op eds.")

df_today = scrape_sabah(all_links)
logging.info(f"Scraped info from {len(df_today)} op eds.")

db_path, table_name = os.getenv('SABAH_DB'), os.getenv('SABAH_TABLE_NAME')
update_db_with_articles(db_path, table_name, df_today)
logging.info(f"Updated the sabah db.")
