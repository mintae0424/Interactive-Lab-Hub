import time
from datetime import datetime
import pytz
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
from pyowm.owm import OWM
import requests
import json


# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True
buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input()
buttonB.switch_to_input()

API_KEY = '606c32357a961d745bf0477313a08789'
URL = 'http://api.openweathermap.org/data/2.5/weather?q='
ICON_URL = ' http://openweathermap.org/img/wn/'
owm = OWM(API_KEY)
mgr = owm.weather_manager()

weathers = ['Sunny', 'Rainy', 'Cloudy']
tz = pytz.timezone('America/New_York')
current_tz = "New York"
current_units = 'imperial'

r = requests.get('{}{}&APPID={}&units={}'.format(URL, current_tz, API_KEY, current_units))

# weather = mgr.weather_at_place(current_tz).weather

weather = r.json()

update = False
metric = False

while True:
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    if buttonB.value and not buttonA.value:
        current_units = 'imperial' if current_units == 'metric' else 'metric'
        update = True

    if buttonA.value and not buttonB.value:
        if current_tz == "Seoul":
            current_tz = "New York"
            tz = pytz.timezone('America/New_York')
            
            update = True
        else:
            current_tz = "Seoul"
            tz = pytz.timezone("Asia/Seoul")
            update = True

    if update:
        r = requests.get('{}{}&APPID={}&units={}'.format(URL, current_tz, API_KEY, current_units))
        weather = r.json()
        update = False

    #TODO: fill in here. You should be able to look in cli_clock.py and stats.py 
    current_time = datetime.now(tz)
    t = current_time.strftime("%m/%d/%Y %H:%M:%S")
    h = int(current_time.strftime("%H"))

    icon = weather['weather'][0]['icon']
    weather_detail = weather['weather'][0]['description'].title()
    temp = round(weather['main']['temp'])
    temp_text = '{} F'.format(temp) if current_units == 'imperial' else '{} C'.format(temp)
    image_url = '{}{}.png'.format(ICON_URL, icon)
    image = Image.open(requests.get(image_url, stream=True).raw)

    # if current_weather == 'Rainy':
    #     image = Image.open('rain.png')
    #     background = Image.new("RGB", (width, height), (74, 101, 131))


    # if current_weather == 'Cloudy':
    #     image = Image.open('cloud.png')
    #     background = Image.new("RGB", (width, height), (119, 150, 158))

    # if current_weather == 'Sunny':
    
    if icon[-1] == 'n':
        # image = Image.open("moon.png")
        background = Image.new("RGB", (width, height), (43, 47, 119))
        fill_color = "#ffffff"

    else:
        # image = Image.open("sun.png")
        background = Image.new("RGB", (width, height), (255, 252, 177))
        fill_color = "#000000"

    y = top

    image_ratio = image.width / image.height
    screen_ratio = width / height

    if screen_ratio < image_ratio:
        scaled_width = image.width * height // image.height
        scaled_height = height
    else:
        scaled_width = width
        scaled_height = image.height * width // image.width

    image = image.resize((scaled_width, scaled_height), Image.BICUBIC)

    i_x = scaled_width // 2 - width // 2
    i_y = scaled_height // 2 - height // 2

    image = image.crop((i_x, i_y, i_x + width, i_y + height))

    background.paste(image, mask = image.split()[3])

    img_draw = ImageDraw.Draw(background)
    img_draw.text((x, y), current_tz, font=font, fill=fill_color)
    y += font.getsize(current_tz)[1]
    img_draw.text((x, y), weather_detail, font=font, fill=fill_color)
    y += font.getsize(weather_detail)[1]
    img_draw.text((x, y), temp_text, font=font, fill=fill_color)
    y += font.getsize(temp_text)[1]
    img_draw.text((x, y), t, font=font, fill=fill_color)

    # Display image.
    disp.image(background, rotation)
    time.sleep(1)
