# main.py — Doble portón + botón + Plate Recognizer + whitelist AH084IB (MicroPython)

from machine import Pin, PWM
from time import sleep
import network
import re
import urequests as requests
import ujson as json

# =========================
# CONFIGURACIÓN
# =========================
# Tu token de Plate Recognizer:
PLATE_RECOGNIZER_TOKEN = "TU_TOKEN_AQUI"
PLATE_RECOGNIZER_URL = "https://api.platerecognizer.com/v1/plate-reader/"

# URL pública de tu foto (cámbiala por la tuya)
IMAGE_URL = "https://i.imgur.com/your_photo.jpg"  # <-- reemplazá esto por tu link directo

# Patente autorizada (normalizada automáticamente)
AUTHORIZED_PLATES = ["AH084IB"]

# Pines (coinciden con el diagram.json sugerido)
SERVO_A_PIN = 18
SERVO_B_PIN = 19
LED_A_PIN   = 2
LED_B_PIN   = 15
BUTTON_PIN  = 4

# =========================
# HARDWARE
# =========================
servoA = PWM(Pin(SERVO_A_PIN), freq=50)
servoB = PWM(Pin(SERVO_B_PIN), freq=50)
ledA = Pin(LED_A_PIN, Pin.OUT)
ledB = Pin(LED_B_PIN, Pin.OUT)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)  # a GND con PULL_UP (presionado=0)

# =========================
# UTILIDADES
# =========================
def normalize_plate(s: str) -> str:
    """Deja solo A-Z/0-9 y mayúsculas (soporta 'AH-084-IB', 'ah084ib', etc.)."""
    return re.sub(r'[^A-Za-z0-9]', '', (s or '')).upper()

WHITELIST = {normalize_plate(p) for p in AUTHORIZED_PLATES}

def angle_to_ns(angle):
    angle = max(0, min(180, angle))
    # 0.5ms..2.5ms a 50 Hz
    return int(500_000 + (2_000_000 * angle) / 180)

def set_servo_angle(servo, angle):
    servo.duty_ns(angle_to_ns(angle))

def open_both_gates(open_angle=90, hold_s=2, close_angle=0):
    # “Relés” ON
    ledA.value(1); ledB.value(1)
    # Abrir
    set_servo_angle(servoA, open_angle)
    set_servo_angle(servoB, open_angle)
    sleep(hold_s)
    # Cerrar
    set_servo_angle(servoA, close_angle)
    set_servo_angle(servoB, close_angle)
    # “Relés” OFF
    ledA.value(0); ledB.value(0)

def manual_pressed() -> bool:
    return button.value() == 0  # con PULL_UP, presionado = 0

# =========================
# RED
# =========================
def wifi_connect(ssid="Wokwi-GUEST", key=""):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando a WiFi...", ssid)
        wlan.connect(ssid, key)
        for _ in range(40):  # ~8s
            if wlan.isconnected():
                break
            sleep(0.2)
    print("WiFi:", "OK" if wlan.isconnected() else "FALLO")
    return wlan.isconnected()

# =========================
# LPR: Plate Recognizer (URL de imagen)
# =========================
def recognize_plate(image_url: str) -> str | None:
    """
    Envía una URL de imagen a Plate Recognizer y devuelve la patente detectada (str) o None.
    Consejo: podés pasar "regions": ["ar"] para priorizar formato argentino.
    """
    headers = {
        "Authorization": "Token " + PLATE_RECOGNIZER_TOKEN,
        "Content-Type": "application/json",
    }
    body = {
        "upload_url": image_url,
        "regions": ["ar"]  # sesgo regional (opcional, ayuda en AR)
    }
    try:
        r = requests.post(PLATE_RECOGNIZER_URL, headers=headers, data=json.dumps(body))
        status = r.status_code
        if status == 200:
            data = r.json()
            results = data.get("results") or []
            if results:
                plate = results[0].get("plate")
                return plate.upper() if plate else None
            return None
        else:
            print("PlateRecog HTTP", status)
            # print(r.text)  # descomenta para debug
            return None
    except Exception as e:
        print("PlateRecog error:", e)
        return None

# =========================
# APP
# =========================
def main():
    # Posición inicial
    set_servo_angle(servoA, 0)
    set_servo_angle(servoB, 0)
    ledA.value(0); ledB.value(0)
    print("Whitelist:", WHITELIST)

    # Conexión WiFi (necesaria para llamar al API)
    if not wifi_connect():
        print("Sin WiFi. Modo manual únicamente.")
    
    print("Sistema doble portón listo.")
    while True:
        # 1) Modo manual por botón
        if manual_pressed():
            print("Botón: abrir ambos portones")
            open_both_gates(90, 2, 0)
            # anti-rebote: esperar a soltar
            while manual_pressed():
                sleep(0.02)
            sleep(0.2)

        # 2) Modo automático: LPR con tu foto
        plate_raw = recognize_plate(IMAGE_URL)
        plate = normalize_plate(plate_raw)
        print("Detectada:", plate_raw, "->", plate)

        if plate and plate in WHITELIST:
            print("Autorizada -> abrir ambos portones")
            open_both_gates(90, 2, 0)
        else:
            print("No autorizada")

        sleep(3)  # bajá la frecuencia para no quemar créditos del API

if __name__ == "__main__":
    main()
