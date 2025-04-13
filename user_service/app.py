import pika
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token
import os
from models import db, User
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Adore1893@db/healthcare'
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

db = SQLAlchemy(app)
jwt = JWTManager(app)



# RabbitMQ setup
RABBITMQ_HOST = 'rabbitmq'

connection = pika.BlockingConnection(pika.ConnectionParameters(
    host='rabbitmq',  # RabbitMQ service name in Docker Compose
    port=5672,        # AMQP port
    credentials=pika.PlainCredentials('guest', 'guest')  # Correct credentials
))

channel = connection.channel()

channel.queue_declare(queue='user_queue')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    new_user = User(username=data['username'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    
    # Send a message to RabbitMQ to notify other services about the new user
    message = f"New user created: {new_user.username}"
    channel.basic_publish(exchange='',
                          routing_key='user_queue',
                          body=message)
    return jsonify({"message": "User created"}), 201

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get(id)
    if user:
        return jsonify({"id": user.id, "username": user.username}), 200
    return jsonify({"message": "User not found"}), 404

@app.route('/register', methods=['POST'])
def register():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        token = create_access_token(identity=user.id)
        return jsonify({'token': token})
    return jsonify({'error': 'Invalid credentials'}), 401



if __name__ == '__main__':
    with app.app_context():  # Ensure the app context is set up
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=6001)
