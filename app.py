from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = "88c5de10c652fca821ced0515c1df06b"

def load_users():
    users = {}
    try:
        with open("users.txt", "r") as f:
            for line in f:
                username, password = line.strip().split(":")
                users[username] = password
    except FileNotFoundError:
        pass
    return users
def save_user(username, password):
    with open("users.txt", "a") as f:
        f.write(f"{username}:{password}\n")


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
        users[username] = password
        save_user(username, password)  # Save to file
        return redirect(url_for('home'))
    return render_template('signup.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in users and users[username] == password:
        return redirect(url_for('success'))
    return "Invalid credentials. Please try again."

@app.route('/success')
def success():
    return "Login successful!"

@app.route('/users')
def show_users():
    return "<br>".join(users.keys()) 

if __name__ == '__main__':
    app.run(debug=True)
