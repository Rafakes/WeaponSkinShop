"""Create Cobalt and Cyberpunk model shaders from the installed vanilla shader.

The derivative retains the game's lighting, UV, alpha and instancing paths.
"""
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
VANILLA = Path(r'C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media\shaders')
TARGET = PROJECT / 'Contents/mods/WeaponSkinShop/42.19/media/shaders'
TARGET.mkdir(parents=True, exist_ok=True)

COBALT = '''// Cobalt cosmetic variant. Works on the original UV atlas without moving pixels.
// Preserve near-black recesses, blue-tint the visible midtones and keep their shading.
vec3 wssCobalt(vec3 base)
{
    float luminance = dot(base, vec3(0.299, 0.587, 0.114));
    float strength = 0.88 * smoothstep(0.055, 0.20, luminance);
    vec3 blue = vec3(0.11, 0.30, 0.64) * (0.35 + 1.45 * luminance);
    return mix(base, min(blue, vec3(1.0)), strength);
}

'''

CYBERPUNK = '''// Cyberpunk premium finish: graphite, iridescent violet and neon traces.
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

'''

for finish, function, expression in (
        ('Cobalt', COBALT, 'wssCobalt(texSample.xyz)'),
        ('Cyberpunk', CYBERPUNK, 'wssCyberpunk(texSample.xyz, texCoords)')):
    for suffix in ('_static.vert', '_static_instanced.vert', '.vert', '_instanced.vert'):
        (TARGET / ('WSS_' + finish + suffix)).write_bytes((VANILLA / ('basicEffect' + suffix)).read_bytes())
    for suffix in ('.frag', '_instanced.frag'):
        shader = (VANILLA / ('basicEffect' + suffix)).read_text(encoding='utf-8')
        assert shader.count('void main()') == 1 and shader.count('vec3 col = texSample.xyz;') == 1
        shader = shader.replace('void main()', function + 'void main()', 1)
        shader = shader.replace('vec3 col = texSample.xyz;', 'vec3 col = ' + expression + ';', 1)
        (TARGET / ('WSS_' + finish + suffix)).write_text(shader, encoding='utf-8')
print('Generated twelve shader files from the installed vanilla basicEffect shader.')
