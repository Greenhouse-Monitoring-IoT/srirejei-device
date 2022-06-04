#Import Library
from machine import ADC, Pin, SoftI2C
from umqttsimple import MQTTClient
import wifimgr
import time
import ubinascii
import machine
import micropython
import network
import esp
import dht
import gc
from lcd_api import LcdApi
from i2c_lcd import I2cLcd
from time import sleep
try:
  import usocket as socket
except:
  import socket

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

#LED
r_led = Pin(33, Pin.OUT)
g_led = Pin(4, Pin.OUT)
#LDR Sensor
ldr = LDR(34)
#DHT Sensor
DHT = dht.DHT22(Pin(14))
#Moisture sensor
mspin = ADC(Pin(32))
mspin.atten(ADC.ATTN_11DB)
#Water Level Sensor
wls = ADC(Pin(35))
wls.atten(ADC.ATTN_11DB)
#LCD Configuration
I2C_ADDR = 0x27
rows = 2
columns = 16
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=10000)
lcd = I2cLcd(i2c, I2C_ADDR, rows, columns)

class LDR:
    def __init__(self, pin, min_value=0, max_value=100):
        if min_value >= max_value:
            raise Exception('Min value is greater or equal to max value')

        # initialize ADC (analog to digital conversion)
        self.adc = ADC(Pin(pin))

        # set 11dB input attenuation (voltage range roughly 0.0v - 3.6v)
        self.adc.atten(ADC.ATTN_11DB)

        self.min_value = min_value
        self.max_value = max_value

    def read(self):
        return self.adc.read()

    def value(self):
        return (self.max_value - self.min_value) * self.read() / 4095

esp.osdebug(None)
gc.collect()

wlan = wifimgr.get_connection()

if wlan is None:
  print("Tidak dapat melakukan konfigurasi Wi-Fi")
  while True:
    pass

print("Proses Lanjut")

mqtt_server = '20.124.124.81'

client_id = ubinascii.hexlify(machine.unique_id())

last_message = 0
message_interval = 5

def ldr_condition(val):
    print(val)
    if val < 50:
        r_led.value(1)
    else:
        r_led.value(0)
        
def temp_condition(temperature):    
    if int(temperature) > 25 and int(temperature) < 32:
        g_led.value(1)
    else:
        g_led.value(0)
        
def printMonitoring(temp, hum, light, mois, water):
    temp_condition(temp)
    lcd.clear()
    lcd.putstr("Suhu : " + str(temp, 'utf-8') + '    ')
    lcd.putstr("Klmb : " + str(hum, 'utf-8')+ '')
    time.sleep(0.5)
    lcd.clear()
    lcd.putstr("Chy : " + str(light, 'utf-8') + '    ')
    lcd.putstr("Tnh : " + str(mois, 'utf-8')+ '')
    time.sleep(0.5)
    lcd.clear()
    lcd.putstr("Water : " + str(water, 'utf-8') + '')

def moisture_smooth_reading():
    avg = 0
    count = 100
    for i in range(count):
        avg += mspin.read()
    avg /= count
    return(avg)
    
def water_smooth_reading():
    avg = 0
    count = 100
    for i in range(count):
        avg += wls.read()
    avg /= count
    return(avg)

def connect_mqtt():
  global client_id, mqtt_server
  client = MQTTClient(client_id, mqtt_server)
  client.connect()
  print('Terhubung ke %s MQTT broker' % (mqtt_server))
  return client

def restart_and_reconnect():
  print('Gagal menghubungkan ke MQTT broker. Menghubungkan ulang...')
  time.sleep(10)
  machine.reset()

#Fungsi Callback
def sub_cb(topic, msg):
  print((topic, msg))
  if (topic == topic_sub_lamp or topic == topic_sub_pump) and msg == b'received':
    print('ESP menerima pesan')

def read_sensor():
  try:
    DHT.measure()
    temp = DHT.temperature()
    hum = DHT.humidity()
    light = ldr.value()
    moisture_analog = moisture_smooth_reading() - 450
    moisture = ((int(moisture_analog)/1023) * 100)-100
    sum = 0
    water_read = 0
    water = 0
    wtr_sum = 0
    for i in range(10):
      water_read = water_smooth_reading()
      wtr_sum = wtr_sum + water_read
    water = ((wtr_sum/10) - 900)*0.0065
    if (isinstance(temp, float) and isinstance(hum, float) and isinstance(light, float) and isinstance(moisture, float) and isinstance(water, float)) or (isinstance(temp, int) and isinstance(hum, int) and isinstance(light, int) and isinstance(moisture, int) and isinstance(water, int)):
      temp = (b'{0:3.1f}'.format(temp))
      hum =  (b'{0:3.1f}'.format(hum))
      light = (b'{0:3.1f}'.format(light))
      moisture = (b'{0:3.1f}'.format(moisture))
      water = (b'{0:3.1f}'.format(water))
      return temp, hum, light, moisture, water
      #return temp, hum
    else:
      return('Pembacaan Sensor Tidak Valid')
  except OSError as e:
    return('Gagal Membaca Sensor')

