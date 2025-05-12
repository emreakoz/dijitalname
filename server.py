from flask import Flask, request, jsonify
import sqlite3
from dotenv import load_dotenv
import os
import subprocess
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
load_dotenv()
users_db_path = os.getenv("USERS_DB")
logging.info(f"Received db path: {users_db_path}")

# === /register endpoint ===
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    logging.info(f"Received registration data {data}.")

    if not data:
        return jsonify({'error': 'No JSON received'}), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    logging.info(f"Received username: {data}, email: {email}, password: {password}.")

    if not username or not email or not password:
        return jsonify({'error': 'Missing fields'}), 400

    logging.info(f"will write to db path: {users_db_path}")
    try:
        conn = sqlite3.connect(users_db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                email TEXT UNIQUE,
                password TEXT
            )
        """)
        c.execute("INSERT OR IGNORE INTO users (username, email, password) VALUES (?, ?, ?)",
                  (username, email, password))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'user': email}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# === /refresh endpoint ===
@app.route("/refresh", methods=["POST"])
def refresh_content():
    try:
        result = subprocess.run(["python3", "post_news.py"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        app.logger.info(f"Script output: {result.stdout}")
        return jsonify({"status": "success", "message": "Content refreshed"})
    except subprocess.CalledProcessError as e:
        app.logger.error(f"Script failed: {e.stderr}")
        return jsonify({"status": "error", "message": str(e), "stderr": e.stderr}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
