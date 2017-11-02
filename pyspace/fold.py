import math
import numpy as np
from util import *

class FoldPlane:
	def __init__(self, n, d=0.0):
		self.n = set_global_vec3(n)
		self.d = set_global_float(d)
	
	def fold(self, p):
		n = get_global(self.n)
		d = get_global(self.d)
		p[:3] -= 2.0 * min(0.0, np.dot(p[:3], n) - d) * n

	def unfold(self, p, q):
		n = get_global(self.n)
		d = get_global(self.d)
		if np.dot(p[:3], n) - d < 0.0:
			q[:3] -= 2.0 * (np.dot(q[:3], n) - d) * n
	
	def glsl(self):
		return '\tplaneFold(p, ' + vec3_str(self.n) + ', ' + str(self.d) + ');\n'

class FoldAbs:
	def __init__(self):
		pass
	
	def fold(self, p):
		p[:3] = np.abs(p[:3])

	def unfold(self, p, q):
		if p[0] < 0.0: q[0] = -q[0]
		if p[1] < 0.0: q[1] = -q[1]
		if p[2] < 0.0: q[2] = -q[2]
		
	def glsl(self):
		return '\tabsFold(p);\n'

class FoldSierpinski:
	def __init__(self):
		pass
	
	def fold(self, p):
		if p[0] + p[1] < 0.0:
			p[[0,1]] = -p[[1,0]]
		if p[0] + p[2] < 0.0:
			p[[0,2]] = -p[[2,0]]
		if p[1] + p[2] < 0.0:
			p[[2,1]] = -p[[1,2]]

	def unfold(self, p, q):
		mx = max(-p[1], p[0])
		if max(p[1], -p[0]) + max(-mx, p[2]) < 0.0:
			q[[2,1]] = -q[[1,2]]
		if mx + p[2] < 0.0:
			q[[0,2]] = -q[[2,0]]
		if p[0] + p[1] < 0.0:
			q[[0,1]] = -q[[1,0]]
		
	def glsl(self):
		return '\tsierpinskiFold(p);\n'

class FoldScaleTranslate:
	def __init__(self, s=1.0, t=(0,0,0)):
		self.s = set_global_float(s)
		self.t = set_global_vec3(t)

	def fold(self, p):
		p[:] *= get_global(self.s)
		p[:3] += get_global(self.t)

	def unfold(self, p, q):
		q[:3] -= get_global(self.t)
		q[:] /= get_global(self.s)
	
	def glsl(self):
		ret_str = ''
		if self.s != 1.0:
			ret_str += '\tp.xyz *= ' + str(self.s) + ';\n'
			ret_str += '\tp.w *= abs(' + str(self.s) + ');\n'
		if not np.array_equal(self.t, np.zeros((3,), dtype=np.float32)):
			ret_str += '\tp.xyz += ' + vec3_str(self.t) + ';\n'
		return ret_str
		
class FoldScaleOrigin:
	def __init__(self, s=1.0):
		self.s = set_global_float(s)
		self.o = None

	def fold(self, p):
		p[:] = p*get_global(self.s) + self.o

	def unfold(self, p, q):
		q[:] = (q - self.o[:3]) / get_global(self.s)
	
	def glsl(self):
		ret_str = ''
		if self.s != 1.0:
			ret_str += '\tp = p*' + str(self.s) + ' + o;\n'
		else:
			ret_str += '\tp += o;\n'
		return ret_str

class FoldBox:
	def __init__(self, r=1.0):
		self.r = set_global_float(r)
	
	def fold(self, p):
		r = get_global(self.r)
		p[:3] = np.clip(p[:3], -r, r)*2 - p[:3]

	def unfold(self, p, q):
		r = get_global(self.r)
		if p[0] < -r: q[0] = -2*r - q[0]
		if p[1] < -r: q[1] = -2*r - q[1]
		if p[2] < -r: q[2] = -2*r - q[2]
		if p[0] > r: q[0] = 2*r - q[0]
		if p[1] > r: q[1] = 2*r - q[1]
		if p[2] > r: q[2] = 2*r - q[2]
	
	def glsl(self):
		return '\tboxFold(p,' + str(self.r) + ');\n'

class FoldSphere:
	def __init__(self, min_r=0.5, max_r=1.0):
		self.min_r = set_global_float(min_r)
		self.max_r = set_global_float(max_r)
	
	def fold(self, p):
		max_r = get_global(self.max_r)
		min_r = get_global(self.min_r)
		r2 = np.dot(p[:3], p[:3])
		p[:] *= max(max_r / max(min_r, r2), 1.0)

	def unfold(self, p, q):
		max_r = get_global(self.max_r)
		min_r = get_global(self.min_r)
		r2 = np.dot(p[:3], p[:3])
		q[:] /= max(max_r / max(min_r, r2), 1.0)
	
	def glsl(self):
		return '\tsphereFold(p,' + str(self.min_r) + ',' + str(self.max_r) + ');\n'

