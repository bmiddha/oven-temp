FROM arm32v7/python:3-buster


RUN pip3 install --no-cache-dir rpi.gpio influxdb adafruit-circuitpython-ssd1306 Pillow Adafruit_DHT 

COPY oven_temp.py ./

CMD ["python3", "./oven_temp.py"]
