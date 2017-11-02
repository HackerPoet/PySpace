import numpy as np
from util import *

class Object:
	def __init__(self, name='main'):
		self.trans = []
		self.name = name

	def add(self, fold):
		self.trans.append(fold)

	def DE(self, origin):
		p = np.copy(origin)
		d = 1e20
		for t in self.trans:
			if hasattr(t, 'fold'):
				#if hasattr(t, 'o'):
				#	t.o = origin
				t.fold(p)
			elif hasattr(t, 'DE'):
				d = min(d, t.DE(p))
			else:
				raise Exception("Invalid type in transformation queue")
		return d

	def NP(self, origin):
		undo = []
		p = np.copy(origin)
		d = 1e20
		n = None
		for t in self.trans:
			if hasattr(t, 'fold'):
				#if hasattr(fold, 'o'):
				#	fold.o = origin
				undo.append((t, np.copy(p)))
				t.fold(p)
			elif hasattr(t, 'NP'):
				cur_n = t.NP(p)
				cur_d = norm_sq(cur_n - p[:3])
				if cur_d < d:
					d = cur_d
					n = cur_n
			else:
				raise Exception("Invalid type in transformation queue")
		for fold, p in undo[::-1]:
			fold.unfold(p, n)
		return n

	def glsl(self):
		return 'de_' + self.name + '(p)'

	def glsl_col(self):
		return 'col_' + self.name + '(p)'

	def compiled(self):
		s = 'float de_' + self.name + '(vec4 p) {\n'
		#s += '\tvec4 o = p;\n'
		s += '\tfloat d = 1e20;\n'
		for t in self.trans:
			if hasattr(t, 'fold'):
				s += t.glsl()
			elif hasattr(t, 'DE'):
				s += '\td = min(d, ' + t.glsl() + ');\n'
			else:
				raise Exception("Invalid type in transformation queue")
		s += '\treturn d;\n'
		s += '}\n'
		s += 'vec4 col_' + self.name + '(vec4 p) {\n'
		#s += '\tvec4 o = p;\n'
		#s += '\tvec4 orbit = vec4(1e20);\n'
		s += '\tvec4 col = vec4(1e20);\n'
		s += '\tvec4 newCol;\n'
		for t in self.trans:
			if hasattr(t, 'fold'):
				s += t.glsl()
			elif hasattr(t, 'DE'):
				s += '\tnewCol = ' + t.glsl_col() + ';\n'
				s += '\tif (newCol.w < col.w) { col = newCol; }\n'
			else:
				raise Exception("Invalid type in transformation queue")
			#if t.__class__.__name__ == 'FoldScaleTranslate':
			#	s += '\torbit.xyz = min(orbit.xyz, abs(p.xyz));\n'
		s += '\treturn col;\n'
		s += '}\n'
		return s

class MultiObject:
	def __init__(self, objs, blend=0.0, name='main'):
		self.objs = objs
		self.name = name
		self.blend = blend

	def DE(self, origin):
		return min(obj.DE(origin) for obj in self.objs)

	def NP(self, origin):
		best_n = None
		best_d = 1e20
		for obj in self.objs:
			n = obj.NP(origin)
			d = norm_sq(n - origin[:3])
			if d < best_d:
				best_d = d
				best_n = n
		return best_n

	def glsl(self):
		s = 'float de_' + self.name + '(vec4 p) {\n'
		s += '\tfloat d = 99999.0;\n'
		for obj in self.objs:
			s += '\td = min(d, de_' + obj.name + '(p));\n'
		s += '\treturn d;\n'
		s += '}\n'
		s += 'vec4 col_' + self.name + '(vec4 p) {\n'
		s += '\tvec4 col = vec4(99999.0);\n'
		s += '\tvec4 newCol;\n'
		for obj in self.objs:
			s += '\tnewCol = col_' + obj.name + '(p);\n'
			s += '\tif (newCol.w < col.w) { col = newCol; }\n'
		s += '\treturn col;\n'
		s += '}\n'
		return s
		return s