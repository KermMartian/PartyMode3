#!/usr/bin/env python3

import sys
import time
import asyncio
import random

import datetime
from pysolar import *
import math
from sunsky import SkyLight

from leds import *

LOCALHOST = '127.0.0.1'
LED_INTERFACE_PORT = 4237

LATITUDE = 40.78431480655391
LONGITUDE = -73.95592912942985

MODE_FULL_COLOR = 0xFFFFFF
MODE_SKYLIGHT_COLOR_BRIGHTSTAR = 0xE0E0FF
MODE_SKYLIGHT_COLOR_DIMSTAR = 0x404050

MODE_FULL_BRIGHTNESS = 255
MODE_DIM_COLOR = 0x303030
MODE_DIM_BRIGHTNESS = 64
MODE_OFF_BRIGHTNESS = 0

PROBABILITY_STAR_BRIGHT = 0.02
PROBABILITY_STAR = 0.05

# For Romantic mode
CANDLESIM_RED_MAX = 40
CANDLESIM_YELLOW_MAX = 88
CANDLESIM_RESET_PROB = 0.075
CANDLESIM_ADJUST_PROB = 0.3

# For Christmas Light mode
MODE_CHRISTMAS_FREQ = 4
c9_red     = 0xae0202
c9_orange  = 0xbf3803
c9_green   = 0x04600
c9_blue    = 0x202069
c9_colors = [c9_red, c9_orange, c9_green, c9_blue]

# For Easter mode
easter_blue = 0x7cecf8
easter_violet = 0x8876eb
easter_pink = 0xfe7f91
easter_yellow = 0xfdd27f
easter_green = 0x76eba7
easter_colors = [easter_blue, easter_violet, easter_pink, easter_yellow, easter_green]

