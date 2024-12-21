import sqlite3
from datetime import datetime, timedelta

DATABASE = 'tasks.db'

# Mock tasks to insert
mock_tasks = [
    ("testtest", "Submit project report", "2024-12-01", "15:00"),
    ("testtest", "Team meeting", "2024-12-02", "10:00"),
    ("testtest", "Doctor appointment", "2024-12-03", "09:30"),
    ("testtest", "Grocery shopping", "2024-12-04", "17:00"),
    ("testtest", "Workout session", "2024-12-05", "18:00")
]

# Function to insert tasks into the database
def add_mock_tasks():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.executemany('''
        INSERT INTO tasks (username, task, date, time) VALUES (?, ?, ?, ?)
    ''', mock_tasks)

    conn.commit()
    conn.close()
    print("Mock tasks added successfully.")

add_mock_tasks()
