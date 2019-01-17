import math
import numpy as np
from pyspace.util import *

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
		if vec3_eq(self.n, (1,0,0)):
			return '\tp.x = abs(p.x - ' + float_str(self.d) + ') + ' + float_str(self.d) + ';\n'
		elif vec3_eq(self.n, (0,1,0)):
			return '\tp.y = abs(p.y - ' + float_str(self.d) + ') + ' + float_str(self.d) + ';\n'
		elif vec3_eq(self.n, (0,0,1)):
			return '\tp.z = abs(p.z - ' + float_str(self.d) + ') + ' + float_str(self.d) + ';\n'
		elif vec3_eq(self.n, (-1,0,0)):
			return '\tp.x = -abs(p.x + ' + float_str(self.d) + ') - ' + float_str(self.d) + ';\n'
		elif vec3_eq(self.n, (0,-1,0)):
			return '\tp.y = -abs(p.y + ' + float_str(self.d) + ') - ' + float_str(self.d) + ';\n'
		elif vec3_eq(self.n, (0,0,-1)):
			return '\tp.z = -abs(p.z + ' + float_str(self.d) + ') - ' + float_str(self.d) + ';\n'
		else:
			return '\tplaneFold(p, ' + vec3_str(self.n) + ', ' + float_str(self.d) + ');\n'

'''
EQUIVALENT FOLD:
  FoldPlane((1, 0, 0), c_x))
  FoldPlane((0, 1, 0), c_y))
  FoldPlane((0, 0, 1), c_z))
'''
class FoldAbs:
	def __init__(self, c=(0,0,0)):
		self.c = set_global_vec3(c)

	def fold(self, p):
		c = get_global(self.c)
		p[:3] = np.abs(p[:3] - c) + c

	def unfold(self, p, q):
		c = get_global(self.c)
		if p[0] < c[0]: q[0] = 2*c[0] - q[0]
		if p[1] < c[1]: q[1] = 2*c[0] - q[1]
		if p[2] < c[2]: q[2] = 2*c[0] - q[2]

	def glsl(self):
		if vec3_eq(self.c, (0,0,0)):
			return '\tp.xyz = abs(p.xyz);\n'
		else:
			return '\tabsFold(p, ' + vec3_str(self.c) + ');\n'

'''
EQUIVALENT FOLD:
  FoldPlane((inv_sqrt2, inv_sqrt2, 0)))
  FoldPlane((inv_sqrt2, 0, inv_sqrt2)))
  FoldPlane((0, inv_sqrt2, inv_sqrt2)))
'''
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

'''
EQUIVALENT FOLD:
  FoldPlane((inv_sqrt2, -inv_sqrt2, 0)))
  FoldPlane((inv_sqrt2, 0, -inv_sqrt2)))
  FoldPlane((0, inv_sqrt2, -inv_sqrt2)))
'''
class FoldMenger:
	def __init__(self):
		pass

	def fold(self, p):
		if p[0] < p[1]:
			p[[0,1]] = p[[1,0]]
		if p[0] < p[2]:
			p[[0,2]] = p[[2,0]]
		if p[1] < p[2]:
			p[[2,1]] = p[[1,2]]

	def unfold(self, p, q):
		mx = max(p[0], p[1])
		if min(p[0], p[1]) < min(mx, p[2]):
			q[[2,1]] = q[[1,2]]
		if mx < p[2]:
			q[[0,2]] = q[[2,0]]
		if p[0] < p[1]:
			q[[0,1]] = q[[1,0]]

	def glsl(self):
		return '\tmengerFold(p);\n'

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
			if isinstance(self.s, (float, int)) and self.s >= 0:
				ret_str += '\tp *= ' + float_str(self.s) + ';\n'
			else:
				ret_str += '\tp.xyz *= ' + float_str(self.s) + ';\n'
				ret_str += '\tp.w *= abs(' + float_str(self.s) + ');\n'
		if not np.array_equal(self.t, np.zeros((3,), dtype=np.float32)):
			ret_str += '\tp.xyz += ' + vec3_str(self.t) + ';\n'
		return ret_str

class FoldScaleOrigin:
	def __init__(self, s=1.0):
		self.s = set_global_float(s)
		self.o = set_global_vec3((0,0,0))

	def fold(self, p):
		p[:] = p*get_global(self.s) + self.o

	def unfold(self, p, q):
		q[:] = (q - self.o[:3]) / get_global(self.s)

	def glsl(self):
		ret_str = ''
		if self.s != 1.0:
			ret_str += '\tp = p*' + float_str(self.s) + ';p.w = abs(p.w);p += o;\n'
		else:
			ret_str += '\tp += o;\n'
		return ret_str

class FoldBox:
	def __init__(self, r=(1.0,1.0,1.0)):
		self.r = set_global_vec3(r)

	def fold(self, p):
		r = get_global(self.r)
		p[:3] = np.clip(p[:3], -r, r)*2 - p[:3]

	def unfold(self, p, q):
		r = get_global(self.r)
		if p[0] < -r[0]: q[0] = -2*r[0] - q[0]
		if p[1] < -r[1]: q[1] = -2*r[1] - q[1]
		if p[2] < -r[2]: q[2] = -2*r[2] - q[2]
		if p[0] > r[0]: q[0] = 2*r[0] - q[0]
		if p[1] > r[1]: q[1] = 2*r[1] - q[1]
		if p[2] > r[2]: q[2] = 2*r[2] - q[2]

	def glsl(self):
		return '\tboxFold(p,' + vec3_str(self.r) + ');\n'

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
		return '\tsphereFold(p,' + float_str(self.min_r) + ',' + float_str(self.max_r) + ');\n'

class FoldInversion:
	def __init__(self):
		pass

	def fold(self, p):
		p[:] /= (np.dot(p[:3], p[:3]) + 1e-12)

	def unfold(self, p, q):
		q[:] *= (np.dot(p[:3], p[:3]) + 1e-12)

	def glsl(self):
		return '\tp /= length(p.xyz) + 1e-12;\n'

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
		if isinstance(self.a, (float, int)):
			return '\trotX(p, ' + float_str(math.sin(self.a)) + ', ' + float_str(math.cos(self.a)) + ');\n'
		else:
			return '\trotX(p, ' + float_str(self.a) + ');\n'

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
		if isinstance(self.a, (float, int)):
			return '\trotY(p, ' + float_str(math.sin(self.a)) + ', ' + float_str(math.cos(self.a)) + ');\n'
		else:
			return '\trotY(p, ' + float_str(self.a) + ');\n'

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
		if isinstance(self.a, (float, int)):
			return '\trotZ(p, ' + float_str(math.sin(self.a)) + ', ' + float_str(math.cos(self.a)) + ');\n'
		else:
			return '\trotZ(p, ' + float_str(self.a) + ');\n'

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
		return '\tp.x = abs(mod(p.x - ' + float_str(self.m) + '/2,' + float_str(self.m) + ') - ' + float_str(self.m) + '/2);\n'

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
		return '\tp.y = abs(mod(p.y - ' + float_str(self.m) + '/2,' + float_str(self.m) + ') - ' + float_str(self.m) + '/2);\n'

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
		return '\tp.z = abs(mod(p.z - ' + float_str(self.m) + '/2,' + float_str(self.m) + ') - ' + float_str(self.m) + '/2);\n'
