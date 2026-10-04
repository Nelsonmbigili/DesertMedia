import time
import board
import digitalio
import pwmio
import audiobusio
import audiocore
import audiomixer
import neopixel
from analogio import AnalogIn
from adafruit_motor import servo
from rainbowio import colorwheel

print("Prop-Maker Servo, Audio, Potentiometer & Photoresistor Demo")

# allow extenal power 
external_power = digitalio.DigitalInOut(board.EXTERNAL_POWER)
external_power.direction = digitalio.Direction.OUTPUT
external_power.value = True
time.sleep(0.2)

# Photocell (A0), and Potentiometer (A2)
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
light_sensor = AnalogIn(board.A0)
potentiometer = AnalogIn(board.A2)

# Servo
pwm = pwmio.PWMOut(board.EXTERNAL_SERVO, duty_cycle=0, frequency=50)
my_servo = servo.Servo(pwm, min_pulse=500, max_pulse=2500)

# NeoPixel Ring
NUM_PIXELS = 16 
pixels = neopixel.NeoPixel(
    board.EXTERNAL_NEOPIXELS, 
    NUM_PIXELS, 
    brightness=0.3, 
    auto_write=True
)

# Speaker Audio & Mixer
audio = audiobusio.I2SOut(
    bit_clock=board.I2S_BIT_CLOCK,
    word_select=board.I2S_WORD_SELECT,
    data=board.I2S_DATA
)

wav_file = open("assets/wind.wav", "rb")
wave_obj = audiocore.WaveFile(wav_file)

mixer = audiomixer.Mixer(
    voice_count=1,
    sample_rate=wave_obj.sample_rate,
    channel_count=wave_obj.channel_count,
    bits_per_sample=wave_obj.bits_per_sample,
    samples_signed=True
)
audio.play(mixer)

def play_sound():
    if not mixer.voice[0].playing:
        mixer.voice[0].play(wave_obj)

servo_angle = 0
servo_direction = 1

while True:
    # Read Potentiometer on A2 (Controls Volume, Brightness, Speed) 
    pot_value = potentiometer.value / 65535.0
    
    mixer.voice[0].level = pot_value
    pixels.brightness = pot_value
    
    current_speed_step = 1 + int(pot_value * 9)
    actual_step = current_speed_step if servo_direction == 1 else -current_speed_step

    # Read Photoresistor on A0 (Controls Color) 
    light_value = light_sensor.value
    color_index = int((light_value / 65535.0) * 255)
    
    pixels.fill(colorwheel(color_index))
    
    if (light_value / 65535.0) < 0.5:
        led.value = True
    else:
        led.value = False

    #  Move Servo 
    servo_angle += actual_step

    if servo_angle >= 180:
        servo_angle = 180
        servo_direction = -1
        play_sound()
    elif servo_angle <= 0:
        servo_angle = 0
        servo_direction = 1
        play_sound()

    my_servo.angle = servo_angle

    side = "Forward" if servo_direction == 1 else "Reverse"
    
    print(f"Speed: ({current_speed_step} + {side}) Volume: ({pot_value:.2f}) Light: ({pot_value:.2f} + {color_index})")

    time.sleep(0.05)
