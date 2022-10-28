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

MODE_CHRISTMAS_FREQ = 4
c9_red     = 0xae0202
c9_orange  = 0xbf3803
c9_green   = 0x04600
c9_blue    = 0x202069
c9_colors = [c9_red, c9_orange, c9_green, c9_blue]

class LEDServerHandler:
	def __init__(self):
		self.strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
		self.strip.begin()
		self.color = MODE_FULL_COLOR
		self.skylight = SkyLight()

	def setBrightness(self, brightness):
		CHANNEL_NUM = 0
		channel = ws.ws2811_channel_get(self.strip._leds, CHANNEL_NUM)
		ws.ws2811_channel_t_brightness_set(channel, brightness)

	def modeFull(self):
		self.setBrightness(MODE_FULL_BRIGHTNESS)
		self.strip.show()
	
	def modeDim(self):
		self.setBrightness(MODE_DIM_BRIGHTNESS)
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

	def modeOff(self):
		self.setBrightness(MODE_OFF_BRIGHTNESS)
		self.strip.show()

	async def handle_client(self, reader, writer):
		while not reader.at_eof():
			command = await reader.read(1)
			if command == b'm':
				mode = await reader.read(1)
				if mode == b'f':                 # Full
					self.modeFull()
				elif mode == b'd':               # Dim
					self.modeDim()
				elif mode == b'x':
					self.modeChristmas()
				elif mode == b'a':
					self.modeRainbow()
				elif mode == b's':
					self.modeSkylight()
				elif mode == b'0':
					self.modeOff()
			elif command == b'c':
				self.color = correctColor()(int(str(await reader.read(6), encoding='ascii'), 16))
				setColor(self.strip, self.color)
				self.strip.show()
			else:
				print("Unknown command %s" % command)

async def main():
	ctx = LEDServerHandler()
	server = await asyncio.start_server(ctx.handle_client, LOCALHOST, LED_INTERFACE_PORT)
	async with server:
		await server.serve_forever()

if __name__ == '__main__':
	asyncio.run(main())
