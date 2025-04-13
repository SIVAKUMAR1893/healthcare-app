import pika
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import threading

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///appointments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# RabbitMQ setup
RABBITMQ_HOST = 'rabbitmq'

connection = pika.BlockingConnection(pika.ConnectionParameters(
    host='rabbitmq',  # RabbitMQ service name in Docker Compose
    port=5672,        # AMQP port
    credentials=pika.PlainCredentials('guest', 'guest')  # Correct credentials
))

channel = connection.channel()
channel.queue_declare(queue='user_queue')

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    date = db.Column(db.String(50))
    doctor = db.Column(db.String(100))

# Consumer function to process messages from RabbitMQ
def callback(ch, method, properties, body):
    print(f"Received message: {body.decode()}")
    # You can process the message here, for example, create an appointment for the new user
    # This is just a placeholder to simulate an appointment creation:
    new_appointment = Appointment(user_id=1, date='2025-04-15', doctor='Dr. Smith')
    db.session.add(new_appointment)
    db.session.commit()
    print("Created default appointment for the new user")

# Start consuming messages in a separate thread
def consume_messages():
    channel.basic_consume(queue='user_queue', on_message_callback=callback, auto_ack=True)
    print('Waiting for messages from the user service...')
    channel.start_consuming()

# Run consumer in a background thread
threading.Thread(target=consume_messages, daemon=True).start()

@app.route('/appointments', methods=['POST'])
def create_appointment():
    data = request.get_json()
    new_appointment = Appointment(user_id=data['user_id'], date=data['date'], doctor=data['doctor'])
    db.session.add(new_appointment)
    db.session.commit()
    return jsonify({"message": "Appointment created"}), 201

@app.route('/appointments', methods=['GET'])
def get_appointments():
    appointments = Appointment.query.all()
    return jsonify([{'id': a.id, 'user_id': a.user_id, 'date': a.date, 'doctor': a.doctor} for a in appointments])

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=6001)
