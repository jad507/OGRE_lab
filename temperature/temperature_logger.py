"""
This script is a Temperature Logger for the Reverse Telescope system in the OGRE Lab, meant to help diagnose drift and
defocus errors at long time-frames (errors across hours/days) that we believed may be due to the building's HVAC.
Those errors have an unknown relationship (and might be totally independent of) vibrations experienced at short time-frames
(15 hz to 1 hz) that we were addressing through standard vibration mitigation bladders and rubber pads.

This temperature logger was meant to run on a Raspberry Pi and BMP388 temperature/pressure sensor, both orginally meant
for use in the Rockets for Inclusive Science Education (RISE) program as an altimeter and video data collector.

The BMP388 communicates over I2C, with temperature accuracy of +/- 0.5 degrees C.
The product page is https://www.adafruit.com/product/3966
The sample code is available at https://learn.adafruit.com/adafruit-bmp388-bmp390-bmp3xx/python-circuitpython which
also lists instructions on how to install the libraries we use.
Other RISE examples are included in this /temperature/ folder.
uses adafruit libraries:
    pip install adafruit-circuitpython-bme280 adafruit-circuitpython-bmp3xx
"""
import time
import csv
import os
from datetime import datetime
from smbus2 import SMBus
import bme280
import adafruit_bmp3xx
import board
import busio
import digitalio

# Temperature Logger using the Raspberry Pi and BMP388 temperature/pressure sensor

# Configuration
LOG_INTERVAL_SECONDS = 1  # Change to 1 for per-second logging
HOURLY_STATUS_INTERVAL = 3600  # Seconds in an hour
TEMP_THRESHOLD = 50.0  # Optional alert threshold (disabled by default)
ENABLE_ALERTS = False
ENABLE_AUTOSTART = False
LOG_FILE = "temperature_log.csv"

# Initialize sensor
port = 1
address = 0x77
# bus = SMBus(port)
# calibration_params = bme280.load_calibration_params(bus, address)
i2c = busio.I2C(board.SCL, board.SDA) 
bmp = adafruit_bmp3xx.BMP3XX_I2C(i2c) 

# Create log file with header if it doesn't exist
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Temperature_C"])

# Main loop
last_status_time = time.time()
start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
start_temperature = round(bmp.temperature, 2)
print(f"Temperature logging started @ {start_time}: Current Temperature = {start_temperature}°C")

try:
    while True:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # data = bme280.sample(bus, address, calibration_params)
        temperature = round(bmp.temperature, 2)

        # Log to CSV
        with open(LOG_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([current_time, temperature])

        # Optional alert
        if ENABLE_ALERTS and temperature > TEMP_THRESHOLD:
            print(f"ALERT: Temperature exceeded threshold at {current_time}: {temperature}°C")

        # Hourly status output
        if time.time() - last_status_time >= HOURLY_STATUS_INTERVAL:
            print(f"Status Update @ {current_time}: Current Temperature = {temperature}°C")
            last_status_time = time.time()

        time.sleep(LOG_INTERVAL_SECONDS)

except KeyboardInterrupt:
    print("Temperature logging stopped by user.")
