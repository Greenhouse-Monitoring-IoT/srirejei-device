from machine import Pin, ADC
from time import sleep
import dht

class LDR:    
    def __init__(self, pin, min_value=0, max_value=100):        
        if min_value >= max_value:
            raise Exception('Nilai minimum lebih besar atau sama dengan nilai maksimum, atur ulang!')

        self.adc = ADC(Pin(pin))
        
        self.adc.atten(ADC.ATTN_11DB)

        self.min_value = min_value
        self.max_value = max_value

    def read(self):        
        return self.adc.read()

    def value(self):        
        return (self.max_value - self.min_value) * self.read() / 4095


ldr = LDR(34)
r_led = Pin(33, Pin.OUT)
g_led = Pin(32, Pin.OUT)
DHT = dht.DHT22(Pin(14))

while True:
    ldr_value = ldr.value()
    print('value = {}'.format(ldr_value))
    sleep(1)
    
    
    
    if ldr_value > 30 and ldr_value < 100:
        r_led.value(1)
    else:
        r_led.value(0)
        
    try:
        sleep(2)
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()
        temp_f = temp * (9/5) + 32.0
        ldr_value = ldr.value()
        print(f'Temperature: {temp} C or {temp} F')
        print(f'Humidity: {hum}')
        print(f'LDR Value: {ldr_value}')
        
    except OSError as e:
        print('Gagal untuk memuat alat, silakan muat ulang!')