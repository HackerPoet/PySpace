from ctypes import *
from OpenGL.GL import *
from pyspace.util import _PYSPACE_GLOBAL_VARS, to_vec3, to_str
from pyspace import camera
import os

class Shader:
	def __init__(self, obj):
		self.obj = obj
		self.keys = {}

	def set(self, key, val):
		if key in _PYSPACE_GLOBAL_VARS:
			cur_val = _PYSPACE_GLOBAL_VARS[key]
			if type(val) is float and type(cur_val) is not float:
				val = to_vec3(val)
		_PYSPACE_GLOBAL_VARS[key] = val
		if key in self.keys:
			key_id = self.keys[key]
			if type(val) is float:
				glUniform1f(key_id, val)
			else:
				glUniform3fv(key_id, 1, val)

	def get(self, key):
		if key in _PYSPACE_GLOBAL_VARS:
			return _PYSPACE_GLOBAL_VARS[key]
		return None

	def compile(self, cam):
		#Open the shader source
		vert_dir = os.path.join(os.path.dirname(__file__), 'vert.glsl')
		frag_dir = os.path.join(os.path.dirname(__file__), 'frag.glsl')
		v_shader = open(vert_dir).read()
		f_shader = open(frag_dir).read()

		#Create code for all defines
		define_code = ''
		for k in cam.params:
			param = to_str(cam.params[k])
			define_code += '#define ' + k + ' ' + param + '\n'
		define_code += '#define DE de_' + self.obj.name + '\n'
		define_code += '#define COL col_' + self.obj.name + '\n'
		split_ix = f_shader.index('// [/pydefine]')
		f_shader = f_shader[:split_ix] + define_code + f_shader[split_ix:]

		#Create code for all keys
		var_code = ''
		for k in _PYSPACE_GLOBAL_VARS:
			typ = 'float' if type(_PYSPACE_GLOBAL_VARS[k]) is float else 'vec3'
			var_code += 'uniform ' + typ + ' _' + k + ';\n'

		split_ix = f_shader.index('// [/pyvars]')
		f_shader = f_shader[:split_ix] + var_code + f_shader[split_ix:]

		#Create code for all pyspace
		nested_refs = {}
		space_code = self.obj.compiled(nested_refs)

		#Also add forward declarations
		forwared_decl_code = ''
		for k in nested_refs:
			forwared_decl_code += nested_refs[k].forwared_decl()
		space_code = forwared_decl_code + space_code

		split_ix = f_shader.index('// [/pyspace]')
		f_shader = f_shader[:split_ix] + space_code + f_shader[split_ix:]

		#Debugging the shader
		#open('frag_gen.glsl', 'w').write(f_shader)

		#Compile program
		program = self.compile_program(v_shader, f_shader)

		#Get variable ids for each uniform
		for k in _PYSPACE_GLOBAL_VARS:
			self.keys[k] = glGetUniformLocation(program, '_' + k);

		#Return the program
		return program

	def compile_shader(self, source, shader_type):
		shader = glCreateShader(shader_type)
		glShaderSource(shader, source)
		glCompileShader(shader)

		status = c_int()
		glGetShaderiv(shader, GL_COMPILE_STATUS, byref(status))
		if not status.value:
			self.print_log(shader)
			glDeleteShader(shader)
			raise ValueError('Shader compilation failed')
		return shader

	def compile_program(self, vertex_source, fragment_source):
		vertex_shader = None
		fragment_shader = None
		program = glCreateProgram()

		if vertex_source:
			print("Compiling Vertex Shader...")
			vertex_shader = self.compile_shader(vertex_source, GL_VERTEX_SHADER)
			glAttachShader(program, vertex_shader)
		if fragment_source:
			print("Compiling Fragment Shader...")
			fragment_shader = self.compile_shader(fragment_source, GL_FRAGMENT_SHADER)
			glAttachShader(program, fragment_shader)

		glLinkProgram(program)

		if vertex_shader:
			glDeleteShader(vertex_shader)
		if fragment_shader:
			glDeleteShader(fragment_shader)

		return program

	def print_log(self, shader):
		length = c_int()
		glGetShaderiv(shader, GL_INFO_LOG_LENGTH, byref(length))

		if length.value > 0:
			log = create_string_buffer(length.value)
			print(glGetShaderInfoLog(shader))
