# -*- coding: utf-8 -*-
import time
import board
import busio
import adafruit_veml7700
import paho.mqtt.client as mqtt
import smbus
import RPi.GPIO as GPIO
import statistics
from smbus2 import SMBus

# Configuration MQTT
BROKER = "localhost"
client = mqtt.Client()
client.connect(BROKER)

# Initialisation I2C pour le LCD
I2C_BUS = SMBus(1)
LCD_ADDR = 0x3e
RGB_ADDR = 0x62

# Initialisation I2C pour les capteurs
i2c = busio.I2C(board.SCL, board.SDA)
veml7700 = adafruit_veml7700.VEML7700(i2c)
HTU21D_I2C_ADDRESS = 0x40
TRIGGER_TEMP_MEASURE_HOLD = 0xE3
TRIGGER_HUMD_MEASURE_HOLD = 0xE5
ADS1115_I2C_ADDR = 0x48
CONFIG_REG = [0xF3, 0x83]

# Configuration du capteur ultrason
GPIO.setmode(GPIO.BCM)
GPIO_TRIGGER = 23
GPIO_ECHO = 24
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

# Configuration du ventilateur
FAN_PIN = 19
GPIO.setup(FAN_PIN, GPIO.OUT)
pwm = GPIO.PWM(FAN_PIN, 100)
pwm.start(0)

# Fonctions LCD
def lcd_command(cmd):
    I2C_BUS.write_byte_data(LCD_ADDR, 0x80, cmd)
    time.sleep(0.05)

def lcd_write(msg):
    lcd_command(0x01)  # Effacer l'écran
    time.sleep(0.05)
    for char in msg:
        I2C_BUS.write_byte_data(LCD_ADDR, 0x40, ord(char))
        time.sleep(0.05)

def set_rgb(r, g, b):
    I2C_BUS.write_byte_data(RGB_ADDR, 0, 0)
    I2C_BUS.write_byte_data(RGB_ADDR, 1, 0)
    I2C_BUS.write_byte_data(RGB_ADDR, 0x08, 0xaa)
    I2C_BUS.write_byte_data(RGB_ADDR, 4, r)
    I2C_BUS.write_byte_data(RGB_ADDR, 3, g)
    I2C_BUS.write_byte_data(RGB_ADDR, 2, b)

# Fonctions de lecture des capteurs
def read_light():
    return round(veml7700.lux, 2)

def read_noise():
    try:
        I2C_BUS.write_i2c_block_data(ADS1115_I2C_ADDR, 0x01, CONFIG_REG)
        time.sleep(0.1)
        data = I2C_BUS.read_i2c_block_data(ADS1115_I2C_ADDR, 0x00, 2)
        valeur_brute = (data[0] << 8) | data[1]
        if valeur_brute > 32767:
            valeur_brute -= 65536
        tension = (valeur_brute * 4.096) / 32767.0
        return round(tension, 3)
    except OSError:
        return None

def read_distance():
    GPIO.output(GPIO_TRIGGER, False)
    time.sleep(0.1)
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
    
    debut_pulse, fin_pulse = time.time(), time.time()
    while GPIO.input(GPIO_ECHO) == 0:
        debut_pulse = time.time()
    while GPIO.input(GPIO_ECHO) == 1:
        fin_pulse = time.time()

    distance = (fin_pulse - debut_pulse) * 17150
    return round(distance, 2)

def read_temperature():
    data = I2C_BUS.read_i2c_block_data(HTU21D_I2C_ADDRESS, TRIGGER_TEMP_MEASURE_HOLD, 3)
    raw_temp = (data[0] << 8) | data[1]
    return round(-46.85 + (175.72 * raw_temp / 65536.0), 2)

def read_humidity():
    data = I2C_BUS.read_i2c_block_data(HTU21D_I2C_ADDRESS, TRIGGER_HUMD_MEASURE_HOLD, 3)
    raw_humidity = (data[0] << 8) | data[1]
    return round(-6.0 + (125.0 * raw_humidity / 65536.0), 2)

# Gestion du ventilateur via MQTT
def on_message(client, userdata, msg):
    global pwm
    print(f"Message recu : {msg.topic} -> {msg.payload.decode()}")
    
    if msg.topic == "home/fan":
        if msg.payload.decode() == "niv1":
            pwm.ChangeDutyCycle(40)
        elif msg.payload.decode() == "niv2":
            pwm.ChangeDutyCycle(70)
        elif msg.payload.decode() == "niv3":
            pwm.ChangeDutyCycle(100)
        else:
            pwm.ChangeDutyCycle(0)

client.on_message = on_message
client.subscribe("home/fan")
client.loop_start()

try:
    while True:
        temperature = read_temperature()
        humidity = read_humidity()
        luminosite = read_light()
        bruit = read_noise()
        distance = read_distance()

        if distance < 20:
            mouvement = "Tranquille"
        elif distance < 50:
            mouvement = "Mouvemente"
        else:
            mouvement = "Agite"

        print(f"Temp: {temperature}C, Humidite: {humidity}%, Luminosite: {luminosite} lux, Bruit: {bruit}V, Mouvement: {mouvement}")

        client.publish("home/temperature", temperature)
        client.publish("home/humidity", humidity)
        client.publish("home/light", luminosite)
        client.publish("home/noise", bruit)
        client.publish("home/movement", mouvement)

        # Mise a jour du LCD
        lcd_write(f"Temp:{temperature}C  Hum:{humidity}%")
        time.sleep(1)
        lcd_write(f"Lumi:{luminosite}lux")
        if luminosite < 10:
            set_rgb(0, 0, 255)
        elif luminosite < 100:
            set_rgb(255, 165, 0)
        else:
            set_rgb(255, 255, 0)

        time.sleep(1)

except KeyboardInterrupt:
    print("Arret du programme")
    pwm.stop()
    GPIO.cleanup()
