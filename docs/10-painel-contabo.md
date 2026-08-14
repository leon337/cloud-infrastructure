# 10 — Painel Contabo: mapa operacional

Este documento preserva os conceitos aprendidos no primeiro acesso.

| Opção | Função | Risco/uso |
|---|---|---|
| Reinstalar | reinstala o sistema e pode apagar o estado atual | destrutivo; equivalente a formatar |
| Sistema de Resgate | inicia Linux temporário para reparar/acessar o disco principal | recuperação; não é backup |
| Redefinir Credenciais | redefine credencial administrativa | usado para rotacionar root |
| Alterar Nome de Exibição | muda etiqueta no painel | não confundir com hostname do Ubuntu |
| Gerenciador de Complementos | add-ons do provedor | pode envolver custo |
| Gerenciar Snapshots | cria/restaura estado da VPS | snapshot não substitui backup |
| Gerenciar Firewall | firewall externo da Contabo | erro pode bloquear acesso |
| Controle VNC | console/tela remota | validado com TigerVNC |
| Atualizar/Reduzir | mudança de capacidade/plano | pode envolver custo/migração |
| Mover Para Outra Região | migração geográfica | pode mudar IP e causar indisponibilidade |
| Expandir Armazenamento | aumenta capacidade contratada | Linux pode exigir expansão de partição/filesystem |
| Cancelar VPS | encerra serviço | crítico; não é botão de desligar |

## Conceitos consolidados

- Reinstalar = começar o sistema novamente.
- Rescue = usar outro sistema temporário para consertar/acessar o atual.
- Snapshot = retornar a um estado anterior.
- Backup = recuperar a partir de cópia independente.
- VNC = console alternativo; não cria GUI sozinho.
- Firewall Contabo e firewall Ubuntu são camadas diferentes.

Detalhes específicos do produto/provedor devem ser revalidados na documentação atual antes de ações de risco.