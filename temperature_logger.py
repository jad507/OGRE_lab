
import time
import csv
import os
from datetime import datetime
from smbus2 import SMBus
import bme280
import adafruit_bmp3xx

# Configuration
LOG_INTERVAL_SECONDS = 1  # Change to 1 for per-second logging
HOURLY_STATUS_INTERVAL = 10  # Seconds in an hour
TEMP_THRESHOLD = 50.0  # Optional alert threshold (disabled by default)
ENABLE_ALERTS = False
ENABLE_AUTOSTART = False
LOG_FILE = "temperature_log.csv"

# Initialize sensor
port = 1
address = 0x77
bus = SMBus(port)
calibration_params = bme280.load_calibration_params(bus, address)

# Create log file with header if it doesn't exist
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Temperature_C"])

# Main loop
last_status_time = time.time()
print("Temperature logging started...")

try:
    while True:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = bme280.sample(bus, address, calibration_params)
        temperature = round(data.temperature, 2)

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