#Fungsi Publish
def do_publish(arg1, arg2, arg3, arg4, arg5):
  #Topic Publish
  topic_pub_light = b'srirejeki/client/'+ client_id +'/light'
  topic_pub_temp = b'srirejeki/client/'+ client_id +'/temperature'
  topic_pub_hum = b'srirejeki/client/'+ client_id +'/humidity'
  topic_pub_mois = b'srirejeki/client/'+ client_id +'/moisture'
  topic_pub_water = b'srirejeki/client/'+ client_id +'/water'
  #Mulai publish
  client.publish(topic_pub_temp, arg1)
  client.publish(topic_pub_hum, arg2)
  client.publish(topic_pub_light, arg3)
  client.publish(topic_pub_mois, arg4)
  client.publish(topic_pub_water, arg5)

#Fungsi Subscribe
def do_subscribe():
  #Topic Subscribe
  topic_sub_pump = b'srirejeki/server/'+ client_id +'/pump'
  topic_sub_lamp = b'srirejeki/server/'+ client_id +'/lamp'
  client.set_callback(sub_cb)
  #Mulai subscribe
  client.subscribe(topic_sub_pump)
  client.subscribe(topic_sub_lamp)
  return client
 
sleep(1)    
lcd.putstr("Sedang melakukan konfigurasi")
sleep(1)

#Menghubungkan ke MQTT
try:
  client = connect_mqtt()
  
except OSError as e:
  print(e)
  print('Terjadi kesalahan, memuat ulang')
  lcd.clear()
  lcd.putstr("Sistem Dimuat Ulang")
  restart_and_reconnect()
  
except Exception as err:
  print(err)
  print('Terjadi kesalahan, memuat ulang')
  lcd.clear()
  lcd.putstr("Sistem Dimuat Ulang")
  restart_and_reconnect()
lcd.clear()
sleep(1)    
lcd.putstr("Selamat Datang")
sleep(1)    
lcd.clear()
count = 0
while True:
  #temp, hum, light, mois, water, = 0, 0, 0, 0, 0
  try:
    #lcd.clear()
    #lcd.putstr("Alat Sedang     Bekerja")
    #temp_condition(float(DHT.temperature())
    #ldr_condition(float(ldr.value())
    temp, hum, light, mois, water = read_sensor()
    
    #Mulai publish
    try:
      do_publish(temp, hum, light, mois, water)
      print("Mengirim")
      print(temp)
      print(hum)
      print(light)
      print(mois)
      print(water)
      print(count)
    except Exception as err:
      print("Gagal melakukan pengiriman data")
      print(err)
      lcd.clear()
      lcd.putstr("Sistem Dimuat Ulang")
      restart_and_reconnect()
      
    #Mulai subscribe
    try:
      print("Menerima")
      #do_subscribe()
    except Exception as err:
      print("Gagal melakukan penerimaan data")
      print(err)
      lcd.clear()
      lcd.putstr("Sistem Dimuat Ulang")
      restart_and_reconnect()
      
    #To Screen
    try:
      if(count % 5 == 0):
        lcd.clear()
        lcd.putstr("Suhu : " + str(temp, 'utf-8') + ' C  ')
        lcd.putstr("Klmb : " + str(hum, 'utf-8') + '%')
        time.sleep(0.5)
        lcd.clear()
        lcd.putstr("Chy : " + str(light, 'utf-8') + ' Lux ')
        lcd.putstr("Tnh : " + str(mois, 'utf-8') + '%')
        lcd.clear()
        time.sleep(0.5)
        lcd.clear()
        lcd.putstr("Water : " + str(water, 'utf-8') + " cm")
        time.sleep(0.5)
    except Exception as e:
      print(e)
      
  except OSError as e:
    print(e)
    print('Terjadi kesalahan, memuat ulang')
    lcd.clear()
    lcd.putstr("Sistem Dimuat Ulang")
    restart_and_reconnect()

  except Exception as err:
    print(err)
    print('Terjadi kesalahan, memuat ulang')
    lcd.clear()
    lcd.putstr("Sistem Dimuat Ulang")
    restart_and_reconnect()
  count+=1
  if count == 100:
    count = 0
    
  if(count % 5 != 0):
    time.sleep(1)
  else:
    time.sleep(0.5)
