from flask import Flask, render_template, request, redirect, session
import requests

app = Flask(__name__)
app.secret_key = 'your-secret-key'

API_URL = 'http://api_gateway:9000'  # Gateway container name & port

@app.route('/')
def index():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        response = requests.post(f"{API_URL}/register", json={
            "username": request.form['username'],
            "password": request.form['password']
        })
        if response.status_code == 200:
            return render_template('register.html', message='Registered successfully!')
        else:
            return render_template('register.html', error='Registration failed.')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        payload = {
            'username': request.form['username'],
            'password': request.form['password']
        }
        response = requests.post(f"{API_URL}/login", json=payload)
        if response.status_code == 200:
            session['token'] = response.json()['token']
            return redirect('/dashboard')
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    token = session.get('token')
    if not token:
        return redirect('/login')

    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{API_URL}/api/appointment/appointments", headers=headers)

    if response.status_code == 200:
        data = response.json()
        return render_template('dashboard.html', appointments=data)
    return "Error loading dashboard", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
