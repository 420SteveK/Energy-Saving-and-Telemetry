"""
Prueba de luces y señales del carro (sin motores).

Comandos por consola:
    lf [1,0]   luces frontales
    lb [1,0]   luces traseras
    ll [1,0]   direccional izquierda (parpadea)
    lr [1,0]   direccional derecha (parpadea)
    ldr [1,0]  control automático por fotorresistencia
    freno      enciende las luces traseras 1.5 segundos
    salir      termina y apaga todo

Un segundo hilo (_thread) es el único que escribe en el registro 74LS164.
"""
import time
import _thread
from machine import Pin, ADC

DATA = Pin(14, Pin.OUT)
CLK = Pin(15, Pin.OUT)
sensor = ADC(Pin(26))

# Posición de cada LED en el registro (QA = 0 ... QH = 7). Ajustar al cableado.
MASCARA_FRONTALES = (1 << 0) | (1 << 1)
MASCARA_TRASERAS = (1 << 2) | (1 << 3)
MASCARA_IZQ = 1 << 4
MASCARA_DER = 1 << 5

TIEMPO_FRENO = 1500     # milisegundos
UMBRAL_ON = 5000        # menos luz que esto -> encender (calibrar)
UMBRAL_OFF = 15000      # más luz que esto -> apagar (calibrar)

luz = {
    "lf": 0, "lb": 0, "ll": 0, "lr": 0, "ldr": 0,
    "freno": time.ticks_ms(),
    "corriendo": True,
}
leds = 0


def actualizar():
    """Envía los 8 bits de 'leds' al 74LS164 (primero el bit 7, al final el 0)."""
    for i in range(7, -1, -1):
        DATA.value((leds >> i) & 1)
        CLK.value(1)
        CLK.value(0)


def hilo_luces():
    global leds
    oscuro = False
    while luz["corriendo"]:
        # Modo automático con histéresis
        if luz["ldr"]:
            valor = sensor.read_u16()
            if not oscuro and valor < UMBRAL_ON:
                oscuro = True
            elif oscuro and valor > UMBRAL_OFF:
                oscuro = False
        else:
            oscuro = False

        frente = oscuro if luz["ldr"] else luz["lf"]
        frenando = time.ticks_diff(luz["freno"], time.ticks_ms()) > 0
        atras = (oscuro if luz["ldr"] else luz["lb"]) or frenando
        parpadeo = (time.ticks_ms() // 400) % 2 == 0

        nuevo = 0
        if frente:
            nuevo |= MASCARA_FRONTALES
        if atras:
            nuevo |= MASCARA_TRASERAS
        if luz["ll"] and parpadeo:
            nuevo |= MASCARA_IZQ
        if luz["lr"] and parpadeo:
            nuevo |= MASCARA_DER

        if nuevo != leds:            # solo se reenvía si algo cambió
            leds = nuevo
            actualizar()
        time.sleep_ms(100)

    leds = 0                         # al terminar, apagar todo
    actualizar()


def procesar(linea):
    partes = linea.strip().lower().split()
    if not partes:
        return
    cmd = partes[0]
    if cmd == "freno":
        luz["freno"] = time.ticks_add(time.ticks_ms(), TIEMPO_FRENO)
        return
    if len(partes) != 2 or cmd not in ("lf", "lb", "ll", "lr", "ldr"):
        print("Use: lf, lb, ll, lr o ldr seguido de 1 o 0 (ej: ll 1), o 'freno'")
        return
    if partes[1] not in ("0", "1"):
        print(cmd + " acepta 1 (encender) o 0 (apagar).")
        return
    luz[cmd] = int(partes[1])


_thread.start_new_thread(hilo_luces, ())
print("Comandos: lf, lb, ll, lr, ldr, freno, salir")

try:
    while True:
        linea = input("> ")
        if linea.strip().lower() == "salir":
            break
        procesar(linea)
except KeyboardInterrupt:
    print("\nPrograma interrumpido.")
finally:
    luz["corriendo"] = False         # el hilo apaga las luces y termina
    time.sleep(1)
    print("Luces apagadas.")
