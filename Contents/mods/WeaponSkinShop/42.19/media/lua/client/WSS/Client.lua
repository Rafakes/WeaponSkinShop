local WSS = require "WSS/Catalog"
WSS.windows = WSS.windows or {}
WSS.sequence = 0

local function restoreVisual(player, item)
    if not WSS.isGun(item) then return end
    local id = item:getModData().WSS_skin
    local entry = WSS.catalog[item:getFullType()]
    if not id or not entry then return end
    local skin = WSS.getSkin(item:getFullType(), id)
    local model = skin and skin.model or (id == "original" and entry.originalModel)
    if model and item:getWeaponSprite() ~= model then
        WSS.applyVisual(item, id)
        player:resetEquippedHandsModels()
    end
end

local function onServerCommand(module, command, args)
    if module ~= WSS.MODULE or type(args) ~= "table" then return end
    if command == "state" then
        for _, window in pairs(WSS.windows) do
            if window.player:getOnlineID() == args.playerId and window.item:getID() == args.itemId
                and window.requestId == args.requestId then
                -- The response also repairs the owner's sprite after a lost visual packet.
                if args.active and args.fullType == window.item:getFullType() then
                    window.item:getModData().WSS_skin = args.active
                    WSS.applyVisual(window.item, args.active)
                    window.player:resetEquippedHandsModels()
                end
                window:receive(args)
            end
        end
    elseif command == "visual" then
        local player = getPlayerByOnlineID(args.playerId)
        if not player then return end
        local item = WSS.findItem(player:getInventory(), args.itemId)
        -- Remote player inventory can be partial; hands are independently replicated.
        if not item then
            local primary, secondary = player:getPrimaryHandItem(), player:getSecondaryHandItem()
            if primary and primary:getID() == args.itemId then item = primary end
            if secondary and secondary:getID() == args.itemId then item = secondary end
        end
        if WSS.isGun(item) and item:getFullType() == args.fullType and WSS.applyVisual(item, args.skinId) then
            item:getModData().WSS_skin = args.skinId
            player:resetEquippedHandsModels()
        end
    end
end

-- No network polling: only inspect two held items per loaded player once a second.
-- This repairs late equipment replication and skins received while outside the area.
local nextVisualCheck = 0
local function onTick()
    local now = getTimestampMs()
    if now < nextVisualCheck then return end
    nextVisualCheck = now + 1000
    if not isClient() then return end
    local players = getOnlinePlayers()
    for i = 0, players:size() - 1 do
        local player = players:get(i)
        restoreVisual(player, player:getPrimaryHandItem())
        restoreVisual(player, player:getSecondaryHandItem())
    end
end

Events.OnServerCommand.Add(onServerCommand)
Events.OnEquipPrimary.Add(restoreVisual)
Events.OnEquipSecondary.Add(restoreVisual)
Events.OnTick.Add(onTick)

return WSS
