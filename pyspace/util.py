import numpy as np

def normalize(x):
	return x / np.linalg.norm(x)

def norm_sq(v):
	return np.dot(v,v)

def norm(v):
	return np.linalg.norm(v)

def get_sub_keys(v):
	if type(v) is not tuple and type(v) is not list:
		return []
	return [k for k in v if type(k) is str]

def to_vec3(v):
	if isinstance(v, (float, int)):
		return np.array([v, v, v], dtype=np.float32)
	elif len(get_sub_keys(v)) > 0:
		return v
	else:
		return np.array([v[0], v[1], v[2]], dtype=np.float32)

def to_str(x):
	if type(x) is bool:
		return "1" if x else "0"
	elif isinstance(x, (list, tuple)):
		return vec3_str(x)
	else:
		return str(x)

def float_str(x):
	if type(x) is str:
		return '_' + x
	else:
		return str(x)

def vec3_str(v):
	if type(v) is str:
		return '_' + v
	elif isinstance(v, (float, int)):
		return 'vec3(' + str(v) + ')'
	else:
		return 'vec3(' + float_str(v[0]) + ',' + float_str(v[1]) + ',' + float_str(v[2]) + ')'

def vec3_eq(v, val):
	if type(v) is str:
		return False
	for i in range(3):
		if v[i] != val[i]:
			return False
	return True

def smin(a, b, k):
	h = min(max(0.5 + 0.5*(b - a)/k, 0.0), 1.0)
	return b*(1 - h) + a*h - k*h*(1.0 - h)

def get_global(k):
	if type(k) is str:
		return _PYSPACE_GLOBAL_VARS[k]
	elif type(k) is tuple or type(k) is list:
		return np.array([get_global(i) for i in k], dtype=np.float32)
	else:
		return k

def set_global_float(k):
	if type(k) is str:
		_PYSPACE_GLOBAL_VARS[k] = 0.0
	return k

def set_global_vec3(k):
	if type(k) is str:
		_PYSPACE_GLOBAL_VARS[k] = to_vec3((0,0,0))
		return k
	elif isinstance(k, (float, int)):
		return to_vec3(k)
	else:
		sk = get_sub_keys(k)
		for i in sk:
			_PYSPACE_GLOBAL_VARS[i] = 0.0
		return to_vec3(k)

def cond_offset(p):
	if type(p) is str or np.count_nonzero(p) > 0:
		return ' - vec4(' + vec3_str(p) + ', 0)'
	return ''

def make_color(geo):
	if type(geo.color) is tuple or type(geo.color) is np.ndarray:
		return 'vec4(' + vec3_str(geo.color) + ', ' + geo.glsl() + ')'
	elif geo.color == 'orbit' or geo.color == 'o':
		return 'vec4(orbit, ' + geo.glsl() + ')'
	else:
		raise Exception("Invalid coloring type")

_PYSPACE_GLOBAL_VARS = {}
