import time
import subprocess
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import Adafruit_DHT
from datetime import datetime
from influxdb import InfluxDBClient

sensor = Adafruit_DHT.DHT22
pin = '4'

i2c = busio.I2C(board.SCL, board.SDA)

disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

disp.fill(0)
disp.show()

width = disp.width
height = disp.height
image = Image.new("1", (width, height))

draw = ImageDraw.Draw(image)

draw.rectangle((0, 0, width, height), outline=0, fill=0)

padding = -2
top = padding
bottom = height - padding
x = 0

# Load default font.
font = ImageFont.load_default()

env_header_str = "TEMP F  TEMP C  RH  %"
line = "======================"


# Setup Database

ifclient = InfluxDBClient(database="oven_temp", host="influxdb")

print("Create database: oven_temp")
ifclient.create_database("oven_temp")

print("Create a retention policy")
ifclient.create_retention_policy('two_hours', '2h', 1, default=True)
ifclient.create_retention_policy('a_year', '52w', 1, default=False)
select_clause = 'SELECT mean("temperature") AS "mean_temperature",mean("humidity") AS "mean_humidity" INTO "a_year"."downsampled_environment" FROM "environment" GROUP BY time(30m)'
ifclient.create_continuous_query('cq_30m', select_clause)

while True:
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # IP
    ip_cmd = "hostname -I | cut -d' ' -f1"
    ip_str = "IP:   {}".format(subprocess.check_output(
        ip_cmd, shell=True).decode("utf-8"))

    # TIME
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    time_str = "TIME: {}".format(current_time)

    # ENV DATA
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    if humidity is not None and temperature is not None:
        env_values_str = "{:.1f} F  {:.1f} C  {:.1f}%".format(
            temperature * (9 / 5) + 32, temperature
            , humidity)
        # INFLUXDB
        body = [
            {
                "measurement": "environment",
                "time": datetime.utcnow(),
                "fields": {
                    "temperature": temperature,
                    "humidity": humidity
                }
            }
        ]
        ifclient = InfluxDBClient(database="oven_temp", host="influxdb")
        ifclient.write_points(body)
    else:
        env_values_str = "ERROR   ERROR   ERROR"

    # OLED
    draw.text((x, top + 0), env_header_str, font=font, fill=255)
    draw.text((x, top + 8), env_values_str, font=font, fill=255)
    draw.text((x, top + 32), line, font=font, fill=255)
    draw.text((x, top + 40), ip_str, font=font, fill=255)
    draw.text((x, top + 48), time_str, font=font, fill=255)
    draw.text((x, top + 56), line, font=font, fill=255)
    disp.image(image)
    disp.show()

    # SLEEP
    time.sleep(5)
