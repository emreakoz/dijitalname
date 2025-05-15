from flask import Flask, jsonify, request
import subprocess

app = Flask(__name__)

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
    app.run(host="127.0.0.1", port=5000)


    