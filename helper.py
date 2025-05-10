import requests
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta


def get_month_map():
    return {'Ocak':'01', 'Şubat':'02', 'Mart':'03', 'Nisan':'04', 'Mayıs':'05', 'Haziran': '06',
            'Temmuz':'07', 'Ağustos':'08', 'Eylül':'09', 'Ekim':'10', 'Kasım':'11', 'Aralık': '12'}

def get_writers_links(base_url, tag_type, search_str, exclude):
    writers_url = base_url + "/yazarlar/"
    r = requests.get(writers_url)
    # Parse HTML
    soup = BeautifulSoup(r.content, 'html.parser')

    if tag_type == "a":
        author_links = soup.find_all('a', class_=search_str)
    elif tag_type == "div":
        author_links = soup.select(search_str)

    # Extract href values
    hrefs = [link.get('href') for link in author_links]

    all_links = []
    # Output the results
    for link in hrefs:
        if all(xcld not in link for xcld in exclude):
            all_links.append(base_url + link)
    return all_links


def save_dataframe_to_db(db_path, table_name, df):
    # Connect to SQLite database (creates file if it doesn't exist)
    conn = sqlite3.connect(db_path)

    df.to_sql(table_name, conn, if_exists='append', index=False)

    # Commit changes and close connection
    conn.commit()
    conn.close()


def get_dataframe_from_db(db_path, table_name):
    conn = sqlite3.connect(db_path)
    query = "SELECT date, author FROM " + table_name
    df_db = pd.read_sql_query(query, conn)

    return df_db


def filter_new_articles(df_today, df_db):
    new_tuples = set(df_today[['date', 'author']].apply(tuple, axis=1).values)
    db_tuples = set(df_db[['date', 'author']].apply(tuple, axis=1).values)
    articles_to_add = new_tuples - db_tuples

    d = {'date':[], 'author':[]}
    for date,author in articles_to_add:
        d['date'].append(date)
        d['author'].append(author)

    filtered_df = df_today[df_today[['date', 'author']].isin(d).all(axis=1)]

    return filtered_df


def update_db_with_articles(db_path, table_name, df):
    if not os.path.exists(db_path):
        save_dataframe_to_db(db_path, table_name, df)
    else:
        df_db = get_dataframe_from_db(db_path, table_name)
        filtered_df = filter_new_articles(df, df_db)
        save_dataframe_to_db(db_path, table_name, filtered_df)


def get_all_op_eds_of_the_given_day(db_path_tables, date_to_match):
    all_dfs = []
    for db_path, table_name in db_path_tables:

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        query = "SELECT date, author, title, content FROM " + table_name + " WHERE DATE(date) = ?"
        dummy = pd.read_sql_query(query, conn, params=(date_to_match,))
        all_dfs.append(dummy)
    return all_dfs


def check_op_ed_number(all_dfs, date_to_match, db_path_tables, trial_count=0):
    df = pd.concat(all_dfs).reset_index(drop=True)

    if df.empty and trial_count < 10:
        trial_count+=1
        date_to_match = (datetime.strptime(date_to_match, "%Y-%m-%d") 
                         - timedelta(days=1)).date().strftime("%Y-%m-%d")
        all_dfs = get_all_op_eds_of_the_given_day(db_path_tables, date_to_match)
        return check_op_ed_number(all_dfs, date_to_match, db_path_tables, trial_count)
    else:
        return df


def sample_from_all_op_eds(df):
    sampled_row = df.sample()
    op_ed = sampled_row['content'].values[0]
    title = sampled_row['title'].values[0]
    
    return op_ed, title


def get_website_html(title, op_ed_text):
    html = f"""
    <div style="max-width: 800px; margin: 0px auto; padding: 0px 20px 20px 20px; font-family: Arial, sans-serif; line-height: 1.6;">

    <div style="margin-top: 0; padding-top: 0; margin-bottom: 30px; text-align: center;">
        <h3 style="margin-top: 0; padding-top: 0;">{title}</h3>
    </div>

    <p style="margin-top: 0; text-align: justify;">
        {op_ed_text}
    </p>

    <hr style="margin-top: 10px;">

    <!-- Refresh Button -->
    <div style="display: flex; justify-content: center; margin: 30px 0;">
        <button onclick="refreshOpEd()" style="
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background-color: white;
            color: black;
            border: 2px solid black;
            border-radius: 12px;
            padding: 0 24px;
            height: 40px;
            min-width: 220px;
            font-size: 16px;
            font-weight: 600;
            font-family: Arial, sans-serif;
            cursor: pointer;
            transition: background-color 0.3s ease;
        "
        onmouseover="this.style.backgroundColor='#f4f4f4'"
        onmouseout="this.style.backgroundColor='white'">
            <span style="line-height: 1;">Köşe Yazısını Yenile</span>
        </button>
    </div>

    <script>
        function refreshOpEd() {{
            fetch("https://www.dijitalname.com/refresh", {{
                method: "POST"
        }})
            .then(response => response.json())
            .then(data => {{
                location.reload();
            }})
            .catch(error => {{
                console.error("Error calling Flask app:", error);
                alert("Failed to contact the server.");
            }});
        }}
    </script>

    <!-- Formidable form -->
    <div style="max-width: 800px; margin: 0 auto;">
        [formidable id=2]
    </div>

    <!-- JS for setting hidden field -->
    <script>
        document.addEventListener("DOMContentLoaded", function () {{
        const hiddenField = document.querySelector('input[name="item_meta[13]"]');
        if (hiddenField) {{
            hiddenField.value = `{op_ed_text}`;
        }}
        }});
    </script>

    </div>
    """
    return html
