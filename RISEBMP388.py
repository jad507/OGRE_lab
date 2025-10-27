import board
import busio
import adafruit_bmp3xx
import digitalio
from time import sleep

i2c = busio.I2C(board.SCL, board.SDA)

bmp = adafruit_bmp3xx.BMP3XX_I2C(i2c)

print("Pressure: { :6.1f} ".format(bmp.pressure))

for i in range(20):
    print("Temperature: { :5.2f} ".format(bmp.temperature))
    sleep(1)