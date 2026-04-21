from flask import Flask, render_template, Response, jsonify, request
from camera import CameraSystem
import database
import threading
import cv2
import time

app = Flask(__name__)

# Initialisation du système
database.init_db()
cam_system = CameraSystem()

# Lancement de la capture en arrière-plan
threading.Thread(target=cam_system.update, daemon=True).start()

def gen_frames():
    """Générateur pour le flux vidéo MJPEG."""
    while True:
        frame = cam_system.get_frame()
        if frame is not None:
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.05)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def get_status():
    with cam_system.lock:
        return jsonify(cam_system.last_result)

@app.route('/api/history')
def get_history():
    return jsonify(database.get_history())

@app.route('/api/stats')
def get_stats():
    return jsonify(database.get_stats())

@app.route('/api/authorized', methods=['GET', 'POST', 'DELETE'])
def manage_authorized():
    if request.method == 'GET':
        return jsonify(database.get_authorized_list())
    
    elif request.method == 'POST':
        data = request.json
        matricule = data.get('matricule')
        if matricule:
            success = database.add_authorized(matricule)
            return jsonify({"success": success})
        return jsonify({"success": False}), 400
        
    elif request.method == 'DELETE':
        matricule = request.args.get('matricule')
        if matricule:
            database.remove_authorized(matricule)
            return jsonify({"success": True})
        return jsonify({"success": False}), 400

if __name__ == '__main__':
    print("\n--- SERVEUR DASHBOARD ALPR DÉMARRÉ ---")
    print("Accédez à : http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
