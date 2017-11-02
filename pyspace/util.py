import numpy as np

def normalize(x):
	return x / np.linalg.norm(x)

def to_vec3(v):
	return np.array([v[0], v[1], v[2]], dtype=np.float32)

def vec3_str(v):
	if type(v) is str:
		return v
	else:
		return 'vec3(' + str(v[0]) + ',' + str(v[1]) + ',' + str(v[2]) + ')'

def norm_sq(v):
	return np.dot(v,v)

def smin(a, b, k):
	h = min(max(0.5 + 0.5*(b - a)/k, 0.0), 1.0)
	return b*(1 - h) + a*h - k*h*(1.0 - h)

def get_global(k):
	if type(k) is str:
		return _PYSPACE_GLOBAL_VARS[k]
	else:
		return k

def set_global_float(k):
	if type(k) is str:
		k = '_' + k
		_PYSPACE_GLOBAL_VARS[k] = 0.0
	return k

def set_global_vec3(k):
	if type(k) is str:
		k = '_' + k
		_PYSPACE_GLOBAL_VARS[k] = to_vec3((0,0,0))
		return k
	else:
		return to_vec3(k)

def cond_offset(p):
	if type(p) is str or np.count_nonzero(p) > 0:
		return ' - vec4(' + vec3_str(p) + ', 0)'
	return ''

_PYSPACE_GLOBAL_VARS = {}
