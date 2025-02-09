import os

import matplotlib
import matplotlib.pyplot as plt
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

@app.route('/expense_report', methods=['GET','POST'])
def expense_report():
    chart_url = None
    if request.method == 'POST':
    # Retrieve form data
        try:
            income = int(request.form['income'])
            categories = request.form.getlist('categories[]')
            expenses = list(map(int, request.form.getlist('expenses[]')))
            if not categories or not expenses:
                raise ValueError("Incomplete expense data.")

            financial_data = {"income": income, "expenses": dict(zip(categories, expenses))}

    # Generate the pie chart
            chart_filename = generate_expense_pie_chart(financial_data)
            chart_url = url_for('static', filename=chart_filename)
            
        except ValueError:
            return "Please ensure all fields are filled correctly and expenses are numeric."

    # Render the financial form with the chart
    return render_template("expense_report.html", chart_url=chart_url)

matplotlib.use('Agg')  # Ensure compatibility with server environments

def generate_expense_pie_chart(data):
    categories = list(data['expenses'].keys())
    expenses = list(data['expenses'].values())
    total_expenses = sum(expenses)

    savings = max(0, data['income'] - total_expenses)

    # Add savings as a category if there's any
    if savings > 0:
        categories.append("Savings")
        expenses.append(savings)
        
    # Handle case where there are no expenses
    if sum(expenses) == 0:
        return None

    # Choose pastel colors for a chic look
    colors = ["#f8bbd0", "#f48fb1", "#ffec9e", "#7ae7b9", "#5bd2f0",
              "#9be7ff", "#b9acf2", "#c5e1a5", "#e6ee9c", "#ffabab"]

    plt.figure(figsize=(8, 8))
    wedges, texts, autotexts = plt.pie(
        expenses,
        labels=categories,
        colors=colors[:len(categories)],  # Limit to available colors
        autopct='%1.1f%%',
        startangle=140,
        textprops={'fontsize': 12, 'color': '#333'},
        wedgeprops={'edgecolor': '#f3e5f5'}
    )
    
    # Add title with chic color
    plt.title(f"Expense Distribution for Monthly Income: ${data['income']}",
              fontsize=16, color="#e91e63", pad=20)
    
    for autotext in autotexts:
        autotext.set_color("black")

    chart_filename = "expense_chart.png"
    chart_path = f"static/{chart_filename}"
    plt.savefig(chart_path, bbox_inches="tight")
    plt.close()

    return chart_filename

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
