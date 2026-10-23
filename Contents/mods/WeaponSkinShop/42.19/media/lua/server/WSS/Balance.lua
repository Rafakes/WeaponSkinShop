if not isServer() then return {} end

-- 42.20 exposes BalanceCore. 42.19 keeps the same functions local; its storage
-- contract is ServerShopBalance[username] and zPoints_Balance is only a cache.
local ok, Core = pcall(require, "ServerShopBalanceCore")
if not ok or type(Core) ~= "table" or not Core.getBalance then Core = nil end
local B = {}

local function storeFor(player)
    local username = player and player:getUsername()
    if not username or username == "" or not ModData or not ModData.getOrCreate then return nil end
    return ModData.getOrCreate("ServerShopBalance"), username
end

function B.read(player)
    local store, key = storeFor(player)
    if not store then return nil end
    local value = Core and Core.getBalance(player) or tonumber(store[key] or 0)
    if type(value) ~= "number" or value ~= value or value < 0 or value == math.huge then return nil end
    return math.floor(value * 100 + 0.5) / 100
end

function B.write(player, value, reason)
    local store, key = storeFor(player)
    if not store then return false end
    if Core then
        Core.setBalance(player, value, reason)
    else
        -- Purchases and refunds only: neither counts as newly earned points.
        store[key] = value
        player:getModData().zPoints_Balance = value
    end
    return B.read(player) == value
end

function B.sync(player)
    local balance = B.read(player)
    if balance ~= nil then
        sendServerCommand(player, "ServerShop", "get", { balance })
    end
end

return B
