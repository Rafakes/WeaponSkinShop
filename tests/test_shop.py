"""Run with Python + lupa. Real Lua modules; mock only the game's Java/Lua boundary."""
from pathlib import Path
import json
import re
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
LUA = ROOT / 'Contents/mods/WeaponSkinShop/42.19/media/lua'
MEDIA = ROOT / 'Contents/mods/WeaponSkinShop/42.19/media'
GUN_MEDIA = Path(r'C:\Program Files (x86)\Steam\steamapps\workshop\content\108600\3722134990\mods\GunsOfMarz\42.16\media')
CORE = Path(r'C:\Users\rafa_\Zomboid\Workshop\Server Shop\Contents\mods\Server Shop\42.20\media\lua\server\ServerShopBalanceCore.lua')

FIXTURE = r'''
clock = 10000
stores = {}
messages = {}
function isServer() return true end
function isClient() return false end
function getTimestampMs() return clock end
function instanceof(obj, class) return type(obj) == 'table' and obj.class == class end
function javaList(values)
    return { size = function() return #values end, get = function(_, i) return values[i + 1] end }
end
function container(items)
    return { getItems = function() return javaList(items) end }
end
Events = { OnClientCommand = { Add = function(fn) handler = fn end } }
ModData = { getOrCreate = function(name)
    if databaseDown then return nil end
    stores[name] = stores[name] or {}
    return stores[name]
end }
function sendServerCommand(player, module, command, args)
    if networkDown then error('transport unavailable') end
    messages[#messages + 1] = { player = player, module = module, command = command, args = args }
end
function player(name)
    local p = { name = name, md = {}, items = {}, dead = false }
    p.inv = container(p.items)
    function p:getInventory() return self.inv end
    function p:getUsername() return self.name end
    function p:getOnlineID() return self.name == 'alice' and 1 or 2 end
    function p:getModData() return self.md end
    function p:isDead() return self.dead end
    function p:getX() return self.x or 0 end
    function p:getY() return 0 end
    return p
end
function weapon(id, fullType)
    local w = { class = 'HandWeapon', id = id, fullType = fullType or 'MarzGuns.AK47',
        md = {}, sprite = 'MarzGuns.AK47', condition = 7, ammo = 23, jammed = true,
        parts = { scope = 'MarzGuns.Scope' }, syncs = 0 }
    function w:getID() return self.id end
    function w:getFullType() return self.fullType end
    function w:isRanged() return true end
    function w:getModData() return self.md end
    function w:getWeaponSprite() return self.sprite end
    function w:setWeaponSprite(v) self.sprite = v end
    function w:setWorldStaticModel(v)
        if self.failVisual then error('model failed') end
        self.md.worldStaticModel = v
    end
    function w:syncItemFields() self.syncs = self.syncs + 1 end
    return w
end
alice, bob = player('alice'), player('bob')
bob.x = 150
online = { alice, bob }
function getOnlinePlayers() return javaList(online) end
gun = weapon(123)
alice.items[1] = gun
stores.ServerShopBalance = { alice = 200, bob = 99 }
function request(player, command, id, skin, extra)
    clock = clock + 1000
    local args = extra or {}
    args.itemId, args.requestId, args.skinId = id, clock, skin
    handler('WeaponSkinShop', command, player, args)
end
function lastState()
    for i = #messages, 1, -1 do
        if messages[i].command == 'state' then return messages[i].args end
    end
end
'''

def runtime(core=False):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(FIXTURE)
    paths = ';'.join(str(LUA / scope / '?.lua').replace('\\', '/') for scope in ('shared', 'server', 'client'))
    lua.globals().package.path = paths
    if core:
        lua.globals().package.loaded.ServerShopBalanceCore = lua.execute(CORE.read_text(encoding='utf-8-sig'))
    lua.execute('require "WSS/Server"')
    return lua

def check(lua, code):
    lua.execute(code)

