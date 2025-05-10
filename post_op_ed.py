import requests
from base64 import b64encode
from helper import get_all_op_eds_of_the_given_day, check_op_ed_number, sample_from_all_op_eds, get_website_html
from datetime import datetime
from dotenv import load_dotenv
import os

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

db_path_tables = [
    (os.getenv('SABAH_DB'), 'sabah'),
    (os.getenv('HURRIYET_DB'), 'hurriyet'),
    (os.getenv('MILLIYET_DB'), 'milliyet'),
    (os.getenv('ENSONHABER_DB'), 'ensonhaber')
]

date_to_match = datetime.now().date().strftime("%Y-%m-%d")
logging.info(f"The date: {date_to_match} is going to be checked in the db.")

all_dfs = get_all_op_eds_of_the_given_day(db_path_tables, date_to_match)
df = check_op_ed_number(all_dfs, date_to_match, db_path_tables)
logging.info(f"Total of {len(df)} op eds are retreived.")

op_ed_text, title = sample_from_all_op_eds(df)
logging.info(f"Sampled op ed title is {title}")

# === CONFIGURATION ===
wp_user = os.getenv("WP_USER")
wp_app_password = os.getenv("WP_APP_PASSWORD")
page_id = os.getenv("PAGE_ID")
wp_url = f"{os.getenv('WP_URL')}/{page_id}?context=edit"

# Encode credentials
credentials = f"{wp_user}:{wp_app_password}"
token = b64encode(credentials.encode())
headers = {
    'Authorization': f'Basic {token.decode("utf-8")}',
    'Content-Type': 'application/json'
}

html = get_website_html(title, op_ed_text)

# === POST CONTENT ===
post_data = {
    'content': html,
    'status': 'publish'
}

# === SEND REQUEST ===
response = requests.post(wp_url, headers=headers, json=post_data)

# === CHECK RESULT ===
if response.status_code in  (200, 201):
    print('✅ Successfully posted to WordPress!')
else:
    print(f'❌ Failed to post! Status Code: {response.status_code}')
