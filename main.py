import time
import _thread
import socket
from machine import PWM, Pin, ADC

# =================================================================
# CONFIGURACIÓN DE HARDWARE
# =================================================================
# Registro de corrimiento 74LS164 y LDR
DATA = Pin(14, Pin.OUT)
CLK = Pin(15, Pin.OUT)
sensor = ADC(Pin(26))

# Pines del Circuito Decrementador
# Salidas de la Pico hacia las entradas A (MSB), B (Medio), C (LSB) del circuito
pin_dec_A = Pin(17, Pin.OUT)  # MSB
pin_dec_B = Pin(16, Pin.OUT)  # Medio
pin_dec_C = Pin(28, Pin.OUT)  # LSB

# Entradas a la Pico desde las salidas del circuito decrementador
# X = Bit Más Significativo (MSB) -> Ambas luces delanteras
# Y = Bit de En Medio             -> Ambas luces intermitentes
# Z = Bit Menos Significativo (LSB)-> Ambas luces traseras
pin_out_Y = Pin(8, Pin.IN, Pin.PULL_DOWN)   # MSB -> Ambas delanteras
pin_out_Z = Pin(9, Pin.IN, Pin.PULL_DOWN)   # Medio -> Ambas intermitentes
pin_out_X = Pin(10, Pin.IN, Pin.PULL_DOWN)  # LSB -> Ambas traseras

# Motor 1: Tracción (Trasero)
pwm_ena = PWM(Pin(2))
pwm_ena.freq(1000)
pin_in1 = Pin(3, Pin.OUT)
pin_in2 = Pin(4, Pin.OUT)

# Motor 2: Dirección (Delantero)
pwm_enb = PWM(Pin(7))
pwm_enb.freq(1000)
pin_in3 = Pin(5, Pin.OUT)
pin_in4 = Pin(6, Pin.OUT)

# =================================================================
# MÁSCARAS DE BITS SEGÚN TU CABLEADO REAL EN EL 74LS164
# =================================================================
MASCARA_FRONTALES = (1 << 0) | (1 << 5)      # Bit 0 y Bit 5
MASCARA_TRASERAS = (1 << 1) | (1 << 7)       # Bit 1 y Bit 7
MASCARA_IZQ = 1 << 6                         # Bit 6
MASCARA_DER = 1 << 3                         # Bit 3
MASCARA_DIRECCIONALES = MASCARA_IZQ | MASCARA_DER

# Marchas / Velocidades
VEL_MARCHAS = {
    1: 35000,
    2: 45000,
    3: 55000,
    4: 65535
}

# =================================================================
# VARIABLES DE CONTROL GLOBAL
# =================================================================
estado_luces = {"lf": 0, "lb": 0, "ll": 0, "lr": 0, "ldr": 0, "corriendo": True}
modo_dec = 0  # 0: Apagado | 1: Automático (LDR) | 2: Manual (Botones)
marcha_actual = 1
leds_registro = -1

# =================================================================
# FUNCIONES DEL DECREMENTADOR Y REGISTRO DE CORRIMIENTO
# =================================================================
def enviar_bits_decrementador(valor):
    """Convierte un entero (0-7) a 3 bits: A (MSB), B (Medio), C (LSB)."""
    bit_A = (valor >> 2) & 1  # MSB
    bit_B = (valor >> 1) & 1  # Medio
    bit_C = valor & 1         # LSB

    pin_dec_A.value(bit_A)
    pin_dec_B.value(bit_B)
    pin_dec_C.value(bit_C)
    time.sleep_ms(5)

def actualizar_registro(valor_bits):
    """Envía los 8 bits al registro de corrimiento 74LS164."""
    for i in range(7, -1, -1):
        DATA.value((valor_bits >> i) & 1)
        CLK.value(1)
        CLK.value(0)

def apagar_decrementador():
    """Apaga el modo decrementador, pone A,B,C en 0 y apaga las luces."""
    global modo_dec, leds_registro
    modo_dec = 0
    enviar_bits_decrementador(0)
    estado_luces["lf"] = 0
    estado_luces["lb"] = 0
    estado_luces["ll"] = 0
    estado_luces["lr"] = 0
    estado_luces["ldr"] = 0
    leds_registro = 0
    actualizar_registro(0)

