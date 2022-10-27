#!/usr/bin/env python3

import sys
import time
import asyncio

from led import *

LOCALHOST = '127.0.0.1'
LED_INTERFACE_PORT = 4237

MODE_FULL_COLOR = 0xFFFFFF
MODE_FULL_BRIGHTNESS = 255
MODE_DIM_COLOR = 0x303030
MODE_DIM_BRIGHTNESS = 64
MODE_OFF_BRIGHTNESS = 0

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

	def setBrightness(self, brightness):
		CHANNEL_NUM = 0
		channel = ws.ws2811_channel_get(self.strip._leds, CHANNEL_NUM)
		ws.ws2811_channel_t_brightness_set(channel, brightness)

	def modeFull(self):
		setColor(self.strip, self.color)
		self.setBrightness(MODE_FULL_BRIGHTNESS)
		self.strip.show()
	
	def modeDim(self):
		setColor(self.strip, self.color)
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
				elif mode == b'0':
					self.modeOff()
			elif command == b'c':
				self.color = int(str(await reader.read(6), encoding='ascii'), 16)
			else:
				print("Unknown command %s" % command)

async def main():
	ctx = LEDServerHandler()
	server = await asyncio.start_server(ctx.handle_client, LOCALHOST, LED_INTERFACE_PORT)
	async with server:
		await server.serve_forever()

if __name__ == '__main__':
	asyncio.run(main())
