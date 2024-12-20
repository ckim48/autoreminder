from flask import Flask, render_template, request, jsonify
import sqlite3
import json
from pywebpush import webpush, WebPushException
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

# Replace with your VAPID keys
VAPID_PUBLIC_KEY = "BCon0VtA1b72sjtj45d8s-1mmdeg_NSmb8MpGN7vfAMbTWa1fWGWePbn7obBFGDZidVUGz4jWbIvmEwJ9VHMbJ0"
VAPID_PRIVATE_KEY = "LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JR0hBZ0VBTUJNR0J5cUdTTTQ5QWdFR0NDcUdTTTQ5QXdFSEJHMHdhd0lCQVFRZ2NzOFdTYVg4d1JlUmc1cTQKZlhBd21XSXlGZHJXaG9vNWwzN21yblpSRUNxaFJBTkNBQVFxSjlGYlFOVys5ckk3WStPWGZMUHRacG5Yb1B6VQpwbS9ES1JqZTczd0RHMDFtdFgxaGxuajI1KzZHd1JSZzJZblZWQnMrSTFteUw1aE1DZlZSekd5ZAotLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tCg"

DATABASE = 'tasks.db'


def init_db():
    """Initialize SQLite database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            task TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT NOT NULL UNIQUE,
            p256dh TEXT NOT NULL,
            auth TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/subscribe', methods=['POST'])
def subscribe():
    subscription = request.json
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO subscriptions (endpoint, p256dh, auth) VALUES (?, ?, ?)',
        (subscription['endpoint'], subscription['keys']['p256dh'], subscription['keys']['auth'])
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


def send_notification(subscription_info, title, body):
    """Send a push notification."""
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": "mailto:your-email@example.com"}
        )
    except WebPushException as ex:
        print(f"Failed to send notification: {ex}")


def check_and_send_reminders():
    """Check tasks and send reminders."""
    while True:
        now = datetime.now()
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, task, date, time FROM tasks')
        tasks = cursor.fetchall()

        for task in tasks:
            task_time = datetime.strptime(f"{task[2]} {task[3]}", "%Y-%m-%d %H:%M")
            if now + timedelta(minutes=10) >= task_time > now:
                cursor.execute('SELECT endpoint, p256dh, auth FROM subscriptions')
                subscriptions = cursor.fetchall()

                for sub in subscriptions:
                    subscription_info = {
                        "endpoint": sub[0],
                        "keys": {"p256dh": sub[1], "auth": sub[2]}
                    }
                    send_notification(subscription_info, "Task Reminder", f"Upcoming Task: {task[1]}")

        conn.close()
        time.sleep(60)


if __name__ == '__main__':
    init_db()
    threading.Thread(target=check_and_send_reminders, daemon=True).start()
    app.run(debug=True)
