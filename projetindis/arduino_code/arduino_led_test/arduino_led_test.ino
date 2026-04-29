/*
  ALPR Arduino LED Indicator

  This sketch receives serial commands from the Python backend to control LEDs
  indicating the status of the ALPR system.

  Wiring:
  - Pin 8: Scan LED (Indicates any plate was scanned)
  - Pin 12: Authorized LED (Indicates the scanned plate is authorized)
  - GND: Common ground

  Commands recognized (must be terminated with newline \n):
  - "SCAN" -> Blinks the Scan LED (Pin 8)
  - "AUTHORIZED" -> Blinks the Authorized LED (Pin 12)
  - "STATUS" -> Returns the status of the LEDs
*/

const int SCAN_LED_PIN = 8;
const int AUTH_LED_PIN = 12;

void setup() {
  Serial.begin(9600);
  
  pinMode(SCAN_LED_PIN, OUTPUT);
  pinMode(AUTH_LED_PIN, OUTPUT);
  
  // Turn off LEDs initially
  digitalWrite(SCAN_LED_PIN, LOW);
  digitalWrite(AUTH_LED_PIN, LOW);
  
  Serial.println("ALPR ARDUINO READY");
}

void blinkLED(int pin, int times, int duration_ms) {
  for (int i = 0; i < times; i++) {
    digitalWrite(pin, HIGH);
    delay(duration_ms);
    digitalWrite(pin, LOW);
    if (i < times - 1) {
      delay(duration_ms);
    }
  }
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove whitespace/carriage returns
    
    if (command == "SCAN") {
      Serial.println("ACK: SCAN");
      blinkLED(SCAN_LED_PIN, 2, 200); // Fast blink to indicate scan
    } 
    else if (command == "AUTHORIZED") {
      Serial.println("ACK: AUTHORIZED");
      // Turn on Auth LED for 3 seconds
      digitalWrite(AUTH_LED_PIN, HIGH);
      delay(3000);
      digitalWrite(AUTH_LED_PIN, LOW);
    } 
    else if (command == "STATUS") {
      Serial.print("STATUS: SCAN_LED=");
      Serial.print(digitalRead(SCAN_LED_PIN));
      Serial.print(", AUTH_LED=");
      Serial.println(digitalRead(AUTH_LED_PIN));
    } 
    else if (command.length() > 0) {
      Serial.print("ERROR: Unknown command '");
      Serial.print(command);
      Serial.println("'");
    }
  }
}
