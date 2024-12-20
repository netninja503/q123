from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from datetime import datetime
import os
import json
import random
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client.quiz_app
users_collection = db.users
results_collection = db.results

# Load Questions
def load_questions():
    try:
        if not os.path.exists('questions.json'):
            print("Error: questions.json file not found!")
            return []

        with open('questions.json', 'r') as file:
            data = json.load(file)
            questions = data.get('questions', [])
            if not questions:
                print("Error: No questions found in questions.json")
                return []
            return random.sample(questions, min(20, len(questions)))

    except Exception as e:
        print(f"Error loading questions: {e}")
        return []

# Route: Login

@app.route('/', methods=['GET', 'POST'])
def login():
    """User login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Accept any username and password for login
        if not username or not password:
            return "Username and password cannot be empty."

        # Save or update the user in the database
        users_collection.update_one(
            {"username": username},
            {"$set": {"password": password}},
            upsert=True
        )

        session['username'] = username
        session['questions'] = load_questions()
        if not session['questions']:
            return "Error: Could not load questions. Please try again."

        return redirect(url_for('quiz'))

    return render_template('login.html')


# Route: Quiz
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    """Display quiz questions."""
    if 'username' not in session:
        return redirect(url_for('login'))

    questions = session.get('questions', [])
    if not questions:
        return "Error: Questions not loaded."

    if request.method == 'POST':
        score = 0
        skipped = 0
        wrong = 0

        for question in questions:
            question_id = str(question['id'])
            user_answer = request.form.get(question_id)

            if not user_answer:
                skipped += 1
            elif user_answer == question['answer']:
                score += 1
            else:
                wrong += 1

        password = users_collection.find_one({"username": session['username']})['password']

        return render_template(
            'result.html',
            score=score,
            skipped=skipped,
            wrong=wrong,
            total=len(questions),
            username=session['username'],
            password=password
        )

    return render_template('quiz.html', questions=questions)

# Route: Logout
@app.route('/logout')
def logout():
    """Clear session and logout."""
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
