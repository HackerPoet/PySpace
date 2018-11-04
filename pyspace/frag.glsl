#version 400
#define M_PI 3.14159265358979

uniform mat4 iMat;
uniform mat4 iPrevMat;
uniform vec2 iResolution;
uniform float iIPD;

// [pydefine]
// [/pydefine]

// [pyvars]
// [/pyvars]

const float FOCAL_DIST = 1.0 / tan(M_PI * FIELD_OF_VIEW / 360.0);

float rand(float s, float minV, float maxV) {
	float r = sin(s*s*27.12345 + 1000.9876 / (s*s + 1e-5));
	return (r + 1.0) * 0.5 * (maxV - minV) + minV;
}
float smin(float a, float b, float k) {
	float h = clamp(0.5 + 0.5*(b-a)/k, 0.0, 1.0 );
	return mix(b, a, h) - k*h*(1.0 - h);
	//return -log(exp(-a/k) + exp(-b/k))*k;
}

//##########################################
//
//   Space folding functions
//
//##########################################
void planeFold(inout vec4 z, vec3 n, float d) {
	z.xyz -= 2.0 * min(0.0, dot(z.xyz, n) - d) * n;
}
void absFold(inout vec4 z, vec3 c) {
	z.xyz = abs(z.xyz - c) + c;
}
void sierpinskiFold(inout vec4 z) {
	z.xy -= min(z.x + z.y, 0.0);
	z.xz -= min(z.x + z.z, 0.0);
	z.yz -= min(z.y + z.z, 0.0);
}
void mengerFold(inout vec4 z) {
	float a = min(z.x - z.y, 0.0);
	z.x -= a;
	z.y += a;
	a = min(z.x - z.z, 0.0);
	z.x -= a;
	z.z += a;
	a = min(z.y - z.z, 0.0);
	z.y -= a;
	z.z += a;
}
void sphereFold(inout vec4 z, float minR, float maxR) {
	float r2 = dot(z.xyz, z.xyz);
	z *= max(maxR / max(minR, r2), 1.0);
}
void boxFold(inout vec4 z, vec3 r) {
	z.xyz = clamp(z.xyz, -r, r) * 2.0 - z.xyz;
}
void rotX(inout vec4 z, float s, float c) {
	z.yz = vec2(c*z.y + s*z.z, c*z.z - s*z.y);
}
void rotY(inout vec4 z, float s, float c) {
	z.xz = vec2(c*z.x - s*z.z, c*z.z + s*z.x);
}
void rotZ(inout vec4 z, float s, float c) {
	z.xy = vec2(c*z.x + s*z.y, c*z.y - s*z.x);
}
void rotX(inout vec4 z, float a) {
	rotX(z, sin(a), cos(a));
}
void rotY(inout vec4 z, float a) {
	rotY(z, sin(a), cos(a));
}
void rotZ(inout vec4 z, float a) {
	rotZ(z, sin(a), cos(a));
}

//##########################################
//
//   Primative distance estimators
//
//##########################################
float de_sphere(vec4 p, float r) {
	return (length(p.xyz) - r) / p.w;
}
float de_box(vec4 p, vec3 s) {
	vec3 a = abs(p.xyz) - s;
	return (min(max(max(a.x, a.y), a.z), 0.0) + length(max(a, 0.0))) / p.w;
}
float de_tetrahedron(vec4 p, float r) {
	float md = max(max(-p.x - p.y - p.z, p.x + p.y - p.z),
				   max(-p.x + p.y + p.z, p.x - p.y + p.z));
	return (md - r) / (p.w * sqrt(3.0));
}
float de_inf_cross(vec4 p, float r) {
	vec3 q = p.xyz * p.xyz;
	return (sqrt(min(min(q.x + q.y, q.x + q.z), q.y + q.z)) - r) / p.w;
}
float de_inf_cross_xy(vec4 p, float r) {
	vec3 q = p.xyz * p.xyz;
	return (sqrt(min(q.x, q.y) + q.z) - r) / p.w;
}
float de_inf_line(vec4 p, vec3 n, float r) {
	return (length(p.xyz - n*dot(p.xyz, n)) - r) / p.w;
}

