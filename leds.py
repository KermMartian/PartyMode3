#!/usr/bin/env python3

from rpi_ws281x import Color, PixelStrip, ws
import time
import math

# LED strip configuration:
LED_COUNT = 240       # Number of LED pixels.
LED_PIN = 12          # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0
LED_STRIP = ws.WS2812_STRIP

LED_PURE_WHITE_CORRECTION = 0xFFE08C

class ColorTemperature:
	# 1900 Kelvin
	Candle = 0xFF9329         # 1900 K, 255, 147, 41
	# 2600 Kelvin
	Tungsten40W = 0xFFC58F    # 2600 K, 255, 197, 143
	# 2850 Kelvin
	Tungsten100W = 0xFFD6AA   # 2850 K, 255, 214, 170
	# 3200 Kelvin
	Halogen = 0xFFF1E0        # 3200 K, 255, 241, 224
	# 5200 Kelvin
	CarbonArc = 0xFFFAF4      # 5200 K, 255, 250, 244
	# 5400 Kelvin
	HighNoonSun = 0xFFFFFB    # 5400 K, 255, 255, 251
	# 6000 Kelvin
	DirectSunlight = 0xFFFFFF # 6000 K, 255, 255, 255
	# 7000 Kelvin
	OvercastSky = 0xC9E2FF    # 7000 K, 201, 226, 255
	# 20000 Kelvin
	ClearBlueSky = 0x409CFF   # 20000 K, 64, 156, 255

# Get the color for a temperature
def getWhite(temp):
	temps = {
		1900: ColorTemperature.Candle, \
		2600: ColorTemperature.Tungsten40W, \
		2850: ColorTemperature.Tungsten100W, \
		3200: ColorTemperature.Halogen, \
		5200: ColorTemperature.CarbonArc, \
		5400: ColorTemperature.HighNoonSun, \
		6000: ColorTemperature.DirectSunlight, \
		7000: ColorTemperature.OvercastSky, \
		20000: ColorTemperature.ClearBlueSky, \
	}
	temp_keys = sorted(temps.keys())
	if temp < temp_keys[0]:
		return temps[temp_keys[0]]
	elif temp > temp_keys[-1]:
		return temps[temp_keys[-1]]
	else:
		for i in range(len(temp_keys) - 1):
			if temp >= temp_keys[i] and temp <= temp_keys[i + 1]:
				c1 = temp_keys[i]
				c2 = temp_keys[i + 1]
				break
		else:
			# This should be impossible
			return temps[temp_keys[-1]]

	ratio = (temp - c1) / (c2 - c1)
	c1 = temps[c1]
	c2 = temps[c2]
	channelCorrect = lambda ch1, ch2, ratio: int(float(ch2) * ratio + float(ch1) * (1.0 - ratio))
	componentCorrect = lambda c1, c2, bit_offset, ratio: channelCorrect((c1 >> bit_offset) & 0x0ff, (c2 >> bit_offset) & 0x0ff, ratio) << bit_offset
	return componentCorrect(c1, c2, 16, ratio) | componentCorrect(c1, c2, 8, ratio) | componentCorrect(c1, c2, 0, ratio)

# Correct color balance
class correctColor:
	color_factor_r = (LED_PURE_WHITE_CORRECTION >> 16) & 0xff
	color_factor_g = (LED_PURE_WHITE_CORRECTION >> 8) & 0xff
	color_factor_b = LED_PURE_WHITE_CORRECTION & 0xff

	def __call__(self, color):
		return (((((color >> 16) & 0xff) * self.color_factor_r) // 0xff) << 16) | \
		       (((((color >> 8) & 0xff)  * self.color_factor_g) // 0xff) << 8)  | \
		       (((color & 0xff)          * self.color_factor_b) // 0xff)

def gammaTable(gamma = 2.8, max_in = 255, max_out = 255):
	return [int(math.pow(float(i) / float(max_in), gamma) * float(max_out) + 0.5) for i in range(256)]

# Define functions which animate LEDs in various ways.
def setColor(strip, color):
	for i in range(strip.numPixels()):
		strip.setPixelColor(i, color)
	strip.show()

def colorWipe(strip, color, wait_ms=50):
	"""Wipe color across display a pixel at a time."""
	for i in range(strip.numPixels()):
		strip.setPixelColor(i, color)
		strip.show()
		time.sleep(wait_ms / 1000.0)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)

