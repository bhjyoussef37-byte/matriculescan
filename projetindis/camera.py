import cv2
import imutils
import easyocr
import re
import time
import threading
import database

class CameraSystem:
    def __init__(self, arduino_controller=None):
        print("Chargement de l'IA (EasyOCR) en cours...")
        self.reader = easyocr.Reader(['en', 'ar']) 
        print("IA prête !")
        self.cap = cv2.VideoCapture(0)
        self.arduino = arduino_controller
        
        self.dernier_scan = 0
        self.delai_scan = 2.0
        self.statut_parking = "EN ATTENTE DE VEHICULE..."
        self.couleur_statut = (255, 255, 255)
        
        self.last_result = {
            "plate": "Aucune",
            "numbers": "",
            "letters": "",
            "status": "Inconnu",
            "confidence": 0
        }
        self.current_frame = None
        self.running = True
        self.lock = threading.Lock()

    def parse_plate(self, text):
        """Sépare les chiffres des lettres pour le dashboard."""
        numbers = "".join(re.findall(r'\d+', text))
        letters = "".join(re.findall(r'[\u0600-\u06FF]+', text))
        return numbers, letters

    def update(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Erreur de connexion à la caméra.")
                break

            frame = imutils.resize(frame, width=640)
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
            
            if location is not None:
                cv2.drawContours(frame, [location], -1, (0, 255, 0), 3)
                temps_actuel = time.time()
                
                if (temps_actuel - self.dernier_scan) > self.delai_scan:
                    self.dernier_scan = temps_actuel
                    
                    x, y, w, h = cv2.boundingRect(location)
                    y_debut, y_fin = max(0, y - 5), y + h + 5
                    x_debut, x_fin = max(0, x - 5), x + w + 5
                    plaque_image = gray[y_debut:y_fin, x_debut:x_fin]
                    
                    if plaque_image.size > 0:
                        plaque_image = cv2.resize(plaque_image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                        _, plaque_image = cv2.threshold(plaque_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                        
                        resultat = self.reader.readtext(plaque_image)
                        
                        if len(resultat) > 0:
                            texte_brut = resultat[0][1].upper()
                            conf = int(resultat[0][2] * 100) # Probabilité en pourcentage
                            texte_brut = texte_brut.replace('O', '0').replace('Q', '0').replace('I', '1').replace('Z', '2').replace('B', '8').replace('S', '5')
                            texte_plaque = re.sub(r'[^\d\u0600-\u06FF]', '', texte_brut)
                            
                            numbers, letters = self.parse_plate(texte_plaque)
                            is_vip = database.is_authorized(texte_plaque)
                            status = "Authorized" if is_vip else "Unauthorized"
                            
                            if self.arduino:
                                self.arduino.indicate_scan()
                            
                            if is_vip:
                                self.statut_parking = "ACCES AUTORISE - BARRIERE OUVERTE"
                                self.couleur_statut = (0, 255, 0)
                                if self.arduino:
                                    self.arduino.indicate_authorized()
                            else:
                                self.statut_parking = "ACCES REFUSE - PLAQUE INCONNUE"
                                self.couleur_statut = (0, 0, 255)
                            
                            database.save_scan(texte_plaque, numbers, letters, status, conf)
                            
                            with self.lock:
                                self.last_result = {
                                    "plate": texte_plaque,
                                    "numbers": numbers,
                                    "letters": letters,
                                    "status": status,
                                    "confidence": conf
                                }

            cv2.putText(frame, self.statut_parking, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.couleur_statut, 2)
            
            with self.lock:
                self.current_frame = frame.copy()

    def get_frame(self):
        with self.lock:
            if self.current_frame is None:
                return None
            return self.current_frame.copy()

    def stop(self):
        self.running = False
        self.cap.release()

if __name__ == "__main__":
    # Test mode if run directly
    cam = CameraSystem()
    database.init_db()
    t = threading.Thread(target=cam.update)
    t.start()
    
    while True:
        frame = cam.get_frame()
        if frame is not None:
            cv2.imshow('Camera Test', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cam.stop()
            break
    cv2.destroyAllWindows()