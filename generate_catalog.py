"""Inventory GunsOfMarz firearms and derive additive skin model/catalog files.

This script never modifies the dependency. Other guns use a runtime cobalt shader
over their original UV atlas, which avoids altering or duplicating those atlases.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
GUNS = Path(r'C:\Program Files (x86)\Steam\steamapps\workshop\content\108600\3722134990\mods\GunsOfMarz\42.16\media')
MEDIA = PROJECT / 'Contents/mods/WeaponSkinShop/42.19/media'
ITEM_DIR = GUNS / 'scripts/MarzWeapons/items/weapons'
MODEL_DIR = GUNS / 'scripts/MarzWeapons/models/weapons'
TEXTURES = GUNS / 'textures'


def blocks(text: str, keyword: str):
    pattern = re.compile(r'(?m)^\s*' + keyword + r'\s+([A-Za-z0-9_]+)\s*\{')
    for match in pattern.finditer(text):
        depth = 1
        cursor = match.end()
        while depth and cursor < len(text):
            depth += (text[cursor] == '{') - (text[cursor] == '}')
            cursor += 1
        if depth != 0:
            raise ValueError(f'Unbalanced block: {match.group(1)}')
        yield match.group(1), text[match.start():cursor]


def value(body: str, key: str):
    found = re.search(r'(?m)^\s*' + re.escape(key) + r'\s*=\s*([^,\s]+)', body)
    return found.group(1) if found else None


model_blocks = {}
for file in MODEL_DIR.glob('*.txt'):
    for name, body in blocks(file.read_text(encoding='utf-8-sig'), 'model'):
        model_blocks[name] = body

categories = [
    ('pistols', 'Pistolas'), ('revolvers', 'Revólveres'), ('smgs', 'Submetralhadoras'),
    ('shotguns', 'Escopetas'), ('assault_rifles', 'Fuzis de assalto'),
    ('battle_rifles', 'Fuzis de batalha'), ('semi_rifles', 'Fuzis semiautomáticos'),
    ('bolt_rifles', 'Fuzis de ferrolho'), ('lever_rifles', 'Fuzis de alavanca'),
    ('lmgs', 'Metralhadoras'), ('launchers', 'Lançadores'),
    ('underbarrel', 'Módulos acoplados'),
]
entries = []
by_category = defaultdict(list)
for category, title in categories:
    for file in ITEM_DIR.glob(category + '.txt'):
        for name, body in blocks(file.read_text(encoding='utf-8-sig'), 'item'):
            if value(body, 'Ranged') != 'true' and value(body, 'IsAimedFirearm') != 'true':
                continue
            original_model = value(body, 'WeaponSprite') or 'MarzGuns.' + name
            model_name = original_model.split('.')[-1]
            model = model_blocks.get(model_name)
            if not model:
                raise ValueError(f'Missing source model: {name} / {model_name}')
            texture = value(model, 'texture')
            if not texture or not (TEXTURES / (texture + '.png')).is_file():
                raise ValueError(f'Missing texture: {name} / {texture}')
            icon = value(body, 'Icon') or name
            entry = {
                'category': title, 'item': name, 'fullType': 'MarzGuns.' + name,
                'originalModel': original_model, 'model': 'WeaponSkinShop.' + name + '_Cobalt',
                'textureName': texture.rsplit('/', 1)[-1], 'sourceTexture': texture,
                'sourceIcon': 'item_' + icon + '.png',
            }
            entries.append(entry)
            by_category[title].append(entry)

assert len(entries) == 70, f'Expected 70 ranged weapons, found {len(entries)}'
assert len({e['fullType'] for e in entries}) == 70
assert len({e['sourceTexture'] for e in entries}) == 68

models_out = ['module WeaponSkinShop {']
for entry in entries:
    source_block = model_blocks[entry['originalModel'].split('.')[-1]]
    for finish in ('Cobalt', 'Cyberpunk'):
        block = re.sub(r'\bmodel\s+\w+\s*\{', 'model ' + entry['item'] + '_' + finish + ' {', source_block, count=1)
        if entry['item'] == 'AK47' and finish == 'Cobalt':
            block = re.sub(r'(?m)^(\s*texture\s*=\s*)[^,]+,',
                           lambda match: match.group(1) + 'WSS/AK47_Cobalt,', block, count=1)
        else:
            block = re.sub(r'(?m)^(\s*texture\s*=\s*[^,]+,)',
                           lambda match: match.group(1) + '\n        shader   = WSS_' + finish + ',', block, count=1)
        models_out.append(block)
models_out.append('}')
(MEDIA / 'scripts/WSS_models.txt').write_text('\n'.join(models_out) + '\n', encoding='utf-8')

catalog = ['-- Generated from GunsOfMarz B42.16 item/model definitions. Keep persistent IDs stable.',
           'WeaponSkinShop = WeaponSkinShop or {}', 'local WSS = WeaponSkinShop',
           'WSS.MODULE = "WeaponSkinShop"', 'WSS.catalog = {']
for entry in entries:
    original_icon = 'media/textures/' + entry['sourceIcon']
    cobalt_preview = 'media/ui/WSS/AK47_Cobalt.png' if entry['item'] == 'AK47' else original_icon
    cyber_preview = 'media/ui/WSS/AK47_Cyberpunk.png' if entry['item'] == 'AK47' else original_icon
    catalog.extend([
        '    ["' + entry['fullType'] + '"] = {',
        '        originalModel = "' + entry['originalModel'] + '",',
        '        originalIcon = "' + original_icon + '",',
        '        skins = {',
        '            { id = "cobalt", nameKey = "UI_WSS_Cobalt", price = 100,',
        '              model = "' + entry['model'] + '",',
        '              preview = "' + cobalt_preview + '",',
        '              previewTint = ' + ('false' if entry['item'] == 'AK47' else '"cobalt"') + ' },',
        '            { id = "cyberpunk", nameKey = "UI_WSS_Cyberpunk", price = 350,',
        '              model = "WeaponSkinShop.' + entry['item'] + '_Cyberpunk",',
        '              preview = "' + cyber_preview + '",',
        '              previewTint = ' + ('false' if entry['item'] == 'AK47' else '"cyberpunk"') + ' },',
        '        },', '    },',
    ])
catalog.extend(['}', ''])
old_catalog = (MEDIA / 'lua/shared/WSS/Catalog.lua').read_text(encoding='utf-8')
tail = old_catalog[old_catalog.index('function WSS.getSkin'):]
(MEDIA / 'lua/shared/WSS/Catalog.lua').write_text('\n'.join(catalog) + tail, encoding='utf-8')

manifest = {'totalItems': len(entries), 'skinFamilies': ['cobalt', 'cyberpunk'],
            'totalSkins': len(entries) * 2, 'uniqueTextures': 68, 'weapons': entries}
(PROJECT / 'weapons.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
document = ['# Armas com skins Cobalto e Cyberpunk', '',
            '70 armas de fogo identificadas nos scripts de GunsOfMarz 42.16. Cada entrada do catálogo tem Cobalto (100 zPoints) e Cyberpunk Néon (350 zPoints), com desbloqueios separados. A AK-47 Cobalto mantém o atlas anterior; os outros acabamentos usam modelos individuais e shaders sobre o atlas UV original. Os modelos preservam os encaixes.', '']
for category, _ in categories:
    title = next((pt for key, pt in categories if key == category), category)
    category_entries = by_category[title]
    if category_entries:
        document.extend(['## ' + title + ' (' + str(len(category_entries)) + ')', ''])
        document.extend('- `' + entry['fullType'] + '`' for entry in category_entries)
        document.append('')
document.extend(['Facas e granadas foram excluídas porque não são armas de fogo com modelo equipado desta loja.', ''])
(PROJECT / 'ARMAS.md').write_text('\n'.join(document), encoding='utf-8')
print(f"Generated catalog for {len(entries)} weapons, {len(set(e['sourceTexture'] for e in entries))} UV textures.")
