import json
import serial
import time
from bitalino import BITalino

device = BITalino("/dev/rfcomm0")
device.start(1, [1])
sensor_id = "ECG"

arduino_port = "/dev/ttyS0"
baudrate = 9600

arduino = serial.Serial(arduino_port, baudrate, timeout=1)

while True:
  print('Press Cntrl+C to stop sending...')
  data = device.read(1)
  analog = [row[5:] for row in data]

  sample = {
            "timestamp": time.time(), 
            "sensor": sensor_id,
            "analog": int(analog[0][0]),
        }

  json_data = json.dumps(sample)
  print("sending: " + str(json_data))
  arduino.write((json_data).encode("utf-8")) 
  
  time.sleep(30)
  
  
device.stop()
device.close()

