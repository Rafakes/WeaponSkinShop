import json
from pathlib import Path

root = Path(__file__).parent / 'Contents/mods/WeaponSkinShop/42.19/media/lua/shared/Translate'
en = {
    'Title': 'WEAPON SKIN SHOP', 'Context': 'Weapon skin shop', 'Cobalt': 'Cobalt',
    'Cyberpunk': 'Cyberpunk Neon (Premium)',
    'Original': 'Original', 'Free': 'Free', 'Owned': 'Unlocked', 'Buy': 'Buy skin',
    'BuyPrice': 'Buy for %1 zPoints', 'Apply': 'Apply for free', 'Active': 'Already applied',
    'Refresh': 'Refresh', 'Balance': 'Balance: %1 zPoints', 'NoPreview': 'No preview',
    'Loading': 'Waiting for the server...', 'Ready': 'Choose a skin for this weapon.',
    'Applied': 'Skin applied successfully.', 'Missing': 'The weapon is no longer in your inventory.',
    'Empty': 'No skins available for this weapon yet.', 'Unavailable': 'Shop unavailable. Refresh and try again.',
    'Invalid': 'Invalid skin or request.', 'Funds': 'Not enough zPoints.',
    'Timeout': 'No response. Refresh to check the purchase status.',
    'MPOnly': 'Requires multiplayer/coop with Server Shop.',
    'Help': 'Unlock once per account and weapon type. Reapply for free. <LINE> Keeps ammunition, condition and attachments.',
    'PreviewTint': 'Color preview. The 3D shader applies the final finish.',
}
pt = {
    'Title': 'LOJA DE SKINS DE ARMAS', 'Context': 'Loja de skins', 'Cobalt': 'Cobalto',
    'Cyberpunk': 'Cyberpunk Néon (Premium)',
    'Original': 'Original', 'Free': 'Grátis', 'Owned': 'Desbloqueada', 'Buy': 'Comprar skin',
    'BuyPrice': 'Comprar por %1 zPoints', 'Apply': 'Aplicar gratuitamente', 'Active': 'Já aplicada',
    'Refresh': 'Atualizar', 'Balance': 'Saldo: %1 zPoints', 'NoPreview': 'Sem prévia',
    'Loading': 'A aguardar resposta do servidor...', 'Ready': 'Escolha uma skin para esta arma.',
    'Applied': 'Skin aplicada com sucesso.', 'Missing': 'A arma já não está no seu inventário.',
    'Empty': 'Ainda não há skins para esta arma.', 'Unavailable': 'Loja indisponível. Atualize e tente novamente.',
    'Invalid': 'Skin ou pedido inválido.', 'Funds': 'zPoints insuficientes.',
    'Timeout': 'Sem resposta. Atualize para consultar a compra.',
    'MPOnly': 'Requer multiplayer/coop com o Server Shop.',
    'Help': 'Compra única por conta e tipo de arma. Reaplicação gratuita. <LINE> Mantém munição, condição e acessórios.',
    'PreviewTint': 'Prévia de cor. O shader aplica o acabamento final em 3D.',
}
ptbr = dict(pt, Loading='Aguardando resposta do servidor...', Missing='A arma não está mais no seu inventário.')
for locale, translations in [('EN', en), ('PT', pt), ('PTBR', ptbr)]:
    assert translations.keys() == en.keys()
    folder = root / locale
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'UI.json').write_text(json.dumps({'UI_WSS_' + key: value for key, value in translations.items()},
                                             ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('EN, PT and PTBR translations written.')
