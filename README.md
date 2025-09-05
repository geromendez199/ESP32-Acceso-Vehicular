# Sistema de Acceso Vehicular con Reconocimiento de Patentes

Proyecto basado en **ESP32** y **MicroPython** que controla dos portones motorizados.
El sistema consulta la API de [Plate Recognizer](https://www.platerecognizer.com/) para
validar las patentes y abrir los portones solo cuando una matrícula autorizada es detectada.

## Características

- Reconocimiento de patentes mediante servicio web.
- Control de dos servomotores y LEDs indicativos.
- Ángulos `OPEN_ANGLE`/`CLOSE_ANGLE` y tiempo de apertura configurables.
- Tabla de pines editable para adaptarse al hardware disponible.
- Botón físico para apertura manual de respaldo.
- Modo de ejecución `single` (una sola consulta) o `loop` (consulta periódica).

## Hardware

| Pin ESP32 | Uso      | Descripción           |
|-----------|----------|-----------------------|
| 18        | Servo A  | PWM del portón A      |
| 19        | Servo B  | PWM del portón B      |
| 2         | LED A    | Indicador/relé portón A |
| 15        | LED B    | Indicador/relé portón B |
| 4         | Botón    | Apertura manual       |

## Requisitos

- Placa **ESP32 DevKit C** o simulador en [Wokwi](https://wokwi.com/).
- Firmware **MicroPython 1.20+**.
- Token válido de Plate Recognizer.
- Conexión WiFi a Internet.

## Configuración

1. Copiar `main.py` al ESP32 o al proyecto de Wokwi.
2. Reemplazar `PLATE_RECOGNIZER_TOKEN` por el token personal (el programa falla si queda el marcador por defecto).
3. Ajustar `AUTHORIZED_PLATES` y `IMAGE_URL` según la matrícula a validar.
4. Opcionalmente modificar `RUN_MODE`, `OPEN_ANGLE`, `CLOSE_ANGLE`, `HOLD_TIME_S` y los pines usados.

## Uso

Al iniciar, el programa valida el token, conecta a la red WiFi y realiza una consulta a la API según el modo configurado. Si la patente reconocida está en la lista blanca, `cycle_gates()` abre ambos servos durante el tiempo establecido y luego los cierra. El botón físico permite la apertura manual en cualquier momento.

## Simulación

El archivo `diagram.json` describe la conexión de hardware para Wokwi y puede usarse para probar el sistema sin hardware real.

## Desarrollo

Para verificar la sintaxis antes de subir al microcontrolador:

```bash
python -m py_compile main.py
```

## Créditos

Desarrollado por Gero Mendez y colaboradores.

