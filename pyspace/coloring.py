import numpy as np
from pyspace.util import *

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

class OrbitInitNegInf:
	def __init__(self):
		pass

	def orbit(self):
		return '\tvec3 orbit = vec3(-1e20);\n'
		
class OrbitMin:
	def __init__(self, scale=(1,1,1), origin=(0,0,0)):
		self.scale = set_global_vec3(scale)
		self.origin = set_global_vec3(origin)

	def orbit(self):
		if vec3_eq(self.origin, (0,0,0)):
			return '\torbit = min(orbit, p.xyz*' + vec3_str(self.scale) + ');\n'
		else:
			return '\torbit = min(orbit, (p.xyz - ' + vec3_str(self.origin) + ')*' + vec3_str(self.scale) + ');\n'

class OrbitMinAbs:
	def __init__(self, scale=(1,1,1), origin=(0,0,0)):
		self.scale = set_global_vec3(scale)
		self.origin = set_global_vec3(origin)

	def orbit(self):
		return '\torbit = min(orbit, abs((p.xyz - ' + vec3_str(self.origin) + ')*' + vec3_str(self.scale) + '));\n'

class OrbitMax:
	def __init__(self, scale=(1,1,1), origin=(0,0,0)):
		self.scale = set_global_vec3(scale)
		self.origin = set_global_vec3(origin)

	def orbit(self):
		return '\torbit = max(orbit, (p.xyz - ' + vec3_str(self.origin) + ')*' + vec3_str(self.scale) + ');\n'

class OrbitMaxAbs:
	def __init__(self, scale=(1,1,1), origin=(0,0,0)):
		self.scale = set_global_vec3(scale)
		self.origin = set_global_vec3(origin)

	def orbit(self):
		return '\torbit = max(orbit, abs((p.xyz - ' + vec3_str(self.origin) + ')*' + vec3_str(self.scale) + '));\n'

class OrbitSum:
	def __init__(self, scale=(1,1,1), origin=(0,0,0)):
		self.scale = set_global_vec3(scale)
		self.origin = set_global_vec3(origin)

	def orbit(self):
		return '\torbit += (p.xyz - ' + vec3_str(self.origin) + ')*' + vec3_str(self.scale) + ';\n'

class OrbitSumAbs:
	def __init__(self, scale=(1,1,1), origin=(0,0,0)):
		self.scale = set_global_vec3(scale)
		self.origin = set_global_vec3(origin)

	def orbit(self):
		return '\torbit += abs((p.xyz - ' + vec3_str(self.origin) + ')*' + vec3_str(self.scale) + ');\n'