def hilo_luces():
    global leds_registro
    while estado_luces["corriendo"]:
        nuevo_estado = 0

        # MODO DECREMENTADOR (1: Automático LDR | 2: Manual Botones)
        if modo_dec in (1, 2):
            if modo_dec == 1:
                lectura = sensor.read_u16()
                intervalo = 7 - min(7, lectura // 8192)
                enviar_bits_decrementador(intervalo)

            if pin_out_X.value():
                nuevo_estado |= MASCARA_FRONTALES      # MSB -> Delanteras
            if modo_dec == 2 and pin_out_Y.value():
                nuevo_estado |= MASCARA_DIRECCIONALES  # Medio -> Intermitentes (solo manual)
            if pin_out_Z.value():
                nuevo_estado |= MASCARA_TRASERAS       # LSB -> Traseras

        # MODO NORMAL (Fotorresistencia 3 bits + Botones manuales)
        else:
            if estado_luces["ldr"]:
                lectura = sensor.read_u16()
                intervalo = 7 - min(7, lectura // 8192)
                if (intervalo >> 2) & 1:
                    nuevo_estado |= MASCARA_FRONTALES
                if intervalo & 1:
                    nuevo_estado |= MASCARA_TRASERAS

            parpadeo = (time.ticks_ms() // 400) % 2 == 0
            if estado_luces["lf"]:
                nuevo_estado |= MASCARA_FRONTALES
            if estado_luces["lb"]:
                nuevo_estado |= MASCARA_TRASERAS
            if estado_luces["ll"] and parpadeo:
                nuevo_estado |= MASCARA_IZQ
            if estado_luces["lr"] and parpadeo:
                nuevo_estado |= MASCARA_DER

        if nuevo_estado != leds_registro:
            leds_registro = nuevo_estado
            actualizar_registro(leds_registro)

        time.sleep_ms(80)

# =================================================================
# ACCIONES DE MOVIMIENTO Y RUTINAS
# =================================================================
def frenar():
    pwm_ena.duty_u16(0)
    pwm_enb.duty_u16(0)
    pin_in1.value(0); pin_in2.value(0)
    pin_in3.value(0); pin_in4.value(0)

def avanzar():
    pin_in1.value(1); pin_in2.value(0)
    pwm_ena.duty_u16(VEL_MARCHAS[marcha_actual])

def retroceder():
    pin_in1.value(0); pin_in2.value(1)
    pwm_ena.duty_u16(VEL_MARCHAS[marcha_actual])

def girar_izquierda():
    pwm_enb.duty_u16(65535)
    pin_in3.value(1); pin_in4.value(0)

def girar_derecha():
    pwm_enb.duty_u16(65535)
    pin_in3.value(0); pin_in4.value(1)

def centrar_direccion():
    pwm_enb.duty_u16(0)
    pin_in3.value(0); pin_in4.value(0)

def rutina_circulo():
    girar_izquierda()
    avanzar()
    time.sleep(4.0)
    frenar()

def rutina_infinito():
    girar_izquierda()
    avanzar()
    time.sleep(3.0)
    girar_derecha()
    time.sleep(3.0)
    frenar()

def rutina_zigzag():
    avanzar()
    for _ in range(3):
        girar_izquierda()
        time.sleep(0.8)
        girar_derecha()
        time.sleep(0.8)
    frenar()

# =================================================================
# CONEXIÓN WI-FI Y SERVIDOR TCP
# =================================================================
def conectar_wifi():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("Steve_kdl", "12345678")

    print("Conectando a Wi-Fi...", end="")
    while not wlan.isconnected():
        time.sleep(0.5)
        print(".", end="")
    ip = wlan.ifconfig()[0]  # Se extrae solo el primer elemento (la IP)
    print("\n¡Conectado!")
    print("Dirección IP de la Pico W:", ip)
    return ip

def procesar_comando(cmd):
    global marcha_actual, modo_dec
    partes = cmd.strip().split()
    if not partes:
        return

    op = partes[0]

    # Movimiento Básico
    if op == "adelante": avanzar()
    elif op == "atras": retroceder()
    elif op == "izquierda": girar_izquierda()
    elif op == "derecha": girar_derecha()
    elif op == "frenar": frenar()
    elif op == "centrar": centrar_direccion()

    # Marchas
    elif op == "marcha" and len(partes) == 2:
        marcha_actual = int(partes[1])

    # Luces normales
    elif op in ("lf", "lb", "ll", "lr", "ldr") and len(partes) == 2:
        if modo_dec != 0:
            modo_dec = 0
            enviar_bits_decrementador(0)
        estado_luces[op] = int(partes[1])

    # Rutinas Autónomas
    elif op == "circulo": rutina_circulo()
    elif op == "infinito": rutina_infinito()
    elif op == "zigzag": rutina_zigzag()

    # Comandos del Decrementador
    elif op == "dec_auto" and len(partes) == 2:
        if int(partes[1]) == 1:
            modo_dec = 1
            print("Modo decrementador AUTOMÁTICO activado")
        else:
            apagar_decrementador()
            print("Modo decrementador APAGADO")

    elif op == "dec_man" and len(partes) == 4:
        modo_dec = 2
        _, bit_a, bit_b, bit_c = partes
        pin_dec_A.value(int(bit_a))
        pin_dec_B.value(int(bit_b))
        pin_dec_C.value(int(bit_c))
        print(f"Decrementador MANUAL -> A(MSB)={bit_a}, B(Medio)={bit_b}, C(LSB)={bit_c}")

# Inicio del Sistema
apagar_decrementador()
_thread.start_new_thread(hilo_luces, ())
ip_servidor = conectar_wifi()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((ip_servidor, 5000))
server.listen(1)

print("Servidor listo en el puerto 5000. Esperando conexión...")

try:
    while True:
        conn, addr = server.accept()
        print(f"Conexión establecida desde: {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            for linea in data.decode('utf-8').splitlines():
                if linea.strip():
                    print(f"Comando recibido: {linea}")
                    procesar_comando(linea)
        conn.close()
except KeyboardInterrupt:
    print("\nServidor apagado.")
finally:
    estado_luces["corriendo"] = False
    apagar_decrementador()
    frenar()
