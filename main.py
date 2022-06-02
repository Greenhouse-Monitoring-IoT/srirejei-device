from machine import Pin, ADC, SoftI2C
from time import sleep
from lcd_api import LcdApi
from i2c_lcd import I2cLcd
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

I2C_ADDR = 0x27
rows = 2
columns = 16
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=10000)
lcd = I2cLcd(i2c, I2C_ADDR, rows, columns)

def ldr_condition(val):
    try:
        if val > 30 and val < 100:
            r_led.value(1)
        else:
            r_led.value(0)
    except:
        print("Sensor LDR bermasalah")

def temp_codition(temperature):
    try:
        if temperature > 25 and temperature < 32:
            g_led.value(1)
        else:
            g_led.value(0)
    except:
        print('Sensor DHT bermasalah!')

def printMonitoring(tempt, tempt_f, humi, ldrVal):
    print(f'Temperature: {tempt:.2f} C | {tempt_f:.2f} F')
    lcd.putstr(f"Temperature: str({tempt:.2f}) C | str({tempt_f:.2f}) F")
    sleep(3)
    lcd.clear()
    
    print(f'Humidity: {humi:.2%}')
    lcd.putstr(f"Humidity: str({humi:.2%})")
    sleep(3)
    lcd.clear()
    
    print(f'LDR Value: {ldrVal}')
    lcd.putstr(f"LDR Value: str({ldrVal})")
    sleep(3)
    lcd.clear()

while True:    
    sleep(2)
    lcd.putstr("Selamat Datang!        Menginisialisasi...")
    sleep(3)
    lcd.clear()
    try:        
        DHT.measure()
        temp = DHT.temperature()
        hum = DHT.humidity()
        temp_f = temp * (9/5) + 32.0
        ldr_value = ldr.value()
                
        printMonitoring(temp, temp_f, hum, ldr_value)
        ldr_condition(ldr_value)
        temp_condition(temp)
        
    except DeviceError as e:
        print('Gagal untuk memuat alat, silakan muat ulang!')