def suite(core=False):
    lua = runtime(core)
    checks = [
        ('status and authoritative balance', '''request(alice,'status',123)
            assert(lastState().balance == 200 and lastState().rows[1].price == 100)'''),
        ('purchase ignores forged price/owner/balance', '''request(alice,'apply',123,'cobalt',{price=-1000,username='bob',balance=999999})
            assert(stores.ServerShopBalance.alice == 100 and stores.ServerShopBalance.bob == 99)
            assert(gun.sprite == 'WeaponSkinShop.AK47_Cobalt' and gun.md.WSS_skin == 'cobalt')
            assert(stores.WeaponSkinShopUnlocks_v1.alice['MarzGuns.AK47'].cobalt)
            assert(gun.id == 123 and gun.condition == 7 and gun.ammo == 23 and gun.jammed)
            assert(gun.parts.scope == 'MarzGuns.Scope')'''),
        ('idempotent replay', '''request(alice,'apply',123,'cobalt')
            assert(stores.ServerShopBalance.alice == 100)'''),
        ('premium has separate price and unlock', '''request(alice,'status',123)
            assert(lastState().rows[2].id == 'cyberpunk' and lastState().rows[2].price == 350)
            request(alice,'apply',123,'cyberpunk')
            assert(lastState().code == 'Funds' and stores.ServerShopBalance.alice == 100)
            assert(not stores.WeaponSkinShopUnlocks_v1.alice['MarzGuns.AK47'].cyberpunk)'''),
        ('free original and reapply', '''request(alice,'apply',123,'original')
            assert(gun.sprite == 'MarzGuns.AK47' and gun.md.worldStaticModel == nil)
            request(alice,'apply',123,'cobalt')
            assert(stores.ServerShopBalance.alice == 100)'''),
        ('same account second weapon in backpack', '''gun2 = weapon(124)
            alice.items[2] = {class='InventoryContainer', getID=function() return 900 end,
                getInventory=function() return container({gun2}) end}
            request(alice,'apply',124,'cobalt')
            assert(gun2.md.WSS_skin == 'cobalt' and stores.ServerShopBalance.alice == 100)'''),
        ('other player cannot buy with someone else weapon', '''request(bob,'apply',123,'cobalt')
            assert(lastState().code == 'Missing' and stores.ServerShopBalance.bob == 99)'''),
        ('insufficient funds', '''bobgun = weapon(125); bob.items[1] = bobgun
            request(bob,'apply',125,'cobalt')
            assert(lastState().code == 'Funds' and bobgun.md.WSS_skin == nil)'''),
        ('unknown skin', '''request(alice,'apply',123,'free_hack')
            assert(lastState().code == 'Invalid' and stores.ServerShopBalance.alice == 100)'''),
        ('unknown gun catalog', '''alice.items[3] = weapon(126,'MarzGuns.UNLISTED')
            request(alice,'status',126)
            assert(lastState().code == 'Empty' and #lastState().rows == 0)'''),
        ('dropped weapon cannot be changed', '''table.remove(alice.items, 1)
            request(alice,'apply',123,'original')
            assert(lastState().code == 'Missing' and gun.md.WSS_skin == 'cobalt')
            table.insert(alice.items, 1, gun)'''),
        ('invalid payloads and dead player', '''local n = #messages
            handler('WeaponSkinShop','apply',alice,{itemId=0/0,requestId=1,skinId='cobalt'})
            handler('WeaponSkinShop','apply',alice,{itemId=math.huge,requestId=1})
            handler('WeaponSkinShop','apply',alice,'invalid')
            alice.dead=true; request(alice,'apply',123,'original'); alice.dead=false
            assert(#messages == n)'''),
        ('rate limit', '''request(alice,'status',123)
            local n = #messages
            handler('WeaponSkinShop','status',alice,{itemId=123,requestId=clock})
            assert(#messages == n)'''),
        ('visual failure rolls back and does not unlock', '''stores.ServerShopBalance.bob = 200
            bobgun.failVisual = true
            request(bob,'apply',125,'cobalt')
            assert(lastState().code == 'Unavailable' and stores.ServerShopBalance.bob == 200)
            assert(bobgun.sprite == 'MarzGuns.AK47' and bobgun.md.WSS_skin == nil)
            assert(not stores.WeaponSkinShopUnlocks_v1.bob['MarzGuns.AK47'].cobalt)
            bobgun.failVisual = false'''),
        ('database unavailable fails closed', '''databaseDown=true
            request(alice,'apply',123,'original')
            assert(lastState().code == 'Unavailable' and gun.md.WSS_skin == 'cobalt')
            databaseDown=false'''),
        ('no global visual broadcast', '''messages={}; request(alice,'apply',123,'original')
            for _,m in ipairs(messages) do assert(m.player ~= bob) end
            bob.x=1; messages={}; request(alice,'apply',123,'cobalt')
            local saw=false
            for _,m in ipairs(messages) do if m.player == bob and m.command == 'visual' then saw=true end end
            assert(saw)'''),
        ('Lua reload retains persistent unlock and balance', '''package.loaded['WSS/Server']=nil
            require 'WSS/Server'; request(alice,'status',123)
            assert(lastState().balance == 100 and lastState().rows[1].owned)'''),
        ('premium purchase and switch without repeat charge', '''stores.ServerShopBalance.alice = 500
            request(alice,'apply',123,'cyberpunk')
            assert(lastState().code == 'Applied' and stores.ServerShopBalance.alice == 150)
            assert(gun.sprite == 'WeaponSkinShop.AK47_Cyberpunk' and gun.md.WSS_skin == 'cyberpunk')
            local owned = stores.WeaponSkinShopUnlocks_v1.alice['MarzGuns.AK47']
            assert(owned.cobalt and owned.cyberpunk)
            request(alice,'apply',123,'cobalt')
            request(alice,'apply',123,'cyberpunk')
            assert(stores.ServerShopBalance.alice == 150)'''),
    ]
    for name, code in checks:
        check(lua, code)
        print('PASS', 'core' if core else '42.19', name)
    return len(checks)

