from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# In-memory storage for reminders
reminders = []

@app.route('/')
def index():
    return render_template('index.html', reminders=reminders)

@app.route('/add_reminder', methods=['POST'])
def add_reminder():
    data = request.json
    reminders.append({"task": data['task'], "date": data['date']})
    return jsonify({"message": "Reminder added successfully!"})

@app.route('/recommend_date', methods=['POST'])
def recommend_date():
    data = request.json
    task = data['task']

    # Simple logic for date recommendation (e.g., next available day)
    recommended_date = datetime.now() + timedelta(days=1)
    response = {
        "task": task,
        "recommended_date": recommended_date.strftime('%Y-%m-%d')
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
