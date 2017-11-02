from ctypes import *
from OpenGL.GL import *
from util import _PYSPACE_GLOBAL_VARS

class Shader:
	def __init__(self):
		self.objs = []
		self.keys = {}

	def add(self, obj):
		self.objs.append(obj)

	def set(self, key, val):
		key = '_' + key
		_PYSPACE_GLOBAL_VARS[key] = val
		if key in self.keys:
			key_id = self.keys[key]
			if type(val) is float:
				glUniform1f(key_id, val)
			else:
				glUniform3fv(key_id, 1, val)

	def compile(self):
		#Open the shader source
		v_shader = open('vert.glsl').read()
		f_shader = open('frag.glsl').read()

		#Create code for all keys
		var_code = ''
		for k in _PYSPACE_GLOBAL_VARS:
			typ = 'float' if type(_PYSPACE_GLOBAL_VARS[k]) is float else 'vec3'
			var_code += 'uniform ' + typ + ' ' + k + ';\n'

		split_ix = f_shader.index('// [/pyvars]')
		f_shader = f_shader[:split_ix] + var_code + f_shader[split_ix:]

		#Create code for all pyspace
		space_code = ''
		for obj in self.objs:
			space_code += obj.compiled()

		split_ix = f_shader.index('// [/pyspace]')
		f_shader = f_shader[:split_ix] + space_code + f_shader[split_ix:]

		#Debugging ONLY
		open('frag_gen.glsl', 'w').write(f_shader)

		#Compile program
		program = self.compile_program(v_shader, f_shader)

		#Get variable ids for each uniform
		for k in _PYSPACE_GLOBAL_VARS:
			self.keys[k] = glGetUniformLocation(program, k);

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
			raise ValueError, 'Shader compilation failed'
		return shader

	def compile_program(self, vertex_source, fragment_source):
		vertex_shader = None
		fragment_shader = None
		program = glCreateProgram()

		if vertex_source:
			print "Compiling Vertex Shader..."
			vertex_shader = self.compile_shader(vertex_source, GL_VERTEX_SHADER)
			glAttachShader(program, vertex_shader)
		if fragment_source:
			print "Compiling Fragment Shader..."
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
			print glGetShaderInfoLog(shader)
