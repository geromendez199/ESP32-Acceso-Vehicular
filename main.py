"""Sistema de acceso vehicular con ESP32 y Plate Recognizer.

Este módulo controla dos servos para un portón doble, valida patentes
contra una lista blanca y permite apertura manual mediante un botón. Se
optó por una organización modular para facilitar el mantenimiento y la
configuración.
"""

from machine import Pin, PWM
from time import sleep
import network
import urequests as requests
import ujson as json
import re

try:  # solo presente en MicroPython; permite ahorrar memoria con 'const'
    from micropython import const
except ImportError:  # pragma: no cover - compatibilidad con CPython
    def const(x):
        return x

# =========================
# CONFIGURACIÓN
# =========================
OPEN_ANGLE = const(90)
CLOSE_ANGLE = const(0)

# 👉 Pegá acá tu token de Plate Recognizer
PLATE_RECOGNIZER_TOKEN = "PEGA_AQUI_TU_TOKEN"

# Endpoint API (no tocar)
PLATE_RECOGNIZER_URL = const("https://api.platerecognizer.com/v1/plate-reader/")

# URL RAW de tu foto en GitHub (link directo)
IMAGE_URL = (
    "https://raw.githubusercontent.com/geromendez199/ESP32-Acceso-Vehicular/main/patente/PatenteHyundai.png"
)

# Patentes autorizadas
AUTHORIZED_PLATES = ["AH084IB"]

# Modo de ejecución
RUN_MODE = "single"  # "single" = llama 1 vez al API; "loop" = consulta cada LOOP_DELAY_S
LOOP_DELAY_S = const(12)

# Cierre por tiempo fijo (20 s)
HOLD_TIME_S = const(20)

# Frecuencia de los servos PWM
SERVO_FREQ = const(50)

# Pines (coinciden con el diagram.json final)
SERVO_A_PIN = const(18)
SERVO_B_PIN = const(19)
LED_A_PIN = const(2)
LED_B_PIN = const(15)
BUTTON_PIN = const(4)

# =========================
# UTILIDADES
# =========================
PLATE_RE = re.compile(r"[^A-Za-z0-9]")


def normalize_plate(s: str) -> str:
    """Limpia a A–Z/0–9 y mayúsculas (soporta 'ah-084-ib')."""
    return PLATE_RE.sub("", (s or "")).upper()


WHITELIST = {normalize_plate(p) for p in AUTHORIZED_PLATES}


def validate_token() -> None:
    """Verifica que el token de Plate Recognizer haya sido configurado."""
    if "PEGA_AQUI" in PLATE_RECOGNIZER_TOKEN:
        raise ValueError("Debes asignar un token válido a PLATE_RECOGNIZER_TOKEN")


def angle_to_ns(angle: int) -> int:
    """Convierte un ángulo (0–180) al duty en nanosegundos para un servo PWM."""
    angle = max(0, min(180, angle))
    return int(500_000 + (2_000_000 * angle) / 180)  # 0.5–2.5 ms @ 50 Hz


class GateController:
    """Administra dos servos y sus LEDs asociados."""

    def __init__(
        self,
        servo_pins=(SERVO_A_PIN, SERVO_B_PIN),
        led_pins=(LED_A_PIN, LED_B_PIN),
        freq=SERVO_FREQ,
        open_angle=OPEN_ANGLE,
        close_angle=CLOSE_ANGLE,
    ):
        self.servos = [PWM(Pin(servo_pins[0]), freq=freq), PWM(Pin(servo_pins[1]), freq=freq)]
        self.leds = [Pin(led_pins[0], Pin.OUT), Pin(led_pins[1], Pin.OUT)]
        self.open_angle = open_angle
        self.close_angle = close_angle
        self.close()  # posición segura inicial

    def _set_servo(self, servo: PWM, angle: int) -> None:
        servo.duty_ns(angle_to_ns(angle))

    def open(self, angle: int | None = None) -> None:
        """Abre ambos portones y enciende los LEDs."""
        ang = self.open_angle if angle is None else angle
        for led in self.leds:
            led.value(1)
        for s in self.servos:
            self._set_servo(s, ang)

    def close(self, angle: int | None = None) -> None:
        """Cierra ambos portones y apaga los LEDs."""
        ang = self.close_angle if angle is None else angle
        for s in self.servos:
            self._set_servo(s, ang)
        for led in self.leds:
            led.value(0)

    def cycle(
        self,
        open_angle: int | None = None,
        close_angle: int | None = None,
        hold_s: int = HOLD_TIME_S,
    ) -> None:
        """Abre, espera ``hold_s`` segundos y vuelve a cerrar."""
        self.open(open_angle)
        sleep(hold_s)
        self.close(close_angle)


button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)  # a GND; presionado = 0


def manual_pressed() -> bool:
    """Indica si el botón manual está presionado."""
    return button.value() == 0  # con PULL_UP: 0 = presionado


# =========================
# RED / WIFI
# =========================
def wifi_connect(ssid: str = "Wokwi-GUEST", key: str = "") -> bool:
    """Intenta conectar al WiFi y devuelve True si tuvo éxito."""
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


class PlateRecognizer:
    """Cliente simple para la API de Plate Recognizer."""

    def __init__(self, token: str, url: str = PLATE_RECOGNIZER_URL) -> None:
        self.url = url
        self.headers = {
            "Authorization": "Token " + token,
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def recognize(self, image_url: str):
        """Devuelve (plate_norm, plate_raw, score) o (None, None, None)."""
        body = "upload_url={}&regions=ar".format(image_url)
        r = None
        try:
            r = requests.post(self.url, headers=self.headers, data=body)
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
                print("Sin results. Respuesta:", data)
            else:
                print("PlateRecog HTTP", r.status_code, "-", getattr(r, "text", ""))
        except Exception as e:  # pragma: no cover - comunicación externa
            print("LPR error:", e)
        finally:
            if r is not None:
                try:
                    r.close()
                except Exception:
                    pass
        return None, None, None


# =========================
# APP
# =========================
def main() -> None:
    """Punto de entrada principal del sistema."""
    gates = GateController()
    print("Whitelist:", WHITELIST)
    validate_token()
    wifi_ok = wifi_connect()  # necesario para el LPR
    if not wifi_ok:
        print("Sin WiFi: solo modo manual")

    recognizer = PlateRecognizer(PLATE_RECOGNIZER_TOKEN)

    def do_one_request() -> None:
        plate_norm, plate_raw, score = recognizer.recognize(IMAGE_URL)
        print(f"Detectada: {plate_raw} | Normalizada: {plate_norm} | Score: {score}")
        if plate_norm and plate_norm in WHITELIST:
            print(f"Autorizada -> abrir ({HOLD_TIME_S} s)...")
            gates.cycle()
        else:
            print("No autorizada (o no detectada)")

    if RUN_MODE == "single" and wifi_ok:
        do_one_request()
        print("Modo SINGLE: ya probaste la API. Queda el modo manual (botón).")

    print("Sistema listo. Botón = manual; API según RUN_MODE.")
    while True:
        if manual_pressed():
            print(f"Botón: abrir ({HOLD_TIME_S} s)...")
            gates.cycle()
            while manual_pressed():  # anti-rebote
                sleep(0.02)
            sleep(0.2)

        if RUN_MODE == "loop" and wifi_ok:
            do_one_request()
            sleep(LOOP_DELAY_S)
        else:
            sleep(0.1)


if __name__ == "__main__":
    main()

