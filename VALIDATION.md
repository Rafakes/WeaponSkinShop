# Validação desta versão

- 36 cenários de integração em Lua 5.1 passaram: 18 com o contrato de saldo 42.19 e 18 com o ficheiro real `ServerShopBalanceCore.lua` 42.20. Incluem cobrança independente das duas skins e alternância gratuita após desbloqueio.
- Todos os Lua compilam como Lua 5.1. Traduções JSON EN/PT/PTBR têm as mesmas chaves e cobrem as referências da interface.
- O scanner multiplayer identificou apenas pontos de revisão: leitura/escrita visual de ModData no cliente e botão bloqueado na interface. As escritas visuais vêm de respostas do servidor; a autorização financeira é independente, em `WSS/Server.lua`. A posse e o saldo são novamente verificados no servidor.
- Não há redefinição de itens, troca de arma, recriação de munição ou alterações aos ficheiros das dependências.
- Atlas 256×256 inspecionado após exportação. A malha e os transforms dos sete pontos de ligação foram copiados do bloco original `MarzGuns.AK47`.
- Catálogo gerado a partir de 70 itens de fogo e respetivos 140 modelos (70 Cobalto e 70 Cyberpunk); 68 atlas UV existentes foram resolvidos, incluindo os dois atlas partilhados pelos módulos acoplados.
- `ModelScript` aceita a propriedade `shader`; `ShaderProgram` resolve `media/shaders/<nome>_static.vert` e `<nome>.frag` pelo sistema de ficheiros do jogo. Os doze ficheiros `WSS_Cobalt` e `WSS_Cyberpunk` seguem esses nomes. Isto confirma o caminho de carregamento, mas não compila os shaders dentro do jogo.

## APIs verificadas no jogo instalado

Classes extraídas do `projectzomboid.jar` e consultadas com CFR 0.152:

- `HandWeapon.java`: `setWeaponSprite` altera apenas o sprite; `save` grava o sprite diferente do original e `load` restaura-o. `getStaticModel` usa o sprite na ausência de override estático.
- `InventoryItem.java`: `setWorldStaticModel` grava `modData.worldStaticModel`; limpar essa chave restaura o modelo de script. `syncItemFields()` dirige a sincronização ao dono do inventário.
- `SyncItemFieldsPacket.java`: transporta ModData, mas não `weaponSprite`; por isso há uma resposta visual própria, limitada ao dono e vizinhos.
- `LuaManager$GlobalObject.class`: expõe `getPlayerByOnlineID` usado pela receção visual.
- Lua vanilla: lifecycle de `ISCollapsableWindow`, `ISScrollingListBox` e exemplos de `resetEquippedHandsModels`/`syncItemFields`.

## Por validar em runtime

Não foi executado o Project Zomboid nem um servidor dedicado nesta sessão. Ainda é necessário verificar o menu, os tamanhos de fonte, a compilação/renderização do shader 3D, acessórios, visual em outro cliente, transferência, reconexão e gravação/reinício. O roteiro está no README.

Os testes de reload recarregam o módulo Lua mantendo o armazenamento simulado; não são um teste de reinício real do servidor. O mod usa a persistência normal do jogo/Server Shop, sem prometer atomicidade perante falha do processo durante a gravação do mundo.