class FoldInversion:
	def __init__(self):
		self.r = 4.0
		self.a = 0.5
	
	def fold(self, p):
		p[:] /= (np.dot(p[:3], p[:3]) + 1e-12)

	def unfold(self, p, q):
		q[:] *= (np.dot(p[:3], p[:3]) + 1e-12)
	
	def glsl(self):
		return '\tfloat pd = length(p.xyz);p *= 1 + 0.5*max(8.0 - pd, 0.0)/pd;\n'
		#return '\tp.xyz /= dot(p.xyz,p.xyz) + ' + str(self.s) + ';\n'
		
class FoldRotateX:
	def __init__(self, a):
		self.a = set_global_float(a)
	
	def fold(self, p):
		a = get_global(self.a)
		s,c = math.sin(a), math.cos(a)
		p[1], p[2] = (c*p[1] + s*p[2]), (c*p[2] - s*p[1])

	def unfold(self, p, q):
		a = get_global(self.a)
		s,c = math.sin(-a), math.cos(-a)
		q[1], q[2] = (c*q[1] + s*q[2]), (c*q[2] - s*q[1])
	
	def glsl(self):
		return '\trotX(p, ' + str(self.a) + ');\n'

class FoldRotateY:
	def __init__(self, a):
		self.a = set_global_float(a)
	
	def fold(self, p):
		a = get_global(self.a)
		s,c = math.sin(a), math.cos(a)
		p[2], p[0] = (c*p[2] + s*p[0]), (c*p[0] - s*p[2])

	def unfold(self, p, q):
		a = get_global(self.a)
		s,c = math.sin(-a), math.cos(-a)
		q[2], q[0] = (c*q[2] + s*q[0]), (c*q[0] - s*q[2])
	
	def glsl(self):
		return '\trotY(p, ' + str(self.a) + ');\n'

class FoldRotateZ:
	def __init__(self, a):
		self.a = set_global_float(a)
	
	def fold(self, p):
		a = get_global(self.a)
		s,c = math.sin(a), math.cos(a)
		p[0], p[1] = (c*p[0] + s*p[1]), (c*p[1] - s*p[0])

	def unfold(self, p, q):
		a = get_global(self.a)
		s,c = math.sin(-a), math.cos(-a)
		q[0], q[1] = (c*q[0] + s*q[1]), (c*q[1] - s*q[0])
	
	def glsl(self):
		return '\trotZ(p, ' + str(self.a) + ');\n'

class FoldRepeatX:
	def __init__(self, m):
		self.m = set_global_float(m)
	
	def fold(self, p):
		m = get_global(self.m)
		p[0] = abs((p[0] - m/2) % m - m/2)

	def unfold(self, p, q):
		m = get_global(self.m)
		a = (p[0] - m/2) % m - m/2
		if a < 0.0: q[0] = -q[0]
		q[0] += p[0] - a
	
	def glsl(self):
		return '\tp.x = abs(mod(p.x - ' + str(self.m) + '/2,' + str(self.m) + ') - ' + str(self.m) + '/2);\n'

class FoldRepeatY:
	def __init__(self, m):
		self.m = set_global_float(m)
	
	def fold(self, p):
		m = get_global(self.m)
		p[1] = abs((p[1] - m/2) % m - m/2)

	def unfold(self, p, q):
		m = get_global(self.m)
		a = (p[1] - m/2) % m - m/2
		if a < 0.0: q[1] = -q[1]
		q[1] += p[1] - a
	
	def glsl(self):
		return '\tp.y = abs(mod(p.y - ' + str(self.m) + '/2,' + str(self.m) + ') - ' + str(self.m) + '/2);\n'

class FoldRepeatZ:
	def __init__(self, m):
		self.m = set_global_float(m)
	
	def fold(self, p):
		m = get_global(self.m)
		p[2] = abs((p[2] - m/2) % m - m/2)

	def unfold(self, p, q):
		m = get_global(self.m)
		a = (p[2] - m/2) % m - m/2
		if a < 0.0: q[2] = -q[2]
		q[2] += p[2] - a
	
	def glsl(self):
		return '\tp.z = abs(mod(p.z - ' + str(self.m) + '/2,' + str(self.m) + ') - ' + str(self.m) + '/2);\n'
