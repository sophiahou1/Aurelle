from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

users = {}

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

if __name__ == '__main__':
    app.run(debug=True)
