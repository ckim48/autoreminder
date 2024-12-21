from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import json
from pywebpush import webpush, WebPushException
from datetime import datetime, timedelta
import threading
import time
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI
from datetime import datetime
import re
app = Flask(__name__)
app.secret_key = 'sd'  # Replace with a secure secret key

# Replace with your VAPID keys
VAPID_PUBLIC_KEY = "BCon0VtA1b72sjtj45d8s-1mmdeg_NSmb8MpGN7vfAMbTWa1fWGWePbn7obBFGDZidVUGz4jWbIvmEwJ9VHMbJ0"
VAPID_PRIVATE_KEY = "LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JR0hBZ0VBTUJNR0J5cUdTTTQ5QWdFR0NDcUdTTTQ5QXdFSEJHMHdhd0lCQVFRZ2NzOFdTYVg4d1JlUmc1cTQKZlhBd21XSXlGZHJXaG9vNWwzN21yblpSRUNxaFJBTkNBQVFxSjlGYlFOVys5ckk3WStPWGZMUHRacG5Yb1B6VQpwbS9ES1JqZTczd0RHMDFtdFgxaGxuajI1KzZHd1JSZzJZblZWQnMrSTFteUw1aE1DZlZSekd5ZAotLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tCg"

DATABASE = 'tasks.db'


from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
from datetime import datetime
from datetime import datetime, timedelta
import re

def is_valid_future_date(date_str):
    """Validate the date string format as '%Y-%m-%d' and ensure it's in the future."""
    try:
        suggested_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        return suggested_date >= today
    except ValueError:
        return False
@app.route('/chat', methods=['POST'])
def chat():
    if not request.json or 'message' not in request.json:
        return jsonify({"error": "Invalid request"}), 400

    user_message = request.json['message']
    username = session.get('username')

    # Check for user confirmation to add a pending task
    if user_message.lower() == "yes" and session.get('pending_task'):
        task = session.pop('pending_task')
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO tasks (username, task, date, time) VALUES (?, ?, ?, ?)',
            (username, task['task'], task['date'], task['time'])
        )
        conn.commit()
        conn.close()
        return jsonify({
            "reply": "Task has been added successfully!",
            "new_task_added": True,  # Notify the frontend
            "task": {
                "title": task['task'],
                "start": f"{task['date']}T{task['time']}"
            }
        })

    # Fetch user's past tasks for context
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT task, date, time FROM tasks WHERE username = ?', (username,))
    past_tasks = cursor.fetchall()
    conn.close()

    today = datetime.now().date()
    filtered_past_tasks = [
        task for task in past_tasks if datetime.strptime(task[1], "%Y-%m-%d").date() >= today
    ]

    if filtered_past_tasks:
        past_tasks_summary = "\n".join(
            [f"{task[0]} on {task[1]} at {task[2]}" for task in filtered_past_tasks]
        )
        recommendation_prompt = (
            f"Based on these tasks, recommend a similar task or suggest something new "
            f"that aligns with the user's preferences or routine. Only suggest tasks with future dates within the next 30 days."
        )
    else:
        past_tasks_summary = "No relevant future tasks found."
        recommendation_prompt = "The user has no future tasks. Suggest a new task with a date within the next 30 days to help them get started."

    # Construct the OpenAI GPT prompt
    prompt = (
        f"You are a task management assistant. Here are some relevant tasks for the user:\n"
        f"{past_tasks_summary}\n\n"
        f"The user asked: '{user_message}'.\n\n"
        f"{recommendation_prompt}\n"
        f"If you suggest a task, include the following format: 'Task: [task], Date: [YYYY-MM-DD], Time: [HH:MM]'."
    )

    # Call OpenAI GPT API
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI task management assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    ai_message = response.choices[0].message.content.strip()

    # Check if the response contains a task suggestion
    if "Task:" in ai_message:
        try:
            task_details = re.split(r",\s*", ai_message)
            task_name = task_details[0].replace("Task: ", "").strip()
            task_date = task_details[1].replace("Date: ", "").strip()
            task_time = task_details[2].replace("Time: ", "").strip()

            # Validate the suggested date format and ensure it's reasonable
            if not is_valid_future_date(task_date):
                # Automatically correct the date to a reasonable future date
                task_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")

            session['pending_task'] = {
                "task": task_name,
                "date": task_date,
                "time": task_time
            }
            ai_message = f"Task: {task_name}, Date: {task_date}, Time: {task_time}. Do you want to add this task? (Reply with 'yes' to confirm)"
        except (IndexError, ValueError):
            ai_message = "The task suggestion could not be parsed. Please ask again."

    return jsonify({"reply": ai_message, "new_task_added": False})

@app.route('/add-task', methods=['POST'])
def add_task():
    if not request.json:
        return jsonify({"success": False, "error": "Invalid request"}), 400

    task_name = request.json.get('task')
    task_date = request.json.get('date')
    task_time = request.json.get('time')
    username = session.get('username')

    if not all([task_name, task_date, task_time, username]):
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO tasks (username, task, date, time) VALUES (?, ?, ?, ?)',
            (username, task_name, task_date, task_time)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



def init_db():
    """Initialize SQLite database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
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
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            # Hash the password before storing it
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists", 400
        finally:
            conn.close()

        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):  # Validate hashed password
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return "Invalid username or password", 401
    return render_template('login.html')



@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/subscribe', methods=['POST'])
def subscribe():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

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
@app.route('/tasks', methods=['GET'])
def get_tasks():
    username = session.get('username')
    if not username:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT task, date, time FROM tasks WHERE username = ?', (username,))
        tasks = cursor.fetchall()
        conn.close()

        # Format tasks for FullCalendar
        events = [
            {
                "title": task[0],
                "start": f"{task[1]}T{task[2]}",
            }
            for task in tasks
        ]

        # Debugging: Print the events being sent
        print(events)

        return jsonify({"success": True, "events": events})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    init_db()
    threading.Thread(target=check_and_send_reminders, daemon=True).start()
    app.run(debug=True)
