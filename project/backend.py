from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import re
from datetime import datetime
import database

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

latest_matricule = None

# Initialize database with some default allowed matricules
def init_allowed_matricules():
    allowed = database.get_allowed_matricules()
    if not allowed:
        database.add_allowed_matricule("12345أ6")
        database.add_allowed_matricule("98765ب1")
        database.add_allowed_matricule("11111د5")

init_allowed_matricules()

@app.route('/receive_matricule', methods=['POST'])
def receive_matricule():
    global latest_matricule
    data = request.get_json()
    if 'matricule' in data:
        matricule = data['matricule']
        latest_matricule = matricule
        
        # Extract numbers and letters
        numbers = ''.join(re.findall(r'\d', matricule))
        letters = ''.join(re.findall(r'[\u0600-\u06FF]', matricule))
        
        # Check if authorized
        allowed_list = database.get_allowed_matricules()
        is_authorized = matricule in allowed_list
        
        # Store in database
        database.add_scanned_matricule(matricule, numbers, letters, is_authorized)
        
        print(f"Received matricule: {matricule} - Authorized: {is_authorized}")
        return jsonify({"status": "success", "authorized": is_authorized}), 200
    return jsonify({"status": "error", "message": "No matricule provided"}), 400

@app.route('/get_matricule', methods=['GET'])
def get_matricule():
    if latest_matricule:
        # Separate numbers and letters
        numbers = re.findall(r'\d', latest_matricule)
        letters = re.findall(r'[\u0600-\u06FF]', latest_matricule)
        return jsonify({
            "matricule": latest_matricule,
            "numbers": ''.join(numbers),
            "letters": ''.join(letters)
        })
    return jsonify({"matricule": None, "numbers": "", "letters": ""})

@app.route('/history', methods=['GET'])
def get_history():
    history = database.get_scanned_history()
    return jsonify([{
        'matricule': item['matricule'],
        'numbers': item['numbers'],
        'letters': item['letters'],
        'timestamp': item['timestamp'],
        'is_authorized': item['is_authorized']
    } for item in history])

@app.route('/clear_history', methods=['POST'])
def clear_history():
    database.clear_scanned_history()
    return jsonify({"status": "success", "message": "History cleared"}), 200

@app.route('/allowed_matricules', methods=['GET'])
def get_allowed():
    allowed = database.get_allowed_matricules()
    return jsonify({"allowed_matricules": allowed})

@app.route('/add_allowed', methods=['POST'])
def add_allowed():
    data = request.get_json()
    if 'matricule' in data:
        success = database.add_allowed_matricule(data['matricule'])
        if success:
            return jsonify({"status": "success", "message": "Matricule added"}), 200
        else:
            return jsonify({"status": "error", "message": "Matricule already exists"}), 400
    return jsonify({"status": "error", "message": "No matricule provided"}), 400

@app.route('/remove_allowed', methods=['POST'])
def remove_allowed():
    data = request.get_json()
    if 'matricule' in data:
        database.remove_allowed_matricule(data['matricule'])
        return jsonify({"status": "success", "message": "Matricule removed"}), 200
    return jsonify({"status": "error", "message": "No matricule provided"}), 400

@app.route('/stats', methods=['GET'])
def get_stats():
    stats = database.get_database_stats()
    return jsonify(stats)

@app.route('/')
def index():
    return send_file('frontend.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
