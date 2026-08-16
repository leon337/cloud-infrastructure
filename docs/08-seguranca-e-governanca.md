# 08 — Segurança e Governança

## Estado endurecido em 15/08/2026

- SSH: `PermitRootLogin no`, `PasswordAuthentication no`, `KbdInteractiveAuthentication no`, `PubkeyAuthentication yes`, `AllowUsers ubuntu`, `MaxAuthTries 3`, `LoginGraceTime 30`;
- UFW: ativo, default deny incoming, somente TCP 22/OpenSSH em IPv4/IPv6;
- fail2ban: jail `sshd` ativo;
- XRDP: somente `127.0.0.1:3389`; sesman somente `[::1]:3350`;
- sudo: sem `NOPASSWD`, com autenticação validada;
- LXD: `ubuntu` removido do grupo; daemon e socket desabilitados/inativos;
- updates: zero pendências após upgrade e reboot;
- recovery: VNC funcional e Rescue disponível;
- backup: configurações críticas diárias, cópia off-host e extração validadas.

As tentativas automatizadas observadas historicamente comprovam exposição/ataques, não comprometimento. O hardening reduziu a superfície e resolveu `FND-SSH-002`.

## Anti-lockout

Antes de restringir root/senha, foram validados `ubuntu`/publickey em sessão independente e VNC do provedor. Depois de cada mudança, SSH, listeners, UFW e serviços foram rechecados; um reboot final confirmou persistência.

## Secrets

Nunca versionar senhas, passphrases, chaves privadas, tokens, API keys, códigos 2FA, connection strings reais, credenciais Contabo ou arquivos `.env` reais. IP, hostname e fingerprints públicos podem ser documentados quando necessários.

## Próximo controle

Aplicar Foundations F1.1 sem ampliar superfície, mantendo SSH/UFW/XRDP e a
Workstation invariantes. Docker, Management Network, secret store e exposição
possuem slices/gates próprios. Rotação de credenciais permanece
`DEFERRED_BY_HUMAN_DECISION`.

## HUMAN_GATE

Mudanças destrutivas, custos, restore, reinstalação, storage, firewall/exposição, rotação e decisões arquitetônicas permanentes exigem a autorização aplicável de LEANDRO.
