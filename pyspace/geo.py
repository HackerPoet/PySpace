import math
import numpy as np
from util import *

class Sphere:
	def __init__(self, r=1.0, c=(0,0,0)):
		self.r = set_global_float(r)
		self.c = set_global_vec3(c)

	def DE(self, p):
		c = get_global(self.c)
		r = get_global(self.r)
		return (np.linalg.norm(p[:3] - c) - r) / p[3]

	def NP(self, p):
		c = get_global(self.c)
		r = get_global(self.r)
		return normalize(p[:3] - c) * r + c

	def glsl(self):
		return 'de_sphere(p' + cond_offset(self.c) + ', ' + str(self.r) + ')'

	def glsl_col(self):
		return 'col_none(p)'

class Box:
	def __init__(self, r=1.0, c=(0,0,0)):
		self.r = set_global_float(r)
		self.c = set_global_vec3(c)

	def DE(self, p):
		c = get_global(self.c)
		r = get_global(self.r)
		a = np.abs(p[:3] - c) - r;
		return (min(max(a[0], a[1], a[2]), 0.0) + np.linalg.norm(np.maximum(a,0.0))) / p[3]

	def NP(self, p):
		c = get_global(self.c)
		r = get_global(self.r)
		return np.clip(p[:3] - c, -r, r) + c

	def glsl(self):
		return 'de_box(p' + cond_offset(self.c) + ', ' + str(self.r) + ')'

	def glsl_col(self):
		return 'col_none(p)'

class InfCross:
	def __init__(self, r=1.0, c=(0,0,0)):
		self.r = set_global_float(r)
		self.c = set_global_vec3(c)

	def DE(self, p):
		r = get_global(self.r)
		c = get_global(self.c)
		sq = (p[:3] - c) * (p[:3] - c)
		return (math.sqrt(min(min(sq[0] + sq[1], sq[0] + sq[2]), sq[1] + sq[2])) - r) / p[3]

	def NP(self, p):
		r = get_global(self.r)
		c = get_global(self.c)
		n = p[:3] - c
		m_ix = np.argmax(np.abs(n))
		n[m_ix] = 0.0
		n = normalize(n) * r
		n[m_ix] = p[m_ix] - c[m_ix]
		return n + c

	def glsl(self):
		return 'de_inf_cross(p' + cond_offset(self.c) + ', ' + str(self.r) + ')'

	def glsl_col(self):
		return 'col_none(p)'

class InfCrossXY:
	def __init__(self, r=1.0, c=(0,0,0)):
		self.r = set_global_float(r)
		self.c = set_global_vec3(c)

	def DE(self, p):
		r = get_global(self.r)
		c = get_global(self.c)
		sq = (p[:3] - c) * (p[:3] - c)
		return (math.sqrt(min(sq[0], sq[1]) + sq[2]) - r) / p[3]

	def NP(self, p):
		r = get_global(self.r)
		c = get_global(self.c)
		n = p[:3] - c
		m_ix = (0 if abs(n[0]) > abs(n[1]) else 1)
		n[m_ix] = 0.0
		n = normalize(n) * r
		n[m_ix] = p[m_ix] - c[m_ix]
		return n + c

	def glsl(self):
		return 'de_inf_cross_xy(p' + cond_offset(self.c) + ', ' + str(self.r) + ')'

	def glsl_col(self):
		return 'col_none(p)'

class InfLine:
	def __init__(self, r=1.0, n=(1,0,0), c=(0,0,0)):
		self.r = set_global_float(r)
		self.n = set_global_vec3(n)
		self.c = set_global_vec3(c)

	def DE(self, p):
		r = get_global(self.r)
		n = get_global(self.n)
		c = get_global(self.c)
		q = p[:3] - c
		return (np.linalg.norm(q - n*np.dot(n,q)) - r) / p[3]

	def NP(self, p):
		r = get_global(self.r)
		c = get_global(self.c)
		n = p[:3] - c
		m_ix = (0 if abs(n[0]) > abs(n[1]) else 1)
		n[m_ix] = 0.0
		n = normalize(n) * r
		n[m_ix] = p[m_ix] - c[m_ix]
		return n + c

	def glsl(self):
		return 'de_inf_line(p' + cond_offset(self.c) + ', ' + str(self.n) + ', ' + str(self.r) + ')'

	def glsl_col(self):
		return 'col_none(p)'
