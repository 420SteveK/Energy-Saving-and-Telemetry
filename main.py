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

# Máscaras de bits para luces en el 74LS164
MASCARA_FRONTALES = (1 << 0) | (1 << 5)
MASCARA_TRASERAS = (1 << 1) | (1 << 2)
MASCARA_IZQ = 1 << 6
MASCARA_DER = 1 << 3

# Marchas / Velocidades 
VEL_MARCHAS = {
    1: 35000,  # Suave
    2: 45000,  # Media
    3: 55000,  # Rápida
    4: 65535   # Máxima potencia
}

# =================================================================
# VARIABLES DE CONTROL GLOBAL
# =================================================================
estado_luces = {"lf": 0, "lb": 0, "ll": 0, "lr": 0, "ldr": 0, "corriendo": True}
marcha_actual = 1
leds_registro = 0
UMBRAL_LUZ = 15000  

# =================================================================
# GESTIÓN DE LUCES 
# =================================================================
def actualizar_registro():
    global leds_registro
    for i in range(7, -1, -1):
        DATA.value((leds_registro >> i) & 1)
        CLK.value(1)
        CLK.value(0)

def hilo_luces():
    global leds_registro
    while estado_luces["corriendo"]:
        oscuro = False
        if estado_luces["ldr"]:
            if sensor.read_u16() < UMBRAL_LUZ:
                oscuro = True

        frente = oscuro or estado_luces["lf"]
        atras = oscuro or estado_luces["lb"]
        parpadeo = (time.ticks_ms() // 400) % 2 == 0

        nuevo_estado = 0
        if frente: nuevo_estado |= MASCARA_FRONTALES
        if atras: nuevo_estado |= MASCARA_TRASERAS
        if estado_luces["ll"] and parpadeo: nuevo_estado |= MASCARA_IZQ
        if estado_luces["lr"] and parpadeo: nuevo_estado |= MASCARA_DER

        if nuevo_estado != leds_registro:
            leds_registro = nuevo_estado
            actualizar_registro()
        time.sleep_ms(100)

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

# --- Patrones Especiales ---
def rutina_circulo():
    girar_izquierda()
    avanzar()
    time.sleep(4.0)
    frenar()

def rutina_infinito():
    # Bucle izquierdo
    girar_izquierda()
    avanzar()
    time.sleep(3.0)
    # Bucle derecho
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
    print("\n¡Conectado!")
    print("Dirección IP de la Pico W:", wlan.ifconfig()[0])
    return wlan.ifconfig()[0]

def procesar_comando(cmd):
    global marcha_actual
    partes = cmd.strip().split()
    if not partes: return
    
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
        print(f"Marcha cambiada a: {marcha_actual}")
        
    # Luces
    elif op in ["lf", "lb", "ll", "lr", "ldr"] and len(partes) == 2:
        estado_luces[op] = int(partes[1])
        
    # Rutinas Autónomas
    elif op == "circulo": rutina_circulo()
    elif op == "infinito": rutina_infinito()
    elif op == "zigzag": rutina_zigzag()

# Inicio del Sistema
_thread.start_new_thread(hilo_luces, ())
ip_servidor = conectar_wifi()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((ip_servidor, 5000))
server.listen(1)

print("Servidor listo en el puerto 5000. Esperando conexión de VS Code...")

try:
    while True:
        conn, addr = server.accept()
        print(f"Conexión establecida desde: {addr}")
        while True:
            data = conn.recv(1024)
            if not data: break
            comando = data.decode('utf-8')
            print(f"Comando recibido: {comando}")
            procesar_comando(comando)
        conn.close()
        print("Cliente desconectado. Esperando nueva conexión...")
except KeyboardInterrupt:
    print("\nServidor apagado de forma segura.")
finally:
    estado_luces["corriendo"] = False
    frenar()
