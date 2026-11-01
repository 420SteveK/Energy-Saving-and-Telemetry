from machine import Pin, ADC
import time

DATA = Pin (14, Pin.OUT)
CLK = Pin (15, Pin.OUT)
sensor = ADC (Pin(26))

leds = 0
umbral = 15000

def actualizar ():
    for i in range (7, -1, -1):
        DATA.value((leds >> i) & 1)
        CLK.value(1)
        CLK.value(0)

def set_led(n, estado):
    global leds
    if estado:
        leds |= (1 << n)
    else:
        leds &= ~(1<<n)
    print (leds)
    actualizar()

estado_anterior = None 

while True:
    valor = sensor.read_u16()
    print (valor)
    oscuro = valor < umbral
    if oscuro != estado_anterior:
        set_led (0, oscuro)
        set_led (1, oscuro)
        estado_anterior = oscuro
    time.sleep(0.5)