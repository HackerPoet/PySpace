import numpy as np
from util import *

class OrbitInitZero:
	def __init__(self):
		pass

	def orbit(self):
		return '\tvec3 orbit = vec3(0.0);\n'

class OrbitInitInf:
	def __init__(self):
		pass

	def orbit(self):
		return '\tvec3 orbit = vec3(1e20);\n'
		
class OrbitMin:
	def __init__(self, scale=(1,1,1)):
		self.scale = set_global_vec3(scale)

	def orbit(self):
		return '\torbit = min(orbit, abs(p.xyz)*' + vec3_str(self.scale) + ');\n'

class OrbitSum:
	def __init__(self):
		pass

	def orbit(self):
		return '\torbit = min(orbit, abs(p.xyz));\n'
