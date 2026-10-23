# Weapon Skin Shop — Guns of Marz

Mod separado para Project Zomboid **42.19+**, multiplayer/coop, com `GunsOfMarz` e `ServerShop`. O GunsOfMarz também requer `SWMG`.

## Utilização

1. Ative `WeaponSkinShop` no servidor e nos clientes, juntamente com as dependências.
2. Tenha uma arma de fogo no inventário pessoal ou numa mochila que esteja a carregar.
3. Clique com o botão direito na arma → **Loja de skins**.
4. Em qualquer uma das **70 armas listadas em `ARMAS.md`**, selecione **Cobalto** (100 zPoints) ou **Cyberpunk Néon** (350 zPoints).
5. Cada acabamento é desbloqueado separadamente para essa conta e esse tipo de arma. Reaplicar noutra arma do mesmo tipo, alternar entre acabamentos já comprados ou voltar ao original é gratuito.

As 70 armas de fogo do Guns of Marz têm uma opção Cobalto e uma Cyberpunk Néon próprias: 140 modelos cosméticos ao todo. Cyberpunk combina grafite, painéis violeta e traços ciano/magenta. O ícone pequeno do inventário continua a ser o original. A AK-47 tem ilustrações dedicadas para os dois acabamentos; nas outras armas, a prévia da loja é uma versão colorida do ícone original e apenas indica a paleta. A skin modifica o modelo nas mãos e no chão. As peças móveis e acessórios mantêm as suas texturas originais.

## Instalação

O pacote de mod está em `Contents/mods/WeaponSkinShop`. Copie essa pasta para `Zomboid/mods/WeaponSkinShop` para testar localmente, ou coloque o projeto em `Zomboid/Workshop/Weapon Skin Shop` para publicar posteriormente. Use o mesmo pacote em todos os participantes. Não é preciso substituir ficheiros de GunsOfMarz ou do Server Shop.

Este projeto não publica no Workshop, não edita a configuração de servidores e não concede dinheiro. O Server Shop fornecido funciona em multiplayer; a loja de skins indica isso em singleplayer.

## Teste rápido

1. Num servidor de teste, com conta administradora, obtenha `MarzGuns.AK47` e mais algumas armas de `ARMAS.md` pelo painel de itens ou pelo comando `/additem "UTILIZADOR" "MarzGuns.AK47"`.
2. Use o painel administrativo do **Server Shop** para atribuir 500 zPoints à conta de teste.
3. Anote condição, munição, carregador, acessórios e ID da arma.
4. Compre Cobalto: o saldo deve passar de 500 para 400, sem alterar os dados anotados.
5. Compre Cyberpunk Néon: o saldo deve passar de 400 para 50. Restaure o original, alterne entre as duas skins e aplique ambas numa segunda AK-47: o saldo deve continuar em 50.
6. Confira a arma equipada com outro jogador próximo, largue-a no chão, recolha-a e transfira-a a outro jogador. A skin aplicada acompanha o objeto; os desbloqueios pertencem à conta compradora.
7. Reconecte e reinicie o servidor: confira a skin, o saldo e o desbloqueio.
8. Numa conta sem desbloqueio, confirme que uma compra é recusada quando o saldo é inferior ao preço escolhido.
9. Abra a loja e transfira/largue a arma antes da compra; o servidor deve recusar. Teste cliques repetidos e pedidos inválidos.
10. Aplique Cobalto e Cyberpunk a uma pistola, espingarda, escopeta e módulo acoplado; confirme as cores e os pontos de ligação de peças.

## Adicionar skins

O catálogo Cobalto/Cyberpunk foi gerado a partir dos scripts do Guns of Marz por `generate_catalog.py`. Cada chave é o fullType original da arma. Para adicionar novas cores, edite `42.19/media/lua/shared/WSS/Catalog.lua` e crie o modelo respetivo em `media/scripts`. Pode criar uma textura UV própria ou um shader com cor. Preserve a malha e os pontos de ligação dos acessórios. Acrescente traduções em EN/PT/PTBR. Reinicie servidor e clientes após mudar o catálogo.

Não reutilize IDs de skins já publicadas e não altere IDs de mod: os desbloqueios persistem com essas chaves. Faça cópia do save antes de testar ou remover mods.

## Integração e validação

- 42.20: usa `ServerShopBalanceCore.getBalance/setBalance` quando disponível.
- 42.19: usa o mesmo contrato persistente do Server Shop, `ModData.ServerShopBalance[username]`; `zPoints_Balance` é apenas cache.
- Desbloqueios: `ModData.WeaponSkinShopUnlocks_v1[username][fullType][skinId]` no servidor.
- Arma: mantém o próprio item, ID, estado e acessórios; grava `weaponSprite` e `modData.WSS_skin/worldStaticModel`.
- O cliente envia apenas item ID, skin ID e ID do pedido. Preço, saldo, posse e desbloqueio são verificados no servidor.
- `status`: resposta só ao solicitante; limite de 500 ms. `apply`: limite de 750 ms, cobrança idempotente pelo desbloqueio.
- `visual`: só ao dono e a jogadores a até 100 tiles, uma vez por aplicação. O cliente verifica duas armas equipadas por jogador carregado por segundo, sem pedidos de rede periódicos.
- A persistência usa o ciclo de gravação normal do jogo e do Server Shop; não constitui uma transação de base de dados resistente a encerramento abrupto no meio de um save.

Os testes automatizados usam Lua com doubles das APIs do jogo. Não substituem os testes de renderização, reconexão e servidor dedicado descritos acima. A integração foi comparada com as classes extraídas do `projectzomboid.jar` instalado: `HandWeapon.save/load`, `InventoryItem.setWorldStaticModel/syncItemFields`, `SyncItemFieldsPacket`, `ModelScript` e `ShaderProgram`. Os shaders usam os atlas UV originais sem mudar o mapeamento; a renderização final precisa de inspeção em jogo.

## Arte

A AK-47 mantém `media/textures/WSS/AK47_Cobalt.png` (256×256) e `media/ui/WSS/AK47_Cobalt.png` (512×512), criados antes com imagegen. A nova ilustração Cyberpunk está em `media/ui/WSS/AK47_Cyberpunk.png` (512×512). As outras 69 variantes Cobalto usam `WSS_Cobalt`; as 70 variantes Cyberpunk usam `WSS_Cyberpunk`. Ambos os shaders em `media/shaders` derivam do `basicEffect` do jogo instalado e reutilizam os atlas UV originais, a malha e os encaixes de cada arma. O Cyberpunk é um acabamento procedural sobre o atlas da arma, e não uma textura UV pintada separadamente para cada modelo. A aparência final em 3D ainda requer inspeção no jogo.

Créditos: arma, atlas de referência e malha de Guns of Marz (Marz). O addon referencia a malha da dependência.
