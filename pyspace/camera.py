
class Camera:
	def __init__(self):
		self.params = {}

		# Number of additional samples on each axis to average and improve image quality.
		# NOTE: This will slow down rendering quadratically.
		# Recommended Range: 1 to 8 (integer)
		self.params['ANTIALIASING_SAMPLES'] = 1

		# The strength of the ambient occlusion.
		# Recommended Range: 0.0 to 0.05
		self.params['AMBIENT_OCCLUSION_STRENGTH'] = 0.01

		# Represents the maximum RGB color shift that can result from ambient occlusion.
		# Typically use positive values for 'glow' effects and negative for 'darkness'.
		# Recommended Range: All values between -1.0 and 1.0
		self.params['AMBIENT_OCCLUSION_COLOR_DELTA'] = (0.8, 0.8, 0.8)

		# Color of the background when the ray doesn't hit anything
		# Recommended Range: All values between 0.0 and 1.0
		self.params['BACKGROUND_COLOR'] = (0.6, 0.6, 0.9)

		# The strength of the depth of field effect.
		# NOTE: ANTIALIASING_SAMPLES must be larger than 1 to use depth of field effects.
		# Recommended Range: 0.0 to 20.0
		self.params['DEPTH_OF_FIELD_STRENGTH'] = 0.0

		# The distance from the camera where objects will appear in focus.
		# NOTE: ANTIALIASING_SAMPLES must be larger than 1 to use depth of field effects.
		# Recommended Range: 0.0 to 100.0
		self.params['DEPTH_OF_FIELD_DISTANCE'] = 1.0

		# Determines if diffuse lighting should be enabled.
		# NOTE: This flag will be ignored if DIFFUSE_ENHANCED_ENABLED is set.
		# NOTE: SHADOW_DARKNESS is also used to change diffuse intensity.
		self.params['DIFFUSE_ENABLED'] = False

		# This is a 'less correct' but more aesthetically pleasing diffuse variant.
		# NOTE: This will override the DIFFUSE_ENABLED flag.
		# NOTE: SHADOW_DARKNESS is also used to change diffuse intensity.
		self.params['DIFFUSE_ENHANCED_ENABLED'] = True

		# Amount of light captured by the camera.
		# Can be used to increase/decrease brightness in case pixels are over-saturated.
		# Recommended Range: 0.1 to 10.0
		self.params['EXPOSURE'] = 1.0

		# Field of view of the camera in degrees
		# NOTE: This will have no effect if ORTHOGONAL_PROJECTION or ODS is enabled.
		# Recommended Range: 20.0 to 120.0
		self.params['FIELD_OF_VIEW'] = 60.0

		# When enabled, adds a distance-based fog to the scene
		# NOTE: Fog strength is determined by MAX_DIST and fog color is always BACKGROUND_COLOR.
		# NOTE: If enabled, you usually also want VIGNETTE_FOREGROUND=True and SUN_ENABLED=False.
		self.params['FOG_ENABLED'] = False

		# When enabled, adds object glow to the background layer.
		self.params['GLOW_ENABLED'] = False

		# Represents the maximum RGB color shift that can result from glow.
		# Recommended Range: All values between -1.0 and 1.0
		self.params['GLOW_COLOR_DELTA'] = (-0.2, 0.5, -0.2)

		# The sharpness of the glow.
		# Recommended Range: 1.0 to 100.0
		self.params['GLOW_SHARPNESS'] = 4.0

		# Color of the sunlight in RGB format.
		# Recommended Range: All values between 0.0 and 1.0
		self.params['LIGHT_COLOR'] = (1.0, 0.9, 0.6)

		# Direction of the sunlight.
		# NOTE: This must be a normalized quantity (magnitude = 1.0)
		self.params['LIGHT_DIRECTION'] = (-0.36, 0.48, 0.80)

		# Number of additional renderings between frames.
		# NOTE: This will slow down rendering linearly.
		# Recommended Range: 0 to 10 (integer)
		self.params['MOTION_BLUR_LEVEL'] = 0

		# Maximum number of marches before a ray is considered a non-intersection.
		# Recommended Range: 10 to 10000 (integer)
		self.params['MAX_MARCHES'] = 1000

		# Maximum distance before a ray is considered a non-intersection.
		# Recommended Range: 0.5 to 200.0
		self.params['MAX_DIST'] = 50.0

		# Minimum march distance until a ray is considered intersecting.
		# Recommended Range: 0.000001 to 0.01
		self.params['MIN_DIST'] = 0.00001

		# If true will render an omnidirectional stereo 360 projection.
		self.params['ODS'] = False

		# Determines if the projection view should be orthographic instead of perspective.
		self.params['ORTHOGONAL_PROJECTION'] = False

		# When ORTHOGONAL_PROJECTION is enabled, this will determine the size of the view.
		# NOTE: Larger numbers mean the view will appear more zoomed out.
		# Recommended Range: 0.5 to 50.0
		self.params['ORTHOGONAL_ZOOM'] = 5.0

		# Number of additional bounces after a ray collides with the geometry.
		# Recommended Range: 0 to 8 (integer)
		self.params['REFLECTION_LEVEL'] = 0

		# Proportion of light lost each time a reflection occurs.
		# NOTE: This will only be relevant if REFLECTION_LEVEL is greater than 0.
		# Recommended Range: 0.25 to 1.0
		self.params['REFLECTION_ATTENUATION'] = 0.6

		# When enabled, uses an additional ray march to the light source to check for shadows.
		self.params['SHADOWS_ENABLED'] = True

		# Proportion of the light that is 'blocked' by the shadow or diffuse light.
		# Recommended Range: 0.0 to 1.0
		self.params['SHADOW_DARKNESS'] = 0.8

		# How sharp the shadows should appear.
		# Recommended Range: 1.0 to 100.0
		self.params['SHADOW_SHARPNESS'] = 16.0

		# Used to determine how sharp specular reflections are.
		# NOTE: This is the 'shininess' parameter in the phong illumination model.
		# NOTE: To disable specular highlights, use the value 0.
		# Recommended Range: 0 to 1000 (integer)
		self.params['SPECULAR_HIGHLIGHT'] = 40

		# Determines if the sun should be drawn in the sky.
		self.params['SUN_ENABLED'] = True

		# Size of the sun to draw in the sky.
		# NOTE: This only takes effect when SUN_ENABLED is enabled.
		# Recommended Range: 0.0001 to 0.05
		self.params['SUN_SIZE'] = 0.005

		# How sharp the sun should appear in the sky.
		# NOTE: This only takes effect when SUN_ENABLED is enabled.
		# Recommended Range: 0.1 to 10.0
		self.params['SUN_SHARPNESS'] = 2.0

		# When enabled, vignetting will also effect foreground objects.
		self.params['VIGNETTE_FOREGROUND'] = False

		# The strength of the vignetting effect.
		# Recommended Range: 0.0 to 1.5
		self.params['VIGNETTE_STRENGTH'] = 0.5

	def __getitem__(self, k):
		return self.params[k]

	def __setitem__(self, k, x):
		self.params[k] = x
