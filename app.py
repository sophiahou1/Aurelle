from flask import Flask, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "a3f4c8e1b5d9f6a7c2e0b1d8e4f7a6c9"

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
        return redirect(url_for('home'))
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

@app.route('/success')
def success():
    return "Login successful!"

@app.route('/users')
def show_users():
    return "<br>".join(users.keys())  

if __name__ == '__main__':
    app.run(debug=True)