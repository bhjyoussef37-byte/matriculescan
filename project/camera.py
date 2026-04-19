import cv2
import imutils
import easyocr
import numpy as np
import re
import time
import requests
import threading
from flask import Flask, Response, render_template_string
import database

print("Chargement de l'IA (EasyOCR) en cours...")
# On active l'anglais (pour les chiffres) et l'arabe (pour la lettre)
reader = easyocr.Reader(['en', 'ar']) 
print("IA prête !")

# Connexion à la webcam locale du PC

def open_webcam():
    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_VFW, cv2.CAP_ANY]
    for backend in backends:
        for device_index in range(6):
            cap = cv2.VideoCapture(device_index, backend)
            if cap.isOpened():
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                print(f"Using webcam device {device_index} with backend {backend} ({int(width)}x{int(height)})")
                return cap
            cap.release()
    return None


def can_show_window():
    try:
        test_frame = np.zeros((10, 10, 3), dtype=np.uint8)
        cv2.imshow('test_window', test_frame)
        cv2.waitKey(1)
        cv2.destroyWindow('test_window')
        return True
    except Exception:
        return False

app = Flask(__name__)
latest_frame = None
frame_lock = threading.Lock()

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Camera Preview</title>
        </head>
        <body>
            <h1>Live Camera Preview</h1>
            <img src="/video_feed" width="640" />
            <p>Use this page to check if the camera sees the matricule.</p>
        </body>
        </html>
    ''')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def generate_frames():
    global latest_frame
    while True:
        with frame_lock:
            if latest_frame is None:
                time.sleep(0.05)
                continue
            ret, buffer = cv2.imencode('.jpg', latest_frame)
        if not ret:
            time.sleep(0.05)
            continue
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.05)


def start_flask():
    app.run(host='0.0.0.0', port=5002, debug=False, use_reloader=False)

cap = open_webcam()
if cap is None:
    raise SystemExit("Cannot open any webcam device. Check camera drivers, permissions, or try a different device index.")

show_preview = can_show_window()
if show_preview:
    print("OpenCV GUI is available. Showing live preview.")
else:
    print("Warning: OpenCV GUI not available. Starting browser stream on http://localhost:5002")
    threading.Thread(target=start_flask, daemon=True).start()

# --- LISTE VIP DU PARKING ---
# Load authorized matricules from database
plaques_autorisees = database.get_allowed_matricules()
print(f"Loaded {len(plaques_autorisees)} authorized matricules from database")

# --- VARIABLES DU SYSTÈME AUTOMATIQUE ---
dernier_scan = 0
delai_scan = 2.0 # Le système attend 2 secondes entre chaque scan pour ne pas surchauffer
statut_parking = "EN ATTENTE DE VEHICULE..."
couleur_statut = (255, 255, 255) # Texte en blanc par défaut

last_status = None

while True:
    ret, frame = cap.read()
    if not ret or frame is None or frame.size == 0:
        print("Erreur de connexion à la caméra ou image invalide.")
        break

    # --- ÉTAPE 1 : PRÉTRAITEMENT POUR TROUVER LE RECTANGLE ---
    frame = imutils.resize(frame, width=600)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    bfilter = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(bfilter, 30, 200)

    keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(keypoints)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    
    location = None
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:
            location = approx
            break 
            
    # --- ÉTAPE 2 : LA LOGIQUE DE LECTURE ---
    # Si la caméra voit un rectangle (une plaque)
    if location is not None:
        # On dessine un cadre vert de confirmation sur l'image
        cv2.drawContours(frame, [location], -1, (0, 255, 0), 3)

        temps_actuel = time.time()
        
        # Le capteur virtuel : On scanne uniquement si 2 secondes se sont écoulées
        if (temps_actuel - dernier_scan) > delai_scan:
            print("\n--- Scan en cours ---")
            dernier_scan = temps_actuel # On remet le chronomètre à zéro
            
            x, y, w, h = cv2.boundingRect(location)
            
            # Découpage avec marge de sécurité (Padding) pour ne pas couper les lettres
            y_debut = max(0, y - 5)
            y_fin = y + h + 5
            x_debut = max(0, x - 5)
            x_fin = x + w + 5
            plaque_image = gray[y_debut:y_fin, x_debut:x_fin]
            
            # Amélioration de l'image (Zoom x2 + Contraste Noir & Blanc pur)
            plaque_image = cv2.resize(plaque_image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            _, plaque_image = cv2.threshold(plaque_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # L'IA fait son travail
            resultat = reader.readtext(plaque_image)
            
            if len(resultat) > 0:
                # --- ÉTAPE 3 : NETTOYAGE DU TEXTE ---
                texte_brut = resultat[0][1].upper()
                
                # Correction intelligente des erreurs classiques de l'IA
                texte_brut = texte_brut.replace('O', '0').replace('Q', '0').replace('I', '1').replace('Z', '2').replace('B', '8').replace('S', '5')
                
                # Le Filtre Absolu : On supprime tout ce qui n'est pas un chiffre ou une lettre arabe
                texte_plaque = re.sub(r'[^\d\u0600-\u06FF]', '', texte_brut)
                
                # --- ÉTAPE 4 : LA BARRIÈRE DE PARKING ---
                # On vérifie si le texte final est dans la liste VIP
                try:
                    requests.post('http://localhost:5000/receive_matricule', json={'matricule': texte_plaque}, timeout=1)
                except:
                    pass  # Ignore if backend is not running
                
                if texte_plaque in plaques_autorisees:
                    statut_parking = "ACCES AUTORISE - BARRIERE OUVERTE"
                    couleur_statut = (0, 255, 0) # Vert
                    print(f"✅ Succès : Plaque {texte_plaque} reconnue. Ouverture.")
                else:
                    statut_parking = "ACCES REFUSE - PLAQUE INCONNUE"
                    couleur_statut = (0, 0, 255) # Rouge
                    print(f"❌ Refus : Plaque {texte_plaque} non autorisée.")
            else:
                print("⚠️ Impossible de lire la plaque. Image trop floue.")

    # --- ÉTAPE 5 : AFFICHAGE SUR L'ÉCRAN ---
    # On affiche l'état de la barrière en haut à gauche de la vidéo
    cv2.putText(frame, statut_parking, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, couleur_statut, 2)

    with frame_lock:
        latest_frame = frame.copy()

    if show_preview:
        cv2.imshow('Prototype Parking Intelligent', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        if statut_parking != last_status:
            print(statut_parking)
            last_status = statut_parking
        time.sleep(0.1)

cap.release()
if show_preview:
    cv2.destroyAllWindows()