if __name__ == '__main__':
    compiler = LuaRuntime()
    for path in LUA.rglob('*.lua'):
        compiler.execute('assert(loadstring(...))', path.read_text(encoding='utf-8-sig'))
    locales = [json.loads((LUA/'shared/Translate'/lang/'UI.json').read_text(encoding='utf-8')) for lang in ('EN','PT','PTBR')]
    assert all(d.keys() == locales[0].keys() for d in locales)
    references = set()
    for path in LUA.rglob('*.lua'):
        references.update(re.findall(r'"(UI_WSS_[A-Za-z]+)"', path.read_text(encoding='utf-8')))
    assert references <= locales[0].keys(), references - locales[0].keys()
    inventory = json.loads((ROOT/'weapons.json').read_text(encoding='utf-8'))['weapons']
    assert len(inventory) == 70 and len({e['fullType'] for e in inventory}) == 70
    models = (MEDIA/'scripts/WSS_models.txt').read_text(encoding='utf-8')
    catalog = (LUA/'shared/WSS/Catalog.lua').read_text(encoding='utf-8')
    assert models.count('{') == models.count('}')
    assert len(re.findall(r'(?m)^\s*model\s+\w+_Cobalt\s*\{', models)) == 70
    assert len(re.findall(r'(?m)^\s*model\s+\w+_Cyberpunk\s*\{', models)) == 70
    assert models.count('shader   = WSS_Cobalt,') == 69
    assert models.count('shader   = WSS_Cyberpunk,') == 70
    assert 'texture  = WSS/AK47_Cobalt,' in models
    assert len(re.findall(r'\["MarzGuns\.[A-Za-z0-9_]+"\] = \{', catalog)) == 70
    assert catalog.count('id = "cyberpunk"') == 70
    for entry in inventory:
        assert f'model {entry["item"]}_Cobalt {{' in models
        assert f'model {entry["item"]}_Cyberpunk {{' in models
        assert f'["{entry["fullType"]}"] = {{' in catalog
        assert (GUN_MEDIA/'textures'/(entry['sourceTexture']+'.png')).is_file()
        assert (GUN_MEDIA/'textures'/entry['sourceIcon']).is_file()
    shaders = MEDIA/'shaders'
    for finish, call in (('Cobalt', 'wssCobalt(texSample.xyz)'),
                         ('Cyberpunk', 'wssCyberpunk(texSample.xyz, texCoords)')):
        for suffix in ('.vert', '_static.vert', '_instanced.vert', '_static_instanced.vert', '.frag', '_instanced.frag'):
            assert (shaders/('WSS_'+finish+suffix)).is_file()
        for suffix in ('.frag', '_instanced.frag'):
            source = (shaders/('WSS_'+finish+suffix)).read_text(encoding='utf-8')
            assert source.count(call) == 1 and source.count('void main()') == 1
    assert (MEDIA/'ui/WSS/AK47_Cyberpunk.png').is_file()
    count = suite()
    if CORE.exists(): count += suite(core=True)
    print(f'{count} scenario checks passed; all Lua parses as 5.1; EN/PT/PTBR coverage matches.')
    print('All 70 catalog/icon/source texture links, 140 models and twelve shader files validated.')
