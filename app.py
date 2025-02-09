from flask import Flask, redirect, render_template, request, url_for, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash
import openai
from dotenv import load_dotenv
import os


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
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return "Username already taken. Choose another one."
        save_user(username, password)  # Save with hashing
        users[username] = generate_password_hash(password)  # Update in memory
        return redirect(url_for('financial_form'))
    return render_template('signup.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    
        if username in users and check_password_hash(users[username], password): 
            return redirect(url_for('success'))
        return '''
            <p>Invalid credentials. Please try again.</p>
            <a href="/login">Go back to Login</a>
        '''
    return render_template('login.html')

@app.route('/financial_form')
def financial_form():
    return render_template("financial_form.html")

import random

@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    user_message = request.json.get('message')

    if not user_message:
        return jsonify({"response": "I didn't understand that. Can you try again?"})

    # Ensure session variables exist
    if 'chat_history' not in session:
        session['chat_history'] = [
            {"role": "system", "content": "You are a financial assistant. Answer user questions and provide financial advice after gathering information."}
        ]
    if 'question_count' not in session:
        session['question_count'] = 0
    if 'financial_advice_stage' not in session:
        session['financial_advice_stage'] = False
    if 'advice_type' not in session:
        session['advice_type'] = None

    # Save session modifications explicitly
    session.modified = True

    # List of financial-related questions
    random_questions = [
        "What’s your biggest financial goal right now?",
        "How do you usually budget your monthly income?",
        "What’s the smartest financial decision you’ve ever made?",
        "Do you prefer saving for short-term goals or long-term security?",
        "How comfortable are you with investing?",
        "What’s one financial habit you wish to improve?"
    ]

    # Phase 1: Ask 3 random financial questions before moving to advice
    if session['question_count'] < 3 and not session['financial_advice_stage']:
        bot_response = random.choice(random_questions)
        session['question_count'] += 1  # Update the question count
        session.modified = True  # Ensure session updates persist
        return jsonify({"response": bot_response})  # EARLY RETURN (Still in question phase)

    # Phase 2: Ask user what type of financial advice they want
    if not session['financial_advice_stage']:
        session['financial_advice_stage'] = True  # Move to advice stage
        session.modified = True
        return jsonify({"response": "Would you like advice on saving, investing, or general financial guidance?"})  # EARLY RETURN

    # Phase 3: Ensure the user selects an advice category
    if session['advice_type'] is None:
        if user_message.lower() in ["saving", "investing", "general"]:
            session['advice_type'] = user_message.lower()
            session.modified = True
            return jsonify({"response": f"Great! I'll provide detailed advice on {session['advice_type']}. Ask me anything about it!"})  # EARLY RETURN
        else:
            return jsonify({"response": "Please choose one: saving, investing, or general financial advice."})  # EARLY RETURN

    # Phase 4: FINALLY Reach GPT Processing for Financial Advice
    advice_prompt = f"The user is interested in {session['advice_type']} advice. Answer their question in detail."

    # Append user input to chat history
    session['chat_history'].append({"role": "user", "content": user_message})
    session.modified = True

    # Get GPT-generated response
    ai_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=session['chat_history']
    )

    bot_response = ai_response.choices[0].message.content

    # Store AI response in session history
    session['chat_history'].append({"role": "assistant", "content": bot_response})
    session.modified = True

    return jsonify({"response": bot_response})  # FINAL RESPONSE WITH GPT


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