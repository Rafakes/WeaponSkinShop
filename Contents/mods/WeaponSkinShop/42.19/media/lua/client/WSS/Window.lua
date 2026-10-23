require "ISUI/ISCollapsableWindow"
require "ISUI/ISScrollingListBox"
require "ISUI/ISButton"
require "ISUI/ISRichTextPanel"
local WSS = require "WSS/Client"
local Window = ISCollapsableWindow:derive("WSSWindow")

function Window:new(player, item)
    local scale = math.max(1, getTextManager():getFontHeight(UIFont.Small) / 16)
    local w = math.min(math.floor(720 * scale), getCore():getScreenWidth() - 32)
    local h = math.min(math.floor(510 * scale), getCore():getScreenHeight() - 32)
    local o = ISCollapsableWindow.new(self, (getCore():getScreenWidth() - w) / 2,
        (getCore():getScreenHeight() - h) / 2, w, h)
    o.player, o.item = player, item
    o.title = getText("UI_WSS_Title")
    o.resizable = false
    o.backgroundColor = { r = 0.045, g = 0.055, b = 0.07, a = 0.98 }
    o.status = getText("UI_WSS_Loading")
    o.balance, o.ready = -1, false
    o.line = getTextManager():getFontHeight(UIFont.Small) + 5
    return o
end

function Window:createChildren()
    ISCollapsableWindow.createChildren(self)
    local top = self:titleBarHeight() + self.line * 3
    local bodyH = self.height - top - self.line * 5 - 55
    self.list = ISScrollingListBox:new(16, top, math.floor(self.width * 0.48) - 24, bodyH)
    self.list:initialise()
    self.list:instantiate()
    self.list.itemheight = self.line * 2
    self.list.font = UIFont.Small
    self.list.drawBorder = true
    self:addChild(self.list)
    self.bodyTop, self.bodyHeight = top, bodyH

    self.help = ISRichTextPanel:new(16, top + bodyH + 10, self.width - 32, self.line * 3)
    self.help:initialise()
    self.help.background = false
    self.help.autosetheight = false
    self.help.text = getText("UI_WSS_Help")
    self.help:paginate()
    self:addChild(self.help)

    local buttonH = self.line + 10
    self.buy = ISButton:new(16, self.height - buttonH - 16, math.floor(self.width * 0.65) - 24,
        buttonH, getText("UI_WSS_Buy"), self, Window.onApply)
    self.buy:initialise()
    self.buy.enable = false
    self:addChild(self.buy)
    self.refresh = ISButton:new(self.width * 0.65, self.height - buttonH - 16,
        self.width * 0.35 - 16, buttonH, getText("UI_WSS_Refresh"), self, Window.onRefresh)
    self.refresh:initialise()
    self:addChild(self.refresh)
end

function Window:request(command, skinId)
    if not isClient() then
        self.status = getText("UI_WSS_MPOnly")
        self.ready = false
        return
    end
    WSS.sequence = WSS.sequence + 1
    self.requestId = WSS.sequence
    self.pendingUntil = getTimestampMs() + 8000
    self.ready = false
    self.status = getText("UI_WSS_Loading")
    sendClientCommand(self.player, WSS.MODULE, command,
        { itemId = self.item:getID(), requestId = self.requestId, skinId = skinId })
end

function Window:onRefresh()
    if not self.pendingUntil then self:request("status") end
end

function Window:onApply()
    local selected = self.list.items[self.list.selected]
    if not self.ready or self.pendingUntil or not selected then return end
    if self.item:getOutermostContainer() ~= self.player:getInventory() then
        self.ready = false
        self.status = getText("UI_WSS_Missing")
        return
    end
    self:request("apply", selected.item.id)
end

function Window:receive(args)
    self.pendingUntil = nil
    self.balance = args.balance or -1
    self.active = args.active or "original"
    self.status = getText("UI_WSS_" .. (args.code or "Unavailable"))
    self.ready = self.balance >= 0 and args.fullType == self.item:getFullType()
        and args.code ~= "Empty" and args.code ~= "Unavailable" and args.code ~= "Missing"
    local old = self.list.items[self.list.selected]
    local selectedId = old and old.item.id or "cobalt"
    self.list:clear()
    if not args.fullType or not WSS.catalog[args.fullType] then return end
    self.list:addItem(getText("UI_WSS_Original") .. "  /  " .. getText("UI_WSS_Free"),
        { id = "original", price = 0, owned = true })
    for _, row in ipairs(args.rows or {}) do
        local skin = WSS.getSkin(args.fullType, row.id)
        if skin then
            local price = row.owned and getText("UI_WSS_Owned") or tostring(row.price) .. " zPoints"
            local data = { id = row.id, price = row.price, owned = row.owned,
                preview = getTexture(skin.preview), previewTint = skin.previewTint,
                name = getText(skin.nameKey) }
            self.list:addItem(data.name .. "  /  " .. price, data)
        end
    end
    self.list.selected = 1
    for i, row in ipairs(self.list.items) do
        if row.item.id == selectedId then self.list.selected = i; break end
    end