//##########################################
//
//   Compiled
//
//##########################################

// [pyspace]
// [/pyspace]

//##########################################
//
//   Main code
//
//##########################################
vec4 ray_march(inout vec4 p, vec4 ray, float sharpness) {
	//March the ray
	float d = MIN_DIST;
	float s = 0.0;
	float td = 0.0;
	float min_d = 1.0;
	for (; s < MAX_MARCHES; s += 1.0) {
		d = DE(p);
		if (d < MIN_DIST) {
			s += d / MIN_DIST;
			break;
		} else if (td > MAX_DIST) {
			break;
		}
		td += d;
		p += ray * d;
		min_d = min(min_d, sharpness * d / td);
	}
	return vec4(d, s, td, min_d);
}
vec4 ray_march(inout vec4 p, vec3 ray, float sharpness) {
	return ray_march(p, vec4(ray, 0.0), sharpness);
}

vec3 scene(inout vec4 origin, inout vec4 ray, float vignette) {
	//Trace the ray
	vec4 p = origin;
	vec4 d_s_td_m = ray_march(p, ray, GLOW_SHARPNESS);
	float d = d_s_td_m.x;
	float s = d_s_td_m.y;
	float td = d_s_td_m.z;
	float m = d_s_td_m.w;

	//Determine the color for this pixel
	vec3 col = vec3(0.0);
	if (d < MIN_DIST) {
		//Get the surface normal
		vec4 e = vec4(MIN_DIST, 0.0, 0.0, 0.0);
		vec3 n = vec3(DE(p + e.xyyy) - DE(p - e.xyyy),
					  DE(p + e.yxyy) - DE(p - e.yxyy),
					  DE(p + e.yyxy) - DE(p - e.yyxy));
		n /= (length(n));
		vec3 reflected = ray.xyz - 2.0*dot(ray.xyz, n) * n;

		//Get coloring
		vec3 orig_col = clamp(COL(p).xyz, 0.0, 1.0);

		//Get if this point is in shadow
		float k = 1.0;
		#if SHADOWS_ENABLED
			vec4 light_pt = p;
			light_pt.xyz += n * MIN_DIST * 10;
			vec4 rm = ray_march(light_pt, LIGHT_DIRECTION, SHADOW_SHARPNESS);
			k = rm.w * min(rm.z, 1.0);
		#endif

		//Get specular
		#if SPECULAR_HIGHLIGHT > 0
			float specular = max(dot(reflected, LIGHT_DIRECTION), 0.0);
			specular = pow(specular, SPECULAR_HIGHLIGHT);
			col += specular * LIGHT_COLOR * k;
		#endif

		//Get diffuse lighting
		#if DIFFUSE_ENHANCED_ENABLED
			k = min(k, SHADOW_DARKNESS * 0.5 * (dot(n, LIGHT_DIRECTION) - 1.0) + 1.0);
		#elif DIFFUSE_ENABLED
			k = min(k, dot(n, LIGHT_DIRECTION));
		#endif

		//Don't make shadows entirely dark
		k = max(k, 1.0 - SHADOW_DARKNESS);
		col += orig_col * LIGHT_COLOR * k;

		//Add small amount of ambient occlusion
		float a = 1.0 / (1.0 + s * AMBIENT_OCCLUSION_STRENGTH);
		col += (1.0 - a) * AMBIENT_OCCLUSION_COLOR_DELTA;

		//Add fog effects
		#if FOG_ENABLED
			a = td / MAX_DIST;
			col = (1.0 - a) * col + a * BACKGROUND_COLOR;
		#endif

		//Set up the reflection
		origin = p + vec4(n * MIN_DIST * 100, 0.0);
		ray = vec4(reflected, 0.0);

		//Apply vignette if needed
		#if VIGNETTE_FOREGROUND
			col *= vignette;
		#endif
	} else {
		//Ray missed, start with solid background color
		col += BACKGROUND_COLOR;

		//Apply glow
		#if GLOW_ENABLED
			col += (1.0 - m) * (1.0 - m) * GLOW_COLOR_DELTA;
		#endif

		col *= vignette;
		//Background specular
		#if SUN_ENABLED
			float sun_spec = dot(ray.xyz, LIGHT_DIRECTION) - 1.0 + SUN_SIZE;
			sun_spec = min(exp(sun_spec * SUN_SHARPNESS / SUN_SIZE), 1.0);
			col += LIGHT_COLOR * sun_spec;
		#endif
	}

	return col;
}

void main() {
	vec3 col = vec3(0.0);
	for (int k = 0; k < MOTION_BLUR_LEVEL + 1; ++k) {
		for (int i = 0; i < ANTIALIASING_SAMPLES; ++i) {
			for (int j = 0; j < ANTIALIASING_SAMPLES; ++j) {
				mat4 mat = iMat;
				#if MOTION_BLUR_LEVEL > 0
					float a = float(k) / (MOTION_BLUR_LEVEL + 1);
					mat = iPrevMat*a + iMat*(1.0 - a);
				#endif

				vec2 delta = vec2(i, j) / ANTIALIASING_SAMPLES;
				vec2 delta2 = vec2(rand(i,0,1), rand(j+0.1,0,1));
				vec4 dxy = vec4(delta2.x, delta2.y, 0.0, 0.0) * DEPTH_OF_FIELD_STRENGTH / iResolution.x;

				#if ODS
					//Get the normalized screen coordinate
					vec2 screen_pos;
					float scale;
					vec2 ods_coord = vec2(gl_FragCoord.x, gl_FragCoord.y * 2);
					if (ods_coord.y < iResolution.y) {
						screen_pos = (ods_coord + delta) / iResolution.xy;
						scale = -iIPD*0.5;
					} else {
						screen_pos = (ods_coord - vec2(0, iResolution.y) + delta) / iResolution.xy;
						scale = iIPD*0.5;
					}
					float theta = -2*M_PI*screen_pos.x;
					float phi = -0.5*M_PI + screen_pos.y*M_PI;
					scale *= cos(phi);
					vec4 p = mat[3] - mat * vec4(cos(theta) * scale, 0, sin(theta) * scale, 0);
					vec4 ray = mat * vec4(sin(theta)*cos(phi), sin(phi), cos(theta)*cos(phi), 0);
				#else
					//Get normalized screen coordinate
					vec2 screen_pos = (gl_FragCoord.xy + delta) / iResolution.xy;
					vec2 uv = 2*screen_pos - 1;
					uv.x *= iResolution.x / iResolution.y;

					//Convert screen coordinate to 3d ray
					#if ORTHOGONAL_PROJECTION
						vec4 ray = vec4(0.0, 0.0, -FOCAL_DIST, 0.0);
						ray = mat * normalize(ray);
					#else
						vec4 ray = normalize(vec4(uv.x, uv.y, -FOCAL_DIST, 0.0));
						ray = mat * normalize(ray * DEPTH_OF_FIELD_DISTANCE + dxy);
					#endif

					//Cast the first ray
					#if ORTHOGONAL_PROJECTION
						vec4 p = mat[3] + mat * vec4(uv.x, uv.y, 0.0, 0.0) * ORTHOGONAL_ZOOM;
					#else
						vec4 p = mat[3] - mat * dxy;
					#endif
				#endif

				//Reflect light if needed
				float vignette = 1.0 - VIGNETTE_STRENGTH * length(screen_pos - 0.5);
				#if REFLECTION_LEVEL > 0
					vec3 newCol = vec3(0.0);
					vec4 prevRay = ray;
					float ref_alpha = 1.0;
					for (int r = 0; r < REFLECTION_LEVEL + 1; ++r) {
						ref_alpha *= REFLECTION_ATTENUATION;
						newCol += ref_alpha * scene(p, ray, vignette);
						if (ray == prevRay || r >= REFLECTION_LEVEL) {
							break;
						}
					}
					col += newCol;
				#else
					col += scene(p, ray, vignette);
				#endif

			}
		}
	}

	col = col * EXPOSURE / (ANTIALIASING_SAMPLES * ANTIALIASING_SAMPLES * (MOTION_BLUR_LEVEL + 1));
	gl_FragColor.rgb = clamp(col, 0.0, 1.0);
}
