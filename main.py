# main.py — Doble portón + botón + Plate Recognizer (form-urlencoded) + cierre por TIMER (20 s)
# MicroPython para Wokwi

from machine import Pin, PWM
from time import sleep
import network
import urequests as requests
import ujson as json
import re

# =========================
# CONFIGURACIÓN
# =========================
# 👉 Pegá acá tu token de Plate Recognizer
PLATE_RECOGNIZER_TOKEN = "PEGA_AQUI_TU_TOKEN"

# Endpoint API (no tocar)
PLATE_RECOGNIZER_URL   = "https://api.platerecognizer.com/v1/plate-reader/"

# URL RAW de tu foto en GitHub (link directo)
IMAGE_URL = "https://raw.githubusercontent.com/geromendez199/ESP32-Acceso-Vehicular/main/patente/PatenteHyundai.png"

# Patentes autorizadas
AUTHORIZED_PLATES = ["AH084IB"]

# Modo de ejecución
RUN_MODE = "single"     # "single" = llama 1 vez al API; "loop" = consulta cada LOOP_DELAY_S
LOOP_DELAY_S = 12

# Cierre por tiempo fijo (20 s)
HOLD_TIME_S = 20

# Pines (coinciden con el diagram.json final)
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
ledA   = Pin(LED_A_PIN, Pin.OUT)
ledB   = Pin(LED_B_PIN, Pin.OUT)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)  # a GND; presionado = 0

# =========================
# UTILIDADES
# =========================
def normalize_plate(s: str) -> str:
    """Limpia a A–Z/0–9 y mayúsculas (soporta 'ah-084-ib')."""
    return re.sub(r'[^A-Za-z0-9]', '', (s or '')).upper()

WHITELIST = {normalize_plate(p) for p in AUTHORIZED_PLATES}

def angle_to_ns(angle):
    angle = max(0, min(180, angle))
    return int(500_000 + (2_000_000 * angle) / 180)  # 0.5–2.5 ms @ 50 Hz

def set_servo_angle(servo, angle):
    servo.duty_ns(angle_to_ns(angle))

def open_both_gates(open_angle=90, close_angle=0, hold_s=HOLD_TIME_S):
    # “Relés” ON
    ledA.value(1); ledB.value(1)
    # Abrir
    set_servo_angle(servoA, open_angle)
    set_servo_angle(servoB, open_angle)
    # Mantener abierto por tiempo fijo
    sleep(hold_s)
    # Cerrar
    set_servo_angle(servoA, close_angle)
    set_servo_angle(servoB, close_angle)
    # “Relés” OFF
    ledA.value(0); ledB.value(0)

def manual_pressed() -> bool:
    return button.value() == 0  # con PULL_UP: 0 = presionado

# =========================
# RED / WIFI
# =========================
def wifi_connect(ssid="Wokwi-GUEST", key=""):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando a WiFi...", ssid)
        wlan.connect(ssid, key)
        for _ in range(40):  # ~8 s
            if wlan.isconnected():
                break
            sleep(0.2)
    print("WiFi:", "OK" if wlan.isconnected() else "FALLO")
    return wlan.isconnected()

# =========================
# LPR: Plate Recognizer (form-urlencoded para evitar 201 sin results)
# =========================
def recognize_plate(image_url: str):
    """
    Envía upload_url como application/x-www-form-urlencoded y acepta 200/201.
    Devuelve (plate_norm, plate_raw, score) o (None, None, None).
    """
    headers = {
        "Authorization": "Token " + PLATE_RECOGNIZER_TOKEN,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    # regions=ar ayuda con formato argentino
    body = "upload_url={}&regions=ar".format(image_url)
    try:
        r = requests.post(PLATE_RECOGNIZER_URL, headers=headers, data=body)
        if r.status_code in (200, 201):
            try:
                data = r.json()
            except Exception:
                data = json.loads(r.text)
            results = data.get("results") or []
            if results:
                first = results[0]
                plate_raw = first.get("plate") or ""
                score = first.get("score")
                plate_norm = normalize_plate(plate_raw)
                return plate_norm, plate_raw, score
            else:
                print("Sin results. Respuesta:", data)
        else:
            print("PlateRecog HTTP", r.status_code, "-", getattr(r, "text", ""))
    except Exception as e:
        print("LPR error:", e)
    return None, None, None

# =========================
# APP
# =========================
def main():
    # Estado inicial
    set_servo_angle(servoA, 0)
    set_servo_angle(servoB, 0)
    ledA.value(0); ledB.value(0)

    print("Whitelist:", WHITELIST)
    wifi_connect()  # necesario para el LPR

    def do_one_request():
        plate_norm, plate_raw, score = recognize_plate(IMAGE_URL)
        print("Detectada:", plate_raw, "| Normalizada:", plate_norm, "| Score:", score)
        if plate_norm and plate_norm in WHITELIST:
            print("Autorizada -> abrir (20 s)...")
            open_both_gates(90, 0, HOLD_TIME_S)
        else:
            print("No autorizada (o no detectada)")

    # Llamada inicial según modo
    if RUN_MODE == "single":
        do_one_request()
        print("Modo SINGLE: ya probaste la API. Queda el modo manual (botón).")

    print("Sistema listo. Botón = manual; API según RUN_MODE.")
    while True:
        # Apertura manual
        if manual_pressed():
            print("Botón: abrir (20 s)...")
            open_both_gates(90, 0, HOLD_TIME_S)
            # anti-rebote
            while manual_pressed():
                sleep(0.02)
            sleep(0.2)

        # Modo automático en loop (si querés monitoreo continuo)
        if RUN_MODE == "loop":
            do_one_request()
            sleep(LOOP_DELAY_S)
        else:
            sleep(0.1)

if __name__ == "__main__":
    main()
