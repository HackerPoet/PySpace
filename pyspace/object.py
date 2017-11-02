import numpy as np
from util import *

class Object:
	def __init__(self, geo, name='main'):
		self.folds = []
		self.geo = geo
		self.name = name

	def add_fold(self, fold):
		self.folds.append(fold)

	def DE(self, origin):
		p = np.copy(origin)
		for fold in self.folds:
			if hasattr(fold, 'o'):
				fold.o = origin
			fold.fold(p)
		return self.geo.DE(p)

	def NP(self, origin):
		undo = []
		p = np.copy(origin)
		for fold in self.folds:
			if hasattr(fold, 'o'):
				fold.o = origin
			undo.append((fold, np.copy(p)))
			fold.fold(p)
		n = self.geo.NP(p)
		for fold, p in undo[::-1]:
			fold.unfold(p, n)
		return n
	
	def glsl(self):
		s = 'float de_' + self.name + '(vec4 p) {\n'
		s += '\tvec4 o = p;\n'
		for fold in self.folds:
			s += fold.glsl()
		s += '\treturn ' + self.geo.glsl()
		s += '}\n'
		s += 'vec4 col_' + self.name + '(vec4 p) {\n'
		s += '\tvec4 o = p;\n'
		s += '\tvec4 orbit = vec4(99999.0);\n'
		for fold in self.folds:
			s += fold.glsl()
			if fold.__class__.__name__ == 'FoldScaleTranslate':
				s += '\torbit.xyz = min(orbit.xyz, abs(p.xyz));\n'
		s += '\torbit.w = ' + self.geo.glsl()
		s += '\treturn orbit;\n'
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
		best_d = 9999999.0
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