#!/usr/bin/env python3

from pysolar.solar import *
from rgbxy import Converter as ColorspaceConverter
import datetime
import numpy as np
import math

class SkyLight:
	ZENITH_CHROMATICITY_MATRIX_x = np.array([ \
		[0.0017,	-0.0037,	0.0021,		0.000], \
		[-0.0290,	0.0638,		-0.0320,	0.0039], \
		[0.1169,	-0.2120,	0.0605,		0.2589]])

	ZENITH_CHROMATICITY_MATRIX_y = np.array([ \
		[0.0028,	-0.0061,	0.0032,		0.000], \
		[-0.0421,	0.0897,		-0.0415,	0.0052], \
		[0.1535,	-0.2676,	0.0667,		0.2669]])

	COEFFICIENTS_Y = np.array([ \
		[0.1787,	-1.4630], \
		[-0.3554,	0.4275], \
		[-0.0227,	5.3251], \
		[0.1206,	-2.5771], \
		[-0.0670,	0.3703]])

	COEFFICIENTS_x = np.array([ \
		[-0.0193,	-0.2592], \
		[-0.0665,	0.0008], \
		[-0.0004,	0.2125], \
		[-0.0641,	-0.8989], \
		[-0.0033,	0.0452]])

	COEFFICIENTS_y = np.array([ \
		[-0.0167,	-0.2608], \
		[-0.0950,	0.0092], \
		[-0.0079,	0.2102], \
		[-0.0441,	-1.6537], \
		[-0.0109,	0.0529]])

	def __init__(self):
		self.colorspace_converter = ColorspaceConverter()

	@staticmethod
	def componentF(A, B, C, D, E, theta, gamma):
		return (1.0 + A * math.exp(B / math.cos(theta))) * \
		       (1.0 + C * math.exp(D * gamma) + E * math.pow(math.cos(gamma), 2.0))

	@staticmethod
	def componentByAngle(A, B, C, D, E, zenith_value, theta, gamma, sun_theta):
		return zenith_value * \
		       SkyLight.componentF(A, B, C, D, E, theta, gamma) / \
		       SkyLight.componentF(A, B, C, D, E, 0, sun_theta)

	def zenithLuminance(self, turbidity, sun_theta):
		chi = lambda turbidity, sun_theta: ((4.0/9.0) - (turbidity / 120.0)) * (math.pi - 2.0 * sun_theta)
		return (4.0453 * turbidity - 4.9710) * math.tan(chi(turbidity, sun_theta)) - \
		       0.2155 * turbidity + 2.4192

	def zenithChromaticity(self, turbidity, sun_theta):
		turbidity_row = np.array([[math.pow(turbidity, 2.0), turbidity, 1.0]])
		sun_angle_col = np.array([[math.pow(sun_theta, 3.0)], [math.pow(sun_theta, 2.0)], [sun_theta], [1.0]])
		return (turbidity_row @ self.ZENITH_CHROMATICITY_MATRIX_x @ sun_angle_col, \
		        turbidity_row @ self.ZENITH_CHROMATICITY_MATRIX_y @ sun_angle_col)

	def skyYxy(self, turbidity, theta, gamma, sun_theta):
		turbidity_col = np.array([[turbidity], [1.0]])
		AY, BY, CY, DY, EY = list(self.COEFFICIENTS_Y @ turbidity_col)
		Ax, Bx, Cx, Dx, Ex = list(self.COEFFICIENTS_x @ turbidity_col)
		Ay, By, Cy, Dy, Ey = list(self.COEFFICIENTS_y @ turbidity_col)

		Yz = self.zenithLuminance(turbidity, sun_theta)
		Y = SkyLight.componentByAngle(AY, BY, CY, DY, EY, Yz, theta, gamma, sun_theta)
		xz, yz = self.zenithChromaticity(turbidity, sun_theta)
		x = SkyLight.componentByAngle(Ax, Bx, Cx, Dx, Ex, xz, theta, gamma, sun_theta)
		y = SkyLight.componentByAngle(Ay, By, Cy, Dy, Ey, yz, theta, gamma, sun_theta)

		return (Y, x, y)

	def skyRGB(self, turbidity, theta, gamma, sun_theta):
		Y, x, y = self.skyYxy(turbidity, theta, gamma, sun_theta)
		r, g, b = self.colorspace_converter.xy_to_rgb(x, y)
		return (r, g, b)
