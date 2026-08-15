# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Atualizado em 2026-08-15. Este arquivo responde: **onde estamos agora?**

## Gate de continuidade

- PUC v1.0 teve validação independente completa em 14/08 para aquele snapshot.
- A verificação de cobertura pré-publicação de 15/08 permanece em `governance/CONTINUITY-VALIDATION-2026-08-15.md`.
- A reconciliação foi publicada no commit `be52e36962159fa7a42ba93a0e96a028daabb67a`.
- Depois do push, um novo chat reconstruiu o estado a partir do GitHub canônico, sem depender de recapitulação conversacional.
- Resultado: **CONTINUIDADE COMPLETA**.
- Evidência: `governance/CONTINUITY-VALIDATION-INDEPENDENT-2026-08-15.md`.
- O resultado corresponde ao snapshot reconciliado anterior à Missão 2/2B; não é uma nova validação independente do estado atual.
- O PUC permanece ativo para futuras mudanças e migrações.

## Estado atual

- Repositório: `leon337/cloud-infrastructure`.
- FASE 0: `DONE`.
- Auditoria read-only Fase B: `DONE`, aprovada por LEANDRO para reconciliação.
- Reconciliação documental de 15/08: versionada e publicada em `be52e36962159fa7a42ba93a0e96a028daabb67a`.
- Sincronização pós-push validada: HEAD local, `main`, `origin/main` e GitHub `main` apontavam para o mesmo SHA.
- Fechamento pós-push/pós-PUC: documentado no estado canônico.
- Missão 2/2B: nova chave dedicada instalada e login atual de `ubuntu` validado; fechamento em `history/SESSION-2026-08-15-010.md`.
- FASE 1 — acesso administrativo, recovery e segurança mínima: `IN_PROGRESS`.
- FASE 2 — Cloud Workstation: `PRIORITY_PLANNED`, próxima grande entrega após os pré-requisitos da F1.
- Política de futuros commits: **HUMAN_GATE obrigatório**.
- Nova conexão ou alteração na VPS: **NÃO AUTORIZADA**.

## Fotografia real de 15/08/2026

- Ubuntu 24.04.4 LTS, kernel `6.8.0-137-generic`, x86-64 em KVM/QEMU.
- 8 CPUs lógicas, ~23 GiB RAM, sem swap.
- `/dev/sda` 300 GiB GPT; raiz ext4 com ~288 GiB disponíveis.
- systemd running, 0 failed, NTP sincronizado, timezone Europe/Berlin.
- listeners externos observados: SSH TCP 22 IPv4/IPv6; demais apenas DNS local.
- UFW instalado e inativo; nenhuma regra guest nftables/iptables observada; fail2ban ausente.
- cinco pacotes Krb5 ainda adiados por phasing; nenhum upgrade instalado pela auditoria.
- Docker/containerd e desktop gráfico utilizável não confirmados.
- backup independente guest não confirmado; recursos de provider permanecem `UNCONFIRMED`.

Inventário detalhado: `docs/06-inventario.md`.

## Acesso e identidade

- root por senha: acesso operacional preservado, validado e temporário;
- fingerprint ED25519 do host: `SHA256:sb3hPt85xBueteG/kVVVXZs1Wf/KCO3DSeY25fvGkj4`;
- alias/keepalive local: historicamente validados;
- `ubuntu`: UID 1000, senha bloqueada, sudo efetivo e NOPASSWD via cloud-init;
- chave ED25519 anteriormente observada: preservada;
- nova chave ED25519 dedicada: pública instalada exatamente uma vez; fingerprint `SHA256:/p5jX65s2WyxkD3xooTozV09DSYAmKIAgZKk3Veb1Hg`;
- login atual de `ubuntu`: **VALIDATED**, exclusivamente por `publickey`, sem fallback para senha no teste;
- identidade validada: usuário `ubuntu`, UID 1000, hostname `vmi3506102`;
- `config/ssh_config.example` documenta `ubuntu` como canal principal por chave e mantém alias root temporário; o exemplo não foi aplicado automaticamente;
- `ubuntu` pertence ao grupo `lxd`, que exige revisão de menor privilégio.

## LXD

- snap 5.21.6;
- 0 instâncias totais e 0 em execução na auditoria;
- daemon ativado acidentalmente por `lxc version` via socket activation;
- recuperação autorizada: daemon `inactive/dead`, processo ausente, socket `active/listening` e habilitado;
- listeners de rede permaneceram inalterados.

## Findings

Resolvidos: `FND-SSH-001`, `FND-SSH-003`, `FND-DOC-001`, `FND-AUDIT-001`.

Abertos high: `FND-SSH-002`, `FND-LXD-001`, `FND-BACKUP-001`.

Abertos para análise: `FND-CPU-001`, `FND-CLOUDINIT-001`.

## Cloud Workstation

A entrega não está mais adiada. Depois de acesso administrativo, recovery e segurança mínima, deverá ser implementada antes de Docker/observabilidade/plataforma ampla.

Só será `DONE` após LEANDRO validar produtividade real com navegador, VS Code, terminal, gerenciador de arquivos, múltiplas janelas, copiar/colar, resolução, estabilidade, reconexão, latência percebida e consumo de recursos.

## Ponto exato de retomada

Próximo micro-passo: aguardar HUMAN_GATE operacional de LEANDRO para revisão read-only de sudo/NOPASSWD e do privilégio equivalente a root via LXD.

Depois dessa revisão autorizada: validar recovery proporcional e segurança mínima de SSH/firewall sem lockout. Não restringir root/senha nem alterar firewall antes desses controles.

## Proibições imediatas

Sem novo HUMAN_GATE, não:

- criar novo commit ou push sem HUMAN_GATE aplicável;
- conectar novamente à VPS;
- alterar usuário, sudo, SSH, chaves, firewall, LXD, pacotes, swap, filesystem ou serviços;
- instalar Cloud Workstation, Docker ou qualquer componente.

Toda retomada deve começar em `CONTEXT.md` e verificar a `main` real.
