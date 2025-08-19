# Sistema de Acceso Vehicular con Reconocimiento de Patentes

Este proyecto implementa un sistema de control de acceso vehicular utilizando un ESP32, simulado en Wokwi y con código fuente disponible en GitHub. El sistema reconoce patentes de vehículos y activa servomotores para abrir portones según los permisos configurados.

## Componentes del Hardware

- **ESP32 DevKit C**: Microcontrolador principal que ejecuta el código y controla los componentes.
- **2 Servomotores**: Para simular la apertura de los portones A y B.
- **2 LEDs**: Indican el estado de los relés (rojo para portón A y verde para portón B).
- **Resistencias**: 220Ω para limitar la corriente a los LEDs.
- **Botón**: Para apertura manual de los portones.

## Esquema de Conexiones

En la simulación de Wokwi, los componentes están conectados de la siguiente manera:

- **Servomotor Portón A**: Pin 18 (señal PWM), 3V3, GND
- **Servomotor Portón B**: Pin 19 (señal PWM), 3V3, GND
- **LED Relé A (rojo)**: Pin 2, GND (con resistencia de 220Ω)
- **LED Relé B (verde)**: Pin 15, GND (con resistencia de 220Ω)
- **Botón Manual**: Pin 4, GND

## Funcionalidades

- **Reconocimiento de patentes**: El sistema identifica placas vehiculares y compara con una base de datos.
- **Control de acceso**: Permite o deniega el acceso según los permisos asignados a cada patente.
- **Apertura diferenciada**: Según el tipo de permiso, se abre el portón A, el portón B, o ambos.
- **Modo manual**: Botón para abrir los portones en caso de emergencia o necesidad.

## Cómo Funciona

1. El sistema captura la imagen de la patente del vehículo (simulado en Wokwi).
2. Procesa la imagen y extrae el número de la patente.
3. Verifica en la base de datos si la patente tiene permiso de acceso.
4. Si está autorizada, activa el servomotor correspondiente para abrir el portón.
5. Los LEDs indican el estado de los relés y confirman la apertura.

## Recursos

- **Simulación en Wokwi**: [Ver simulación](https://wokwi.com/projects/439740289309594625)   (link)
- **Código fuente en GitHub**: [Repositorio](https://github.com/geromendez199/ESP32-Acceso-Vehicular)   (link)

[]()

## Implementación

El proyecto está implementado en Python para el ESP32 y utiliza bibliotecas para control de servomotores y procesamiento de señales digitales. La simulación permite probar el funcionamiento sin necesidad de hardware físico.

<aside>
Este proyecto demuestra la aplicación de sistemas embebidos en soluciones de seguridad y control de acceso, combinando hardware y software para resolver un problema práctico.

</aside>
