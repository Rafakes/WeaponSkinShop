if not isServer() then return end
local WSS = require "WSS/Catalog"
local Balance = require "WSS/Balance"
local limits = setmetatable({}, { __mode = "k" })

local function finiteInteger(n)
    return type(n) == "number" and n == n and n ~= math.huge and n ~= -math.huge and n == math.floor(n)
end

local function unlocksFor(player, fullType)
    if not ModData or not ModData.getOrCreate then return nil end
    local key = player:getUsername()
    if not key or key == "" then return nil end
    local store = ModData.getOrCreate("WeaponSkinShopUnlocks_v1")
    if not store then return nil end
    store[key] = store[key] or {}
    store[key][fullType] = store[key][fullType] or {}
    return store[key][fullType]
end

local function reply(player, args, code, item)
    local payload = { requestId = args.requestId, itemId = args.itemId,
        playerId = player:getOnlineID(), code = code, balance = Balance.read(player) or -1 }
    if item then
        payload.fullType = item:getFullType()
        payload.active = item:getModData().WSS_skin or "original"
        payload.rows = {}
        local entry = WSS.catalog[item:getFullType()]
        local owned = entry and unlocksFor(player, item:getFullType())
        if entry and owned then
            for i, skin in ipairs(entry.skins) do
                payload.rows[i] = { id = skin.id, price = skin.price, owned = owned[skin.id] == true }
            end
        end
    end
    sendServerCommand(player, WSS.MODULE, "state", payload)
end

local function syncVisual(player, item, skinId)
    -- syncItemFields includes item ModData/worldStaticModel but NOT weaponSprite.
    item:syncItemFields()
    local payload = { playerId = player:getOnlineID(), itemId = item:getID(),
        fullType = item:getFullType(), skinId = skinId }
    sendServerCommand(player, WSS.MODULE, "visual", payload)
    local players = getOnlinePlayers()
    for i = 0, players:size() - 1 do
        local other = players:get(i)
        local dx, dy = other:getX() - player:getX(), other:getY() - player:getY()
        if other ~= player and dx * dx + dy * dy <= 100 * 100 then
            sendServerCommand(other, WSS.MODULE, "visual", payload)
        end
    end
end

local function onCommand(module, command, player, args)
    if module ~= WSS.MODULE or (command ~= "status" and command ~= "apply") then return end
    if not player or player:isDead() or type(args) ~= "table" then return end
    if not finiteInteger(args.itemId) or not finiteInteger(args.requestId) then return end
    local now = getTimestampMs()
    local rate = limits[player] or {}
    limits[player] = rate
    local interval = command == "apply" and 750 or 500
    if rate[command] and now - rate[command] < interval then return end
    rate[command] = now
    local item = WSS.findItem(player:getInventory(), args.itemId)
    if not WSS.isGun(item) then reply(player, args, "Missing"); return end
    local entry = WSS.catalog[item:getFullType()]
    if not entry then reply(player, args, "Empty", item); return end
    local owned, balance = unlocksFor(player, item:getFullType()), Balance.read(player)
    if not owned or balance == nil then reply(player, args, "Unavailable"); return end
    if command == "status" then reply(player, args, "Ready", item); return end
    if type(args.skinId) ~= "string" or #args.skinId > 48 then reply(player, args, "Invalid", item); return end
    local skin = WSS.getSkin(item:getFullType(), args.skinId)
    if args.skinId ~= "original" and not skin then reply(player, args, "Invalid", item); return end
    local price = skin and not owned[skin.id] and skin.price or 0
    if not finiteInteger(price) or price < 0 then reply(player, args, "Invalid", item); return end
    if balance < price then reply(player, args, "Funds", item); return end
    -- Check every required mutation API before touching money.
    if not item.setWeaponSprite or not item.setWorldStaticModel or not item.syncItemFields then
        reply(player, args, "Unavailable", item); return
    end
    local md = item:getModData()
    local before = { sprite = item:getWeaponSprite(), world = md.worldStaticModel,
        skin = md.WSS_skin, balance = balance, owned = skin and owned[skin.id] }
    local success, err = pcall(function()
        assert(WSS.applyVisual(item, args.skinId), "visual rejected")
        md.WSS_skin = args.skinId
        assert(Balance.write(player, balance - price, "purchase"), "balance write failed")
        if skin then owned[skin.id] = true end
    end)
    if not success then
        item:setWeaponSprite(before.sprite)
        md.worldStaticModel, md.WSS_skin = before.world, before.skin
        if skin then owned[skin.id] = before.owned end
        Balance.write(player, before.balance, "refund")
        print("[WeaponSkinShop] Transaction rolled back: " .. tostring(err))
        reply(player, args, "Unavailable", item)
        return
    end
    -- Transport failures must not refund an already committed unlock/application.
    local sent, syncError = pcall(syncVisual, player, item, args.skinId)
    if not sent then print("[WeaponSkinShop] Sync retry on next status: " .. tostring(syncError)) end
    Balance.sync(player)
    print(string.format("[WeaponSkinShop] user=%s item=%s id=%s skin=%s cost=%s balance=%s",
        player:getUsername(), item:getFullType(), tostring(item:getID()), args.skinId, tostring(price), tostring(balance - price)))
    reply(player, args, "Applied", item)
end

Events.OnClientCommand.Add(onCommand)
return { onCommand = onCommand }
