from machine import  ADC, Pin
import time 

sensor = ADC (Pin(26))
led = Pin (16, Pin.OUT)

umbral = 4000


while True:
    valor = sensor.read_u16()
    print (valor)
    if valor < umbral:
        led.value(1)
    else:
        led.value(0)
    time.sleep(0.5)