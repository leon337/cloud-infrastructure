# 08 — Segurança e Governança

## Princípio

Nenhuma melhoria de segurança deve criar risco maior de perda de acesso sem caminho de recuperação validado.

## Sequência de segurança planejada

Estudar e implementar gradualmente:

- senha root comprometida — já rotacionada;
- atualização inicial;
- usuário administrativo próprio;
- sudo;
- SSH;
- chave SSH;
- validação por chave;
- política de root;
- política de senha SSH;
- firewall Contabo;
- firewall Ubuntu;
- portas necessárias;
- brute force quando pertinente;
- logs;
- backups;
- snapshots;
- recuperação;
- menor privilégio.

## Regras de proteção contra lockout

- não fechar acesso root antes de validar usuário administrativo;
- não desativar senha antes de validar chave;
- não alterar firewall sem garantir rota de recuperação;
- manter VNC/Rescue como opções conhecidas enquanto a política definitiva não for escolhida;
- mudanças pequenas e verificadas.

## Secrets

Proibido versionar:

- senhas;
- chaves SSH privadas;
- tokens;
- API keys;
- códigos 2FA;
- connection strings reais;
- credenciais Contabo;
- `.env` real.

Identificadores operacionais como IP público, hostname, alias e fingerprint SSH não são secrets por si só e podem ser documentados quando necessários.

## HUMAN_GATE

Exige autorização explícita de LEANDRO:

- mudanças destrutivas;
- firewall/exposição de rede;
- políticas que podem bloquear acesso;
- particionamento/filesystem;
- instalação estrutural relevante;
- custo/upgrade/migração;
- cancelamento/reinstalação;
- decisões arquitetônicas permanentes.

## Segurança do próprio GitHub

O repositório permanece privado nesta fase. Privacidade do repositório não substitui política de zero secrets.