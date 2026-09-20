# This code shows the colours of the sky/sun in day on a single NeoPixel.
# The variations of daylight are represented by changing colours
# and brightness levels. The code cycles through the different times of day,
# fading between colours to simulate the changing light conditions.
import time
import board
import neopixel

pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel.brightness = 1.0

ROOM_BRIGHTNESS = 0.5  # Adjust this value to change the overall brightness of the pixel

# The colours of the day
NIGHT = (10, 10, 10)
FIRST_LIGHT = (60, 40, 60)
GOLD = (255, 150, 40)
PALE_GOLD = (255, 205, 120)
WHITE = (255, 255, 250)
WARM = (255, 215, 130)
DEEP_GOLD = (255, 140, 35)
RED = (255, 55, 15)
PURPLE = (100, 35, 100)


# --- Show, Hold and Fade --------------------------------------


def show(color, brightness):
    """Light the pixel with one colour at one brightness."""
    level = brightness * ROOM_BRIGHTNESS
    red = int(color[0] * level)
    green = int(color[1] * level)
    blue = int(color[2] * level)
    pixel.fill((red, green, blue))


def hold(color, brightness, seconds):
    """Stay on one colour without changing."""
    show(color, brightness)
    time.sleep(seconds)


def fade(from_color, from_bright, to_color, to_bright, seconds):
    """Change colour and brightness together from one to the next."""
    steps = int(seconds * 50)
    for i in range(steps):
        amount = i / steps
        red = from_color[0] + (to_color[0] - from_color[0]) * amount
        green = from_color[1] + (to_color[1] - from_color[1]) * amount
        blue = from_color[2] + (to_color[2] - from_color[2]) * amount
        brightness = from_bright + (to_bright - from_bright) * amount
        show((red, green, blue), brightness)
        time.sleep(seconds / steps)


# --- Times of the Day -----------------------------------------


def before_dawn():
    print("Before dawn")
    hold(NIGHT, 0.0, 4)


def first_light():
    print("First light")
    fade(NIGHT, 0.0, FIRST_LIGHT, 0.12, 3)


def golden_morning():
    print("Golden morning")
    fade(FIRST_LIGHT, 0.12, GOLD, 0.45, 3)


def late_morning():
    print("Late morning")
    fade(GOLD, 0.45, PALE_GOLD, 0.75, 2)


def noon():
    print("Noon")
    fade(PALE_GOLD, 0.75, WHITE, 1.0, 3)
    hold(WHITE, 1.0, 1)


def afternoon():
    print("Afternoon")
    fade(WHITE, 1.0, WARM, 0.8, 2)


def early_evening():
    print("Early evening")
    fade(WARM, 0.8, DEEP_GOLD, 0.5, 3)


def golden_evening():
    print("Golden evening")
    fade(DEEP_GOLD, 0.5, RED, 0.28, 2)


def early_night():
    print("Early night")
    fade(RED, 0.28, PURPLE, 0.1, 3)


def night():
    print("Night")
    fade(PURPLE, 0.1, NIGHT, 0.0, 3)
    hold(NIGHT, 0.0, 3)


# --- run the day, over and over -------------------------------------------

while True:
    before_dawn()
    first_light()
    golden_morning()
    late_morning()
    noon()
    afternoon()
    early_evening()
    golden_evening()
    early_night()
    night()