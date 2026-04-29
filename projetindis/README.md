# 🚀 ALPR Neural · Automated License Plate Recognition

A futuristic, high-performance license plate recognition system built with Python, Flask, and EasyOCR. This system features a real-time web dashboard with a "Neural" aesthetic, automated detection history, and a VIP authorization management system.

![Neural Dashboard](https://img.shields.io/badge/UI-Cyberpunk-00f5c8?style=for-the-badge)
![Tech Stack](https://img.shields.io/badge/Stack-Python%20|%20Flask%20|%20OCR-7b5cff?style=for-the-badge)

## ✨ Key Features

- **Live Video Stream**: Real-time MJPEG feed directly in your browser.
- **Neural Inference Engine**: High-accuracy plate detection using EasyOCR (English/Arabic support).
- **Confidence Tracking**: Real-time probability scoring for every detection.
- **Smart History**: Persistent logs of every vehicle including timestamps and recognition confidence.
- **VIP Management**: Add or remove authorized matricules directly from the dashboard.
- **Hardware Integration**: Real-time Arduino feedback with LED indicators for authorized/unauthorized access.
- **Persistence**: SQLite-backed storage for authorized lists and scanning history.

## 🛠️ Tech Stack

- **Backend**: Python 3.12, Flask
- **Vision**: OpenCV, Imutils
- **OCR Engine**: EasyOCR (PyTorch based)
- **Database**: SQLite3
- **Hardware**: Arduino (Serial Communication)
- **Frontend**: Vanilla JS, Space Grotesk Typography, Futuristic CSS

## 🏁 Quick Start

### 1. Installation
Ensure you have Python 3.10+ installed. Install the required dependencies:

```bash
pip install flask opencv-python easyocr imutils torch torchvision torchaudio pyserial
```

*Note: The first run will take a few minutes as it downloads the OCR models (approx. 100MB).*

### 2. Configuration
The system is configured to use the local camera (index 0). If you are using a different camera or a phone link, you can adjust this in `camera.py`:

```python
self.cap = cv2.VideoCapture(0) # Change to URL or index
```

### 3. Hardware Setup (Optional)
To use the LED feedback system:
1.  **Wiring**: 
    - **Pin 8**: Connect to a "Scan" LED.
    - **Pin 12**: Connect to an "Authorized" LED.
2.  **Arduino Code**: Upload the sketch located in `arduino_code/arduino_led_test/arduino_led_test.ino` to your Arduino board.
3.  **Test**: Run `python test_arduino.py` to verify the connection.

### 3. Launching the System
Start the Flask backend:

```bash
python backend.py
```

Open your browser and navigate to:
**[http://localhost:5000](http://localhost:5000)**

## 📂 Project Structure

- `backend.py`: Flask server and API endpoints.
- `camera.py`: The ALPR recognition engine and camera thread.
- `database.py`: Handles SQLite persistence for VIPs and History.
- `templates/index.html`: The futuristic "Neural" web dashboard.
- `arduino_controller.py`: Logic for communicating with the Arduino.
- `test_arduino.py`: Standalone script to test your hardware wiring.
- `arduino_code/`: Contains the `.ino` sketch for the Arduino board.
- `plates.db`: Local database file (generated on first run).

## ⚠️ Important Note
This system runs on **CPU** by default. For real-time performance (>10 FPS recognition), a CUDA-capable GPU is recommended. The first detection might be slow as the models initialize.

---
*Created with ❤️ for Advanced ALPR Projects.*
