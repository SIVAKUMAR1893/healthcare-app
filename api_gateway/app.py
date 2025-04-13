from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['JWT_SECRET_KEY'] = 'super-secret-key'
jwt = JWTManager(app)

# API Gateway Routes
@app.route('/register', methods=['POST'])
def register():
    if request.is_json:
        data = request.get_json()  # Parse JSON content from the frontend
    else:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    # Forward the request to the User Service
    response = requests.post('http://user_service:6001/register', json=data)

    # Return the response from the User Service to the frontend
    return jsonify(response.json()), response.status_code

@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        data = request.get_json()  # Parse JSON content from the frontend
    else:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    # Forward the login request to the User Service
    response = requests.post('http://user_service:6001/login', json=data)

    # Return the response (JWT Token or error message)
    return jsonify(response.json()), response.status_code

@app.route('/appointments', methods=['GET', 'POST'])
@jwt_required()
def handle_appointments():
    # Check if the content is JSON for POST requests
    if request.is_json:
        data = request.get_json()  # Parse the request data (for POST)
    else:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    # Extract JWT token for validation
    token = request.headers.get('Authorization')

    # Forward the request to Appointment Service
    if request.method == 'POST':
        response = requests.post(
            'http://appointment_service:6000/appointments',
            json=data,
            headers={'Authorization': token}  # Forward JWT token for authorization
        )
    else:
        response = requests.get(
            'http://appointment_service:6000/appointments',
            headers={'Authorization': token}
        )

    # Return the response from the Appointment Service
    return jsonify(response.json()), response.status_code

@app.route('/gateway/<path:path>', methods=['GET', 'POST'])
@jwt_required(optional=True)  # Optional JWT for some routes
def gateway(path):
    token = request.headers.get('Authorization')
    headers = {'Authorization': token} if token else {}

    # Handle requests to User Service and Appointment Service
    if path.startswith("appointments"):
        url = f"http://appointment_service:6000/{path}"
    else:
        url = f"http://user_service:6001/{path}"

    # Allow unauthenticated access for login/register
    if path in ['login', 'register']:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        response = requests.post(url, json=data)
        return (response.content, response.status_code, response.headers.items())

    # Token is required for other requests
    if not token:
        return jsonify({'error': 'Missing token'}), 401

    if request.method == 'POST':
        response = requests.post(url, json=request.get_json(), headers=headers)
    else:
        response = requests.get(url, headers=headers)

    return (response.content, response.status_code, response.headers.items())


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'API Gateway is running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