end

function Window:prerender()
    ISCollapsableWindow.prerender(self)
    if self.pendingUntil and getTimestampMs() > self.pendingUntil then
        self.pendingUntil = nil
        self.ready = false
        self.status = getText("UI_WSS_Timeout")
    end
    if self.player:isDead() then self:close(); return end
    local selected = self.list.items[self.list.selected]
    local row = selected and selected.item
    local price = row and (row.owned and 0 or row.price) or 0
    local inInventory = self.item:getOutermostContainer() == self.player:getInventory()
    self.buy.enable = self.ready and not self.pendingUntil and row ~= nil and inInventory
        and self.balance >= price and row.id ~= self.active
    self.refresh.enable = not self.pendingUntil
    self.buy:setTitle(row and row.id == self.active and getText("UI_WSS_Active")
        or (price == 0 and getText("UI_WSS_Apply") or getText("UI_WSS_BuyPrice", tostring(price))))
    local y = self:titleBarHeight() + 10
    self:drawText(self.item:getName(), 16, y, 0.9, 0.93, 1, 1, UIFont.Medium)
    self:drawText(getText("UI_WSS_Balance", self.balance >= 0 and string.format("%.2f", self.balance) or "..."),
        16, y + self.line + 5, 0.42, 0.72, 1, 1, UIFont.Small)
    local px, py = math.floor(self.width * 0.5), self.bodyTop
    local pw = self.width - px - 16
    self:drawRect(px, py, pw, self.bodyHeight, 1, 0.07, 0.085, 0.11)
    if row and row.id == "cyberpunk" then
        self:drawRectBorder(px, py, pw, self.bodyHeight, 0.9, 0.52, 0.15, 0.75)
        self:drawRect(px + 5, py + 5, pw - 10, 2, 0.95, 0.08, 0.78, 0.96)
        self:drawRect(px + 5, py + self.bodyHeight - 7, pw - 10, 2, 0.95, 0.05, 0.84, 0.96)
    end
    local texture = row and row.preview
    if texture then
        local side = math.min(pw, self.bodyHeight, row.previewTint and 140 or 512)
        if row.previewTint then
            local red, green, blue = 0.35, 0.60, 1
            if row.previewTint == "cyberpunk" then red, green, blue = 0.76, 0.35, 1 end
            self:drawTextureScaledAspect(texture, px + (pw - side) / 2,
                py + (self.bodyHeight - side) / 2, side, side, 1, red, green, blue)
        else
            self:drawTextureScaledAspect(texture, px + (pw - side) / 2,
                py + (self.bodyHeight - side) / 2, side, side, 1, 1, 1, 1)
        end
    elseif row and row.id == "original" then
        local icon = getTexture(WSS.catalog[self.item:getFullType()].originalIcon)
        if icon then self:drawTextureScaledAspect(icon, px + pw / 2 - 48, py + self.bodyHeight / 2 - 48, 96, 96, 1, 1, 1, 1) end
    else
        self:drawTextCentre(getText("UI_WSS_NoPreview"), px + pw / 2, py + 35, 0.65, 0.68, 0.72, 1, UIFont.Small)
    end
    if row and row.previewTint then
        self:drawTextCentre(getText("UI_WSS_PreviewTint"), px + pw / 2,
            py + self.bodyHeight - self.line - 8, 0.65, 0.72, 0.82, 1, UIFont.Small)
    end
    self:drawText(self.status, 16, self.height - self.line * 2 - 35, 0.85, 0.85, 0.85, 1, UIFont.Small)
end

function Window:close()
    WSS.windows[self.player:getPlayerNum()] = nil
    ISCollapsableWindow.close(self)
    self:removeFromUIManager()
end

function WSS.open(player, item)
    local old = WSS.windows[player:getPlayerNum()]
    if old then old:close() end
    local window = Window:new(player, item)
    window:initialise()
    window:addToUIManager()
    window:setVisible(true)
    WSS.windows[player:getPlayerNum()] = window
    window:request("status")
end

Events.OnFillInventoryObjectContextMenu.Add(function(playerIndex, context, selections)
    local player = getSpecificPlayer(playerIndex)
    if not player then return end
    for _, selected in ipairs(selections) do
        local item = instanceof(selected, "InventoryItem") and selected or selected.items and selected.items[1]
        if WSS.isGun(item) and item:getOutermostContainer() == player:getInventory() then
            context:addOption(getText("UI_WSS_Context"), player, WSS.open, item)
            return
        end
    end
end)

return Window
