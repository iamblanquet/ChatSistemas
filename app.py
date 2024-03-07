import random
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, send, emit
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = "secret123"
socketio = SocketIO(app, cors_allowed_origins="*")

access_code_value = str(random.randint(100000, 999999))
print("Generated access code:", access_code_value)

connected_users = set()

@socketio.on('connect')
def handle_connect():
    username = session.get('username', 'Guest')
    connected_users.add(username)
    emit('update_user_list', list(connected_users), broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username', 'Guest')
    if username in connected_users:
        connected_users.remove(username)
        emit('update_user_list', list(connected_users), broadcast=True)

@socketio.on('message')
def handle_message(message):
    print("Received message:", message)
    if message != "User connected!":
        send(message, broadcast=True)

@socketio.on('image')
def handle_image(image_data):
    print("Received image data:", image_data[:50])  # Imprime solo los primeros 50 caracteres para verificar que se recibió algún dato
    emit('image', image_data, broadcast=True)  # Envía la imagen a todos los clientes conectados

@app.route('/')
def index():
    return redirect(url_for('access_code_page'))

@app.route('/access_code')
def access_code_page():
    return render_template("access_code.html")

@app.route('/verify_access_code', methods=['POST'])
def verify_access_code():
    global access_code_value
    user_code = request.form.get('code')
    print("User code:", user_code)
    print("Access code:", access_code_value)
    if str(user_code) == access_code_value:
        return redirect(url_for('username_page'))
    else:
        return redirect(url_for('access_code_incorrect'))

@app.route('/username')
def username_page():
    return render_template("username.html")

@app.route('/set_username', methods=['POST'])
def set_username():
    username = request.form.get('username')
    session['username'] = username
    return redirect(url_for('chat'))

@app.route('/chat')
def chat():
    username = session.get('username', 'Guest')
    return render_template("chat.html", username=username)

@app.route('/access_code_incorrect')
def access_code_incorrect():
    return render_template("access_code_incorrect.html")

@app.route('/upload_image', methods=['POST'])
def upload_image():
    image_data = request.files['file'].read()
    image_data = base64.b64encode(image_data).decode('utf-8')
    print("Image data received:", image_data)  # Agregar esta línea para depuración
    socketio.emit('image', image_data)
    return '', 204

if __name__ == "__main__":
    socketio.run(app, host="192.168.0.11")
