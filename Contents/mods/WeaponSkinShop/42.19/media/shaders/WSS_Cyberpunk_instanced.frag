#version 430 core

#include "util/instancing"

in vec3 vertColour;
in vec3 vertNormal;
in vec2 texCoords;

out vec4 colour;

DECLARE_INSTANCING_FRAG

BEGIN_INSTANCING

vec3 LightDirection[5];

vec3 LightColour[5];

mat4 MatrixPalette[60];

mat4 transform;
mat4 mvp;

vec2 UVScale;
float targetDepth;
float DepthBias;

vec3 TintColour;
float HighResDepthMultiplier; // 0.5 when drawing models to double-sized chunk textures

vec3 AmbientColour;
float Alpha;

float LightingAmount;
float HueChange;
bool FlipNormal;

END_INSTANCING

#include "util/math"
#include "util/hueShift"

// Cyberpunk premium finish: graphite, iridescent violet and neon traces.
// Sample the existing UV atlas to retain baked highlights and original geometry.
vec3 wssCyberpunk(vec3 base, vec2 uv)
{
    float luminance = dot(base, vec3(0.299, 0.587, 0.114));
    float surface = smoothstep(0.045, 0.17, luminance);
    vec3 graphite = base * vec3(0.31, 0.33, 0.45);
    float panel = smoothstep(0.32, 0.48, fract(uv.x * 3.0 + uv.y * 1.75));
    vec3 violet = vec3(0.25, 0.055, 0.41) * (0.35 + 1.8 * luminance);
    vec3 finish = mix(graphite, violet, 0.68 * panel * surface);

    float diagonal = fract(uv.x * 7.0 + uv.y * 5.0);
    float cyanTrace = 1.0 - smoothstep(0.008, 0.026, abs(diagonal - 0.49));
    cyanTrace *= surface * step(0.16, fract(uv.y * 7.0));
    float magentaTrace = 1.0 - smoothstep(0.007, 0.018,
                                         abs(fract(uv.x * 4.0 - uv.y * 3.0) - 0.35));
    magentaTrace *= surface * 0.45;
    finish = mix(finish, vec3(0.03, 0.89, 1.0), cyanTrace * 0.85);
    finish = mix(finish, vec3(0.88, 0.07, 0.75), magentaTrace);
    return min(finish, vec3(1.0));
}

void main()
{
	GET_INSTANCED_STRUCT(inst);

	vec3 normal = normalize(vertNormal);

	vec4 texSample = SAMPLE_TEXTURE_ARRAY(texCoords, inst);

	if (texSample.w < 0.01)
	    discard;

	vec3 col = wssCyberpunk(texSample.xyz, texCoords);

    if (inst.HueChange != 0.0)
        col = hueShift(col, inst.HueChange);

	const float QuantiseLevels = 8.0;
	vec3 lighting = vec3(0.0);

    for (int i = 0; i < 5; i++)
    {
	    vec3 dir = normalize(inst.LightDirection[i]);
	    float dotProd = max(dot(normal, dir), 0.0);
	    lighting += inst.LightColour[i] * dotProd;
    }

	lighting += inst.AmbientColour;
	lighting = min(lighting, vec3(1.0));

	col = col * inst.TintColour * lighting;

	colour = vec4(col * vertColour, texSample.w) * inst.Alpha;
}
