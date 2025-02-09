import os

import openai
from dotenv import load_dotenv
from flask import (Flask, jsonify, redirect, render_template, request, session,
                   url_for)
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = "a3f4c8e1b5d9f6a7c2e0b1d8e4f7a6c9"
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load users from file
def load_users():
    users = {}
    try:
        with open("users.txt", "r") as f:
            for line in f:
                line = line.strip()
                if ":" in line:
                    username, hashed_password = line.split(":",1)
                    users[username] = hashed_password
                else:
                        print(f"Skipping malformed line: {line}")
    except FileNotFoundError:
        print("User file not found. Starting with an empty user list.")
    return users

def save_user(username, password):
    hashed_password = generate_password_hash(password) 
    with open("users.txt", "a") as f:
        f.write(f"{username}:{hashed_password}\n")

users = load_users()

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return "Username already taken. Choose another one."
        save_user(username, password)  # Save with hashing
        users[username] = generate_password_hash(password)  # Update in memory
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    
        if username in users and check_password_hash(users[username], password): 
            return redirect(url_for('financial_form'))
        return '''
            <p>Invalid credentials. Please try again.</p>
            <a href="/login">Go back to Login</a>
        '''
    return render_template('login.html')

@app.route('/financial_form')
def financial_form():
    return render_template("financial_form.html")

@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    user_message = request.json.get('message')

    if not user_message:
        return jsonify({"response": "I didn't understand that. Can you try again?"})

    # Maintain chat history in session
    if 'chat_history' not in session:
        session['chat_history'] = [
            {"role": "system", "content": "You are a friendly financial assistant gathering financial details."},
            {"role": "assistant", "content": "Hi! Let's talk about your finances. What's your monthly income?"}
        ]

    # Add user message to chat history
    session['chat_history'].append({"role": "user", "content": user_message})

    # Get AI response
    ai_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=session['chat_history']
    )

    bot_response = ai_response.choices[0].message.content

    # Add AI response to chat history
    session['chat_history'].append({"role": "assistant", "content": bot_response})

    return jsonify({"response": bot_response})

def save_financial_data(username, financial_data):
    with open("users.txt", "r") as f:
        lines = f.readlines()

    with open("users.txt", "w") as f:
        for line in lines:
            if line.startswith(username + ":"):
                f.write(f"{line.strip()}:{':'.join(financial_data)}\n")
            else:
                f.write(line)

@app.route('/submit_financial_data', methods=['POST'])
def submit_financial_data():
    username = session.get('username', "unknown_user")
    financial_data = request.json.get("financial_data", [])
    save_financial_data(username, financial_data)
    return jsonify({"message": "Thank you! Your financial data has been saved."})


@app.route('/success')
def success():
    return "Login successful!"

@app.route('/users')
def show_users():
    return "<br>".join(users.keys())  

if __name__ == '__main__':
    app.run(debug=True)