class LEDServerHandler:
	def __init__(self):
		self.strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
		self.strip.begin()
		self.setBrightness(MODE_FULL_BRIGHTNESS)
		self.color = MODE_FULL_COLOR
		self.skylight = SkyLight()

		# Cache these separately so that brightness commands don't override the mode
		self.mode = b'0'
		self.brightness = b'0'

	def setBrightness(self, brightness):
		CHANNEL_NUM = 0
		channel = ws.ws2811_channel_get(self.strip._leds, CHANNEL_NUM)
		ws.ws2811_channel_t_gamma_set(channel, gammaTable(2.0))
		ws.ws2811_channel_t_brightness_set(channel, brightness)

	def brightnessFull(self):
		self.setBrightness(MODE_FULL_BRIGHTNESS)
		self.strip.show()
	
	def brightnessDim(self):
		self.setBrightness(MODE_DIM_BRIGHTNESS)
		self.strip.show()
	
	def modeEaster(self):
		setColor(self.strip, 0x000000)
		self.setBrightness(MODE_FULL_BRIGHTNESS)
		for i in range(0, LED_COUNT):
			self.strip.setPixelColor(i, easter_colors[(i * len(easter_colors)) // LED_COUNT])
		self.strip.show()

	def modeChristmas(self):
		color_idx = 0
		setColor(self.strip, 0x000000)
		self.setBrightness(MODE_FULL_BRIGHTNESS)
		for i in range(0, LED_COUNT, MODE_CHRISTMAS_FREQ):
			self.strip.setPixelColor(i, c9_colors[color_idx])
			color_idx = (color_idx + 1) % len(c9_colors)
		self.strip.show()

	def modeRainbow(self):
		self.setBrightness(MODE_FULL_BRIGHTNESS)
		rainbow(self.strip)

	def modeSkylight(self):
		# Figure out the altitude angle of the sun, right here, right now
		date = datetime.datetime.now(datetime.timezone.utc)
		sun_altitude = math.radians(solar.get_altitude(LATITUDE, LONGITUDE, date))
		sun_azimuth = math.radians(solar.get_azimuth(LATITUDE, LONGITUDE, date))
		if sun_altitude < 0:
			# Nighttime
			setColor(self.strip, 0x000000)
			for i in range(0, LED_COUNT):
				r = random.random()
				if r < PROBABILITY_STAR_BRIGHT:
					self.strip.setPixelColor(i, MODE_SKYLIGHT_COLOR_BRIGHTSTAR)
				elif r < PROBABILITY_STAR:
					self.strip.setPixelColor(i, MODE_SKYLIGHT_COLOR_DIMSTAR)
		else:
			# Daytime
			half_pi = 0.5 * math.pi
			r, g, b = self.skylight.skyRGB(4, half_pi - sun_altitude, sun_azimuth + half_pi, half_pi - sun_altitude)
			for i in range(0, LED_COUNT):
				self.strip.setPixelColorRGB(i, r, g, b)
		self.strip.show()

	def modeRomantic(self):
		self.cur_color_idx = (8 << 8) | 8;
		self.modeRomanticUpdate(force = True)

	def modeRomanticUpdate(self, force = False):
		red    = (self.cur_color_idx >> 8) & 0xff;
		yellow = (self.cur_color_idx & 0xff);

		def updateRomanticColor(self, red, yellow):
			self.cur_color_idx = (red << 8) | yellow
			self.color = correctColor()( \
			             ((16 + red + (yellow >> 1)) << 16) | \
			             ((16 + (yellow >> 1)) << 8) | \
			             8);
			setColor(self.strip, self.color)
			self.strip.show()

		action_prob = random.random()
		if CANDLESIM_RESET_PROB >= action_prob or force:
			# Choose new colors
			red = random.randint(0, CANDLESIM_RED_MAX);
			yellow = random.randint(0, CANDLESIM_YELLOW_MAX);
			updateRomanticColor(self, red, yellow)

		elif CANDLESIM_ADJUST_PROB >= action_prob:
			# Slightly adjust existing colors
			if CANDLESIM_ADJUST_PROB / 2. >= action_prob:
				red = max(min(red + random.choice((-1, 1)), CANDLESIM_RED_MAX - 1), 0)
			else:
				yellow = max(min(yellow + random.choice((-1, 1)), CANDLESIM_YELLOW_MAX - 1), 0)
			updateRomanticColor(self, red, yellow)

	def modeOff(self):
		self.setBrightness(MODE_OFF_BRIGHTNESS)
		self.strip.show()

	async def handle_client(self, reader, writer):
		while not reader.at_eof():
			command = await reader.read(1)
			if command == b'm':
				mode = await reader.read(1)
				if mode == b'x':
					self.modeChristmas()
				elif mode == b'e':
					self.modeEaster()
				elif mode == b'a':
					self.modeRainbow()
				elif mode == b'r':
					self.modeRomantic()
				elif mode == b's':
					self.modeSkylight()
				elif mode == b'0':
					self.modeOff()

				# Update stored mode
				self.mode = mode

			elif command == b'b':
				brightness = await reader.read(1)
				if brightness == b'f':                 # Full
					self.brightnessFull()
				elif brightness == b'd':               # Dim
					self.brightnessDim()

				# Update stored brightness
				self.brightness = brightness

			elif command == b'w':
				temperature = await reader.read(5)
				try:
					temperature = int(temperature.decode('ascii').lstrip('0'))
				except ValueError:
					temperature = 2900

				self.color = getWhite(temperature)
				setColor(self.strip, self.color)
				self.strip.show()

			elif command == b'c':
				self.color = correctColor()(int(str(await reader.read(6), encoding='ascii'), 16))
				setColor(self.strip, self.color)
				self.strip.show()
			else:
				print("Unknown command %s" % command)

	@staticmethod
	async def updateLighting(self):
		while True:
			if self.mode == b's':
				self.modeSkylight()
			elif self.mode == b'r':
				self.modeRomanticUpdate()
			await asyncio.sleep(0.1)

async def main():
	ctx = LEDServerHandler()
	server = await asyncio.start_server(ctx.handle_client, LOCALHOST, LED_INTERFACE_PORT)
	loop = server.get_loop()
	task = loop.create_task(LEDServerHandler.updateLighting(ctx), name='update')
	async with server:
		await server.serve_forever()

if __name__ == '__main__':
	asyncio.run(main())
