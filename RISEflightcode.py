import pandas as pd 
import board 
import busio 
import adafruit_bmp3xx 
import adafruit_lsm303_accel 
import adafruit_lsm303dlh_mag 
import time 
from picamera import PiCamera 

i2c = busio.I2C(board.SCL, board.SDA) 
bmp = adafruit_bmp3xx.BMP3XX_I2C(i2c) 
mag = adafruit_lsm303dlh_mag.LSM303DLH_Mag(i2c) 
accel = adafruit_lsm303_accel.LSM303_Accel(i2c) 

#establish initial dataframe with desired columns 
df = pd.DataFrame(columns = ['Time', 'Temp', 'Pressure', 'Accel X', 'Accel Y', 'Accel Z', 'Mag X', 'Mag Y', 'Mag Z']) 

#record initial time 
start = time.time() 
#and turn on the camera 
camera = PiCamera() 
camera.start_recording('/home/pi/Desktop/test_video.h264') 

#define variable to increment time 
elapsed = time.time() - start

#and a built-in delay, in seconds, if there is a lag before launch 
delay = 10 #change the value if a delay time is desired 

print('Now') 

#set how long to collect data, in seconds, after the delay 
while elapsed < delay + 10: 
    #update the time 
    elapsed = time.time() - start 
     
    #skip everything else, if we're still in the delay period 
    if elapsed < delay: 
        continue 
         
    #otherwise append data to the dataframe 
    df = df.append({ 'Time':elapsed, 'Temp':bmp.temperature, 'Pressure':bmp.pressure, 
                    'Accel X':accel.acceleration[0], 
                    'Accel Y':accel.acceleration[1], 
                    'Accel Z':accel.acceleration[2], 
                    'Mag X':mag.magnetic[0], 
                    'Mag Y':mag.magnetic[1], 
                    'Mag Z':mag.magnetic[2]} , ignore_index = True) 
                        
#write to a csv file, limiting the number of decimals 
df.to_csv('/home/pi/Desktop/test_csv', float_format='%.3f') 

#turn off the camera 
camera.stop_recording() 

print(bmp.temperature) 

#track the total time for the whole script 
elapsed = time.time()-start 
print(elapsed) 