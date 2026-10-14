import time
import math
import board
import digitalio
import pwmio
import audiobusio
import audiomp3
import audiomixer
import neopixel
from analogio import AnalogIn
from adafruit_motor import servo

print("Loading Midterm: Flying Eagle v4")

# ── EXTERNAL POWER ──
external_power = digitalio.DigitalInOut(board.EXTERNAL_POWER)
external_power.direction = digitalio.Direction.OUTPUT
external_power.value = True
time.sleep(0.2)

# ── SENSORS ──
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

potentiometer = AnalogIn(board.A1)
light_sensor  = AnalogIn(board.A3)

# ── SERVO ──
pwm = pwmio.PWMOut(board.EXTERNAL_SERVO, duty_cycle=0, frequency=50)
my_servo = servo.Servo(pwm, min_pulse=500, max_pulse=2500)

FLAP_MIN   = 0
FLAP_MAX   = 180
FLAP_STEP  = 8

# Flap Speed
FLAP_DELAY_FAST = 0.015   # At max pot
FLAP_DELAY_SLOW = 0.07    # At min pot 

# ── NEOPIXEL RING ──
NUM_PIXELS = 12
pixels = neopixel.NeoPixel(
    board.EXTERNAL_NEOPIXELS,
    NUM_PIXELS,
    brightness=0.4,
    auto_write=False
)


light_raw_min = light_sensor.value
light_raw_max = light_raw_min + 1
CALIBRATION_PAD = 200

def read_light_mix():
    global light_raw_min, light_raw_max
    raw = light_sensor.value
    if raw < light_raw_min:
        light_raw_min = raw
    if raw > light_raw_max:
        light_raw_max = raw
    span = (light_raw_max + CALIBRATION_PAD) - (light_raw_min - CALIBRATION_PAD)
    if span <= 0:
        return 0.5
    mix = (raw - (light_raw_min - CALIBRATION_PAD)) / span
    return max(0.0, min(1.0, mix))


# ══════════════════════════════════════════════════════
#  COLOR HELPERS
# ══════════════════════════════════════════════════════
def hsv_to_rgb(h, s, v):
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if   h < 60:  r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


# ══════════════════════════════════════════════════════
#  EYE ANIMATION
# ══════════════════════════════════════════════════════
ORBIT_SPEED = 0.25
HUE_SPEED   = 30

DAY_HUE_CENTER   = 45
DAY_HUE_SWING    = 120
NIGHT_HUE_CENTER = 10
NIGHT_HUE_SWING  = 40

EYE_WIDTH = 2.5

BLINK_INTERVAL = 3.5
BLINK_DURATION = 0.12
last_blink_time = time.monotonic()
is_blinking = False
blink_start  = 0.0


def draw_eyes(t, light_mix, flap_pulse, blinking):
    if blinking:
        pixels.fill((0, 0, 0))
        pixels.show()
        return

    day_hue   = DAY_HUE_CENTER   + math.sin(t * HUE_SPEED * 0.02) * DAY_HUE_SWING
    night_hue = NIGHT_HUE_CENTER + math.sin(t * HUE_SPEED * 0.015) * NIGHT_HUE_SWING
    hue = night_hue + (day_hue - night_hue) * light_mix

    day_sat, day_val     = 0.5, 1.0
    night_sat, night_val = 1.0, 0.9
    sat = night_sat + (day_sat - night_sat) * light_mix
    val = night_val + (day_val - night_val) * light_mix

    eye1_pos = (t * ORBIT_SPEED * NUM_PIXELS) % NUM_PIXELS
    eye2_pos = (eye1_pos + NUM_PIXELS / 2) % NUM_PIXELS

    for i in range(NUM_PIXELS):
        d1 = min(abs(i - eye1_pos), NUM_PIXELS - abs(i - eye1_pos))
        d2 = min(abs(i - eye2_pos), NUM_PIXELS - abs(i - eye2_pos))
        d  = min(d1, d2)

        if d < 0.5:
            brightness = 1.0
        elif d < EYE_WIDTH:
            brightness = 1.0 - ((d - 0.5) / (EYE_WIDTH - 0.5))
        else:
            brightness = 0.04 + 0.08 * light_mix

        pixel_hue = hue + (d1 - d2) * 8

        if d < EYE_WIDTH:
            brightness = min(1.0, brightness + flap_pulse * 0.25)

        pixels[i] = hsv_to_rgb(pixel_hue, sat, val * brightness)

    pixels.show()


# ══════════════════════════════════════════════════════
#  AUDIO — single track on loop
# ══════════════════════════════════════════════════════
audio_file = open("assets/audio.mp3", "rb")
audio_mp3  = audiomp3.MP3Decoder(audio_file)

audio = audiobusio.I2SOut(
    bit_clock=board.I2S_BIT_CLOCK,
    word_select=board.I2S_WORD_SELECT,
    data=board.I2S_DATA
)

mixer = audiomixer.Mixer(
    voice_count=1,
    sample_rate=audio_mp3.sample_rate,
    channel_count=audio_mp3.channel_count,
    bits_per_sample=audio_mp3.bits_per_sample,
    samples_signed=True
)
audio.play(mixer)
mixer.voice[0].play(audio_mp3)

# ── STATE ──
servo_angle     = FLAP_MIN
servo_direction = 1
start_time      = time.monotonic()
frame_count     = 0
PIXEL_UPDATE_EVERY = 3

# ══════════════════════════════════════════════════════
#  MAIN LOOP
# ══════════════════════════════════════════════════════
while True:
    now = time.monotonic()
    t   = now - start_time

    #  Potentiometer → volume, brightness & flap speed 
    pot_value = potentiometer.value / 65535.0
    vol = max(0.2, pot_value)
    mixer.voice[0].level = vol
    pixels.brightness = max(0.05, pot_value * 0.8)
    
    flap_delay = FLAP_DELAY_SLOW + (FLAP_DELAY_FAST - FLAP_DELAY_SLOW) * pot_value

    # Photocell
    light_mix = read_light_mix()
    led.value = (light_mix < 0.5)

    # Loop audio when it ends
    if not mixer.voice[0].playing:
        audio_file.seek(0)
        mixer.voice[0].play(audio_mp3)

    # Servo flap
    servo_angle += FLAP_STEP * servo_direction
    if servo_angle >= FLAP_MAX:
        servo_angle = FLAP_MAX
        servo_direction = -1
    elif servo_angle <= FLAP_MIN:
        servo_angle = FLAP_MIN
        servo_direction = 1
    my_servo.angle = servo_angle

    flap_progress = servo_angle / FLAP_MAX
    flap_pulse = 1.0 - abs(flap_progress - 0.5) * 2.0

    # Blink timer
    if not is_blinking and (now - last_blink_time) >= BLINK_INTERVAL:
        is_blinking = True
        blink_start = now
    if is_blinking and (now - blink_start) >= BLINK_DURATION:
        is_blinking = False
        last_blink_time = now

    # Draw animated eyes
    frame_count += 1
    if frame_count >= PIXEL_UPDATE_EVERY:
        frame_count = 0
        draw_eyes(t, light_mix, flap_pulse, is_blinking)

    if frame_count == 0:
        side = "Up" if servo_direction == 1 else "Down"
        mode = "Night" if light_mix < 0.3 else ("Day" if light_mix > 0.7 else "Trans")
        print(f"Ang:{servo_angle:3d} ({side}) | Vol:{vol:.2f} | Mix:{light_mix:.2f} {mode}")

    time.sleep(flap_delay)
