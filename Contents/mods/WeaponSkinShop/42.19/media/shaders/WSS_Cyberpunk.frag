#version 110

varying vec3 vertColour; 
varying vec3 vertNormal;
varying vec2 texCoords;

uniform sampler2D Texture;
uniform float Alpha;
uniform float LightingAmount;

uniform vec3 TintColour;

uniform vec3 AmbientColour;
uniform vec3 Light0Direction;
uniform vec3 Light0Colour;
uniform vec3 Light1Direction;
uniform vec3 Light1Colour;
uniform vec3 Light2Direction;
uniform vec3 Light2Colour;
uniform vec3 Light3Direction;
uniform vec3 Light3Colour;
uniform vec3 Light4Direction;
uniform vec3 Light4Colour;
uniform float HueChange;

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
	vec3 normal = normalize(vertNormal);

	vec4 texSample = texture2D(Texture, texCoords);

	if(texSample.w < 0.01)
	{
	    discard;
	}

	vec3 col = wssCyberpunk(texSample.xyz, texCoords);

    float dotprod;
    if(HueChange != 0.0)
    {
        col = hueShift(col, HueChange);
    }

	const float QuantiseLevels = 8.0;
	vec3 lighting = vec3(0.0);

	dotprod = max(dot(normal, normalize(Light0Direction)), 0.0);
	
	lighting += Light0Colour * dotprod;

	dotprod = max(dot(normal, normalize(Light1Direction)), 0.0);
	
	lighting += Light1Colour * dotprod;

	dotprod = max(dot(normal, normalize(Light2Direction)), 0.0);
	
	lighting += Light2Colour * dotprod;

	dotprod = max(dot(normal, normalize(Light3Direction)), 0.0);
	
	lighting += Light3Colour * dotprod;

	dotprod = max(dot(normal, normalize(Light4Direction)), 0.0);
	
	lighting += Light4Colour * dotprod;

	lighting += AmbientColour;
	lighting.x = min(lighting.x, 1.0);
	lighting.y = min(lighting.y, 1.0);
	lighting.z = min(lighting.z, 1.0);

	vec3 tintColour = TintColour;
	col = vec3(col.x * tintColour.x * lighting.x, col.y * tintColour.y * lighting.y, col.z * tintColour.z * lighting.z);

    vec4 fragCol = vec4(Alpha * col * vertColour, Alpha * texSample.w);
	gl_FragColor = fragCol;
}
