# Matricule Scanner Project

This project consists of a camera-based matricule scanner using OCR, a Flask backend to receive scanned matricules, and a simple web frontend to display them.

## Components

- `camera.py`: Scans matricule codes from camera feed using EasyOCR.
- `backend.py`: Flask server that receives matricule data and serves the web interface.
- `frontend.html`: Simple webpage displaying the latest scanned matricule, separating numbers and letters.
- `requirements.txt`: Python dependencies.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the backend:
   ```
   python backend.py
   ```
   This starts the Flask server on http://localhost:5000

3. Open the webpage at http://localhost:5000 to view the matricule display.

4. Run the camera scanner:
   ```
   python camera.py
   ```
   Make sure the camera URL in camera.py is correct for your setup.

## Usage

- The camera.py will scan for matricule codes and send them to the backend.
- The webpage will update every second to show the latest scanned matricule, with numbers and letters separated.

## Troubleshooting

- Ensure the camera URL in camera.py is accessible.
- If OCR fails, check camera quality and lighting.
- Backend must be running before starting camera.py.