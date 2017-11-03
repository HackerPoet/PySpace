#version 400

uniform mat4 iMat;
uniform mat4 iPrevMat;
uniform vec2 iResolution;
uniform float iSlider;

// [pyvars]
// [/pyvars]

#define NUM_ITERS 24
#define NUM_STEPS 800
#define MIN_DIST 0.00001
#define MAX_DIST 100.0
#define FOCAL_DIST 2.0
#define BG_LVL vec3(0.6,0.6,0.9)
#define LIGHT_COL vec3(1.0,0.9,0.6)

#define DE de_main
#define COL col_main
#define DOF 0.0
#define FOCAL_LENGTH 0.5
#define SHADOW_MULT 0.5
#define AA_LEVEL 2
#define USE_SHADDOW true
#define AO_LEVEL 0.01
#define REFLECTION_LEVEL 0
#define REFLECTION_BLEND 0.5
#define MOTION_BLUR_LEVEL 1
#define DIFFUSE_SHADE 1.0
#define AMBIENT_LIGHT 0.0
#define MY_SIZE 0.02
#define USE_ORTHOGONAL false
#define ZOOM 2.0

const vec4 LIGHT_DIR = vec4(0.36, 0.80, 0.48, 0.0);

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
void planeFold(inout vec4 z, vec3 n, float d=0.0) {
	z.xyz -= 2.0 * min(0.0, dot(z.xyz, n) - d) * n;
}
void absFold(inout vec4 z) {
	z.xyz = abs(z.xyz);
}
void sphereFold(inout vec4 z, float minR, float maxR) {
	float r2 = dot(z.xyz, z.xyz);
	z *= max(maxR / max(minR, r2), 1.0);
	z.w += 1.0;
}
void boxFold(inout vec4 z, float foldLimit) {
	z.xyz = clamp(z.xyz, -foldLimit, foldLimit) * 2.0 - z.xyz;
}
void sierpinskiFold(inout vec4 z) {
	z.xy -= min(z.x + z.y, 0.0);
	z.xz -= min(z.x + z.z, 0.0);
	z.yz -= min(z.y + z.z, 0.0);
}
void sort(inout vec4 z) {
	float mn = min(min(z.x, z.y), z.z);
	float mx = max(max(z.x, z.y), z.z);
	z.xyz = vec3(mx, z.x + z.y + z.z - mx - mn, mn);
}
void rotX(inout vec4 z, float a) {
	float s = sin(a); float c = cos(a);
	z.yz = vec2(c*z.y + s*z.z, c*z.z - s*z.y);
}
void rotY(inout vec4 z, float a) {
	float s = sin(a); float c = cos(a);
	z.xz = vec2(c*z.x - s*z.z, c*z.z + s*z.x);
}
void rotZ(inout vec4 z, float a) {
	float s = sin(a); float c = cos(a);
	z.xy = vec2(c*z.x + s*z.y, c*z.y - s*z.x);
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
//   Complex distance estimators
//
//##########################################
float de_sierpinski_tetrahedron(vec4 z) {
	vec4 ones = vec4(1.0, 1.0, 1.0, 0.0);
	for(int i = 0; i < 8; i++) {
		sierpinskiFold(z);
		z = z * 2.0 - ones;
	}
	return de_tetrahedron(z, 1.0);
}
float de_menger(vec4 z) {
	for(int i = 0; i < 12; i++) {
		absFold(z);
		sort(z);
		z   *= 3.0;
		z.x -= 2.0;
		z.y -= 2.0;
		z.z  = 1.0 - abs(z.z - 1.0);
	}
	return de_box(z, vec3(1.0));
}
float de_mandelbox(vec4 z) {
	vec4 offset = z;
	vec4 scale = vec4(2.0);
	scale.w = abs(scale.w);
	for (int n = 0; n < NUM_ITERS; n++) {
		boxFold(z, 1.0);
		sphereFold(z, 0.5, 1.0);
		z = scale*z + offset;
	}
	return de_box(z, vec3(0.0));
}
float de_test(vec4 p) {
	return de_inf_cross(p,0.1);
}

//##########################################
//
//   Coloring
//
//##########################################
vec3 col_mandelbox(vec4 offset) {
	vec3 minZ = vec3(99999.0);
	vec4 z = offset;
	vec4 scale = vec4(2.0);
	scale.w = abs(scale.w);
	for (int n = 0; n < NUM_ITERS; n++) {
		boxFold(z, 1.0);
		sphereFold(z, 0.5, 1.0);
		z = scale*z + offset;
		minZ = min(minZ, abs(z.xyz) / (n + 1));
	}
	return minZ * 2.0;
}
vec4 col_none(vec4 z) {
	return vec4(abs(z.xyz), 0.0);
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
vec4 ray_march(inout vec4 p, vec4 ray) {
	//March the ray
	float d = MIN_DIST;
	float s = 0;
	float td = 0.0;
	float min_d = 1.0;
	for (; s < NUM_STEPS; s += 1.0) {
		vec4 orig = p;
		float prev_d = d;
		d = DE(p);
		if (d < MIN_DIST) {
			s += d / MIN_DIST;
			break;
		} else if (td > MAX_DIST) {
			break;
		}
		td += d;
		p += ray * d;
		min_d = min(min_d, 16*d/td);
	}
	return vec4(d, s, td, min_d);
}

vec3 scene(inout vec4 origin, inout vec4 ray, float distToCenter) {
	//Trace the ray
	vec4 p = origin;
	vec4 d_s_td_m = ray_march(p, ray);
	float d = d_s_td_m.x;
	float s = d_s_td_m.y;
	float td = d_s_td_m.z;

	//Determine the color for this pixel
	vec3 col = BG_LVL * distToCenter;
	if (d < MIN_DIST) {
		//Get the surface normal
		vec4 e = vec4(MIN_DIST, 0.0, 0.0, 0.0);
		vec3 n = vec3(DE(p + e.xyyy) - DE(p - e.xyyy),
					  DE(p + e.yxyy) - DE(p - e.yxyy),
					  DE(p + e.yyxy) - DE(p - e.yyxy));
		n /= (length(n) + 1e-20);
		vec3 reflected = ray.xyz - 2.0*dot(ray.xyz, n) * n;

		//Get diffuse lighting
		float light = (1.0 - dot(n, LIGHT_DIR.xyz)) * 0.5;
		light = 1.0 - DIFFUSE_SHADE * light;

		//Get coloring
		vec3 closest = COL(p).xyz;
		col = light / (closest + 1.0);

		//Get if this point is in shadow
		float k = 1.0;
		if (USE_SHADDOW) {
			vec4 light_pt = p;
			light_pt.xyz += n * MIN_DIST * 10;
			vec4 rm = ray_march(light_pt, LIGHT_DIR);
			k = rm.w * min(rm.z, 1.0);
		}
		if (k < 0.001) {
			col *= SHADOW_MULT;
		} else {
			//Get specular
			float specular = max(dot(reflected, LIGHT_DIR.xyz), 0.0);
			specular = pow(specular, 40);

			//Blend shadow and specular
			col = k*min(col + specular*LIGHT_COL, 1.0) + (1.0 - k)*SHADOW_MULT*col;
		}

		//Add small amount of ambient occlusion
		float a = 1.0 / (1.0 + s * AO_LEVEL);
		col = a*col + (1.0 - a)*BG_LVL;

		//Add any ambient light at the end
		col += AMBIENT_LIGHT;

		//Set up the reflection
		origin = p + vec4(n * MIN_DIST * 100, 0.0);
		ray = vec4(reflected, 0.0);
	} else {
		//Background specular
		float specular = max(dot(ray.xyz, LIGHT_DIR.xyz), 0.0);
		specular = pow(specular, 80);
		col = min(col + specular*LIGHT_COL, 1.0);
	}

	return col;
}

void main() {
	vec3 col = vec3(0.0);
	for (int k = 0; k < MOTION_BLUR_LEVEL; ++k) {
		for (int i = 0; i < AA_LEVEL; ++i) {
			for (int j = 0; j < AA_LEVEL; ++j) {
				mat4 mat = iMat;
				float a = float(k) / MOTION_BLUR_LEVEL;
				mat[3] = iPrevMat[3]*a + iMat[3]*(1.0 - a);

				vec2 delta = vec2(i, j) / AA_LEVEL;
				vec4 dxy = vec4(delta.x, delta.y, 0.0, 0.0) * DOF / iResolution.x;

				vec2 screen_pos = (gl_FragCoord.xy + delta) / iResolution.xy;
				vec2 uv = 2*screen_pos - 1;
				uv.x *= iResolution.x / iResolution.y;

				//Convert screen coordinate to 3d ray
				vec4 ray;
				if (USE_ORTHOGONAL) {
					ray = vec4(0.0, 0.0, -FOCAL_DIST, 0.0);
					ray = mat * normalize(ray);
				} else {
					ray = normalize(vec4(uv.x, uv.y, -FOCAL_DIST, 0.0));
					ray = mat * normalize(ray * FOCAL_LENGTH + dxy);
				}

				//Cast the first ray
				vec4 p = mat[3];
				//p += mat * vec4(0,0,2,0);
				if (USE_ORTHOGONAL) {
					p += mat * vec4(uv.x, uv.y, 0.0, 0.0) * ZOOM;
				} else {
					p -= mat * dxy;
				}

				//Reflect light if needed
				float distToCenter = 1.0 - 0.5 * length(gl_FragCoord.xy / iResolution.xy - 0.5);
				vec3 newCol = vec3(0.0);
				vec4 prevRay = ray;
				a = 1.0;
				for (int r = 0; r < REFLECTION_LEVEL + 1; ++r) {
					vec3 newRef = a * scene(p, ray, distToCenter);
					if (ray != prevRay && r < REFLECTION_LEVEL) {
						newCol += newRef * (1 - REFLECTION_BLEND);
					} else {
						newCol += newRef;
						break;
					}
					a *= REFLECTION_BLEND;
				}

				col += newCol;
			}
		}
	}

	gl_FragColor.rgb = col / (AA_LEVEL * AA_LEVEL * MOTION_BLUR_LEVEL);
}
