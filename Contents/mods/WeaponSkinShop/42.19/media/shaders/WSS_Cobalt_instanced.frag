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

// Cobalt cosmetic variant. Works on the original UV atlas without moving pixels.
// Preserve near-black recesses, blue-tint the visible midtones and keep their shading.
vec3 wssCobalt(vec3 base)
{
    float luminance = dot(base, vec3(0.299, 0.587, 0.114));
    float strength = 0.88 * smoothstep(0.055, 0.20, luminance);
    vec3 blue = vec3(0.11, 0.30, 0.64) * (0.35 + 1.45 * luminance);
    return mix(base, min(blue, vec3(1.0)), strength);
}

void main()
{
	GET_INSTANCED_STRUCT(inst);

	vec3 normal = normalize(vertNormal);

	vec4 texSample = SAMPLE_TEXTURE_ARRAY(texCoords, inst);

	if (texSample.w < 0.01)
	    discard;

	vec3 col = wssCobalt(texSample.xyz);

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
