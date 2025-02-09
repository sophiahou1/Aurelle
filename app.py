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
            # Redirect to error page if username is taken
            return redirect(url_for('signup_error'))

        # Save the user securely
        save_user(username, password)  # Assume this function saves the user
        users[username] = generate_password_hash(password)  # Store hashed password

        return redirect(url_for('login'))  # Redirect to login page if successful

    return render_template('signup.html')

@app.route('/signup_error')
def signup_error():
    return render_template('sign_failed.html')  # Show error page

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    
        if username in users and check_password_hash(users[username], password): 
            return redirect(url_for('financial_form'))
        else:
            return redirect(url_for('login_failed'))  # Redirect to the login failed page
    return render_template('login.html')  # Render the login page

@app.route('/login_failed')
def login_failed():
    return render_template('login_failed.html')  # Render the login failed page

@app.route('/financial_form')
def financial_form():
    return render_template("financial_form.html")

@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    user_message = request.json.get('message').strip().lower()  # Normalize input
    username = session.get('username', 'Guest')  # Retrieve username
    current_goal = session.get('financial_goal', None)  # Get current goal
    previous_goals = session.get('previous_goals', [])  # Retrieve previous goals

    # Define financial goals and first question for each
    goal_questions = {
        "saving money": "How much do you currently save per month, and what is your savings target?",
        "increasing income": "Are you looking for a raise, a side hustle, or a new job?",
        "investing": "Are you a beginner, or do you have experience with investing?",
        "managing debt": "What type of debt do you currently have (credit card, student loan, mortgage)?",
        "planning for a major purchase": "What are you saving up for, and what’s your expected timeline?",
        "retirement planning": "At what age do you want to retire, and do you have a retirement account?",
        "tax optimization": "Are you looking for deductions, credits, or tax-efficient investments?",
        "building credit score": "Do you know your current credit score?",
        "preparing for unexpected expenses": "Do you currently have an emergency fund? If so, how many months of expenses do you have saved?",
        "financial education": "What financial topics are you most interested in learning about?",
        "expense report": "Would you like a summary of your expenses or budgeting suggestions?"
    }

    # Define formatted financial goals list
    financial_goals_list = [
        "💰 Saving Money",
        "💼 Increasing Income",
        "📈 Investing",
        "💳 Managing Debt",
        "🏡 Planning for a Major Purchase",
        "🏦 Retirement Planning",
        "📊 Tax Optimization",
        "✅ Building Credit Score",
        "🚑 Preparing for Unexpected Expenses",
        "📖 Financial Education",
        "📊 Expense Report"
    ]

    # If user asks for the financial goals list
    if "what are the financial goals" in user_message or "what options" in user_message:
        return jsonify({"response": "Here are the available financial goals:<br><br>" +
                         "<br>".join([f"🔹 {goal}" for goal in financial_goals_list]) +
                         "<br><br>👉 **Type 'Change my goal' to switch to a different goal.**"})

    # If user wants to change their goal
    if "change my goal" in user_message or "i want to change my goal" in user_message:
        return jsonify({"response": "🔄 **You can change your financial goal anytime!**<br><br>" +
                         "Here are the available financial goals:<br><br>" +
                         "<br>".join([f"🔹 {goal}" for goal in financial_goals_list]) +
                         "<br><br>👉 **Please type the goal you want to switch to.**"})

    # Detect if user selects a financial goal
    selected_goal = next((goal for goal in goal_questions.keys() if goal in user_message), None)

    if selected_goal:
        if current_goal and current_goal != selected_goal:
            previous_goals.append(current_goal)  # Save current goal to history

        session['financial_goal'] = selected_goal  # Store new goal
        session['previous_goals'] = previous_goals  # Update previous goals list

        session['chat_history'] = [
            {"role": "system", "content": f"You are a financial assistant specializing in {selected_goal}."},
            {"role": "assistant", "content": f"✅ You've switched to **{selected_goal.title()}**! Let's continue."}
        ]

        # Ask the first question for the selected goal
        first_question = goal_questions[selected_goal]
        session['chat_history'].append({"role": "assistant", "content": first_question})

        return jsonify({"response": f"✅ You've switched to **{selected_goal.title()}**!<br><br>{first_question}"})

    # Allow user to view previous goal
    if "previous goal" in user_message or "what was my last goal" in user_message:
        if previous_goals:
            last_goal = previous_goals.pop()  # Remove last goal from history
            session['financial_goal'] = last_goal  # Switch back to last goal
            session['previous_goals'] = previous_goals  # Update session

            session['chat_history'].append(
                {"role": "assistant", "content": f"🔄 You've switched back to your previous goal: **{last_goal.title()}**!"}
            )

            return jsonify({"response": f"🔄 You've switched back to your previous goal: **{last_goal.title()}**!<br><br>{goal_questions[last_goal]}"})

        return jsonify({"response": "❌ No previous goal found. You are currently working on **" + current_goal.title() + "**."})

    # Ensure chat history exists (prevents chatbot from asking for goal again)
    if 'chat_history' not in session:
        return jsonify({"response": "Please select a financial goal first.<br><br>👉 Type: **'What are the financial goals?'** to see available options."})

    # Add user message to chat history
    session['chat_history'].append({"role": "user", "content": user_message})

    # Get AI response
    ai_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=session['chat_history']
    )

    bot_response = ai_response.choices[0].message.content

    # 🔥 **Automatically format AI-generated "tips" lists for better readability**
    if "tips" in bot_response.lower():
        bot_response = bot_response.replace("1.", "<br><br>1️⃣ ").replace("2.", "<br><br>2️⃣ ") \
                                   .replace("3.", "<br><br>3️⃣ ").replace("4.", "<br><br>4️⃣ ") \
                                   .replace("5.", "<br><br>5️⃣ ").replace("6.", "<br><br>6️⃣ ") \
                                   .replace("7.", "<br><br>7️⃣ ").replace("8.", "<br><br>8️⃣ ") \
                                   .replace("9.", "<br><br>9️⃣ ").replace("10.", "<br><br>🔟 ") \
                                   + "<br><br>😊 Let me know if you need more details on any of these!"

    # Debugging: Print AI response
    print("AI Response:", bot_response)

    # Add AI response to chat history
    session['chat_history'].append({"role": "assistant", "content": bot_response})

    return jsonify({"response": bot_response})

@app.route('/set_goal', methods=['POST'])
def set_goal():
    selected_goal = request.json.get('goal')
    if selected_goal:
        session['financial_goal'] = selected_goal  # Store selected goal
        return jsonify({"message": f"Goal set to {selected_goal}!"})
    return jsonify({"error": "No goal selected."})


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
