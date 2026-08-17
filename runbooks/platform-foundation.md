# Runbook — Foundations F1.1

Escopo: contas técnicas bloqueadas, namespaces, tmpfiles e systemd slices de
accounting. Não inclui Docker, rede, firewall, SSH, XRDP ou secrets.

## Guardrails

- executar somente contra `node-01` DEV;
- confirmar branch/SHA, `origin/main`, worktree limpo e branch remota antes de
  qualquer operação privilegiada;
- usar o desired state validado no commit
  `edd2497d657cc9bc35952f5dfc71090a18dade53` pelo GitHub Actions run
  `31972460567`, ou um descendente cuja CI esteja verde e cujo delta executável
  tenha sido explicitamente reconciliado; o run não cobre mudanças posteriores;
- manter uma segunda sessão SSH validada;
- não usar `NOPASSWD`, `sshpass` ou variável de senha;
- LEANDRO digita sudo diretamente quando `--ask-become-pass` solicitar;
- abortar diante de sessão/mudança concorrente, unit falha, backup inválido ou
  objeto preexistente sem o marker externo exato;
- nunca usar rollback se `/var/lib/cloud-platform` contiver estado.
- o marker `/etc/cloud-platform-foundation.managed` é `root:root 0600`, fica
  fora dos diretórios removíveis e deve ter conteúdo SLICE-001 exato;
- não alterar marker, allowlist ou identidade do nó por `--extra-vars`;
- o harness Docker privilegiado é root-equivalent: executá-lo somente em VM
  descartável ou no runner hospedado do CI, nunca em NODE-01/Workstation.

## Preparar o controller

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.lock
export PLATFORM_SSH_KEY_FILE=/path/to/dedicated/key
```

O arquivo apontado por `PLATFORM_SSH_KEY_FILE` permanece fora do repositório.
Antes de qualquer conexão, o primeiro play valida que ele é arquivo regular,
não symlink, modo `0400/0600` e fingerprint pública previamente registrada. O
alvo remoto também precisa coincidir com IP, hostname e hash sanitizado de
`machine-id` versionados; `StrictHostKeyChecking=yes` continua obrigatório. A
entrada ED25519 conhecida do host deve resultar no fingerprint público
`SHA256:sb3hPt85xBueteG/kVVVXZs1Wf/KCO3DSeY25fvGkj4`; não persistir a chave
privada nem conteúdo de `known_hosts` como evidência.

## Precheck read-only

1. `git fetch --prune origin`; confirmar SHA, worktree e run CI aplicável;
2. validar SSH estrito, fingerprint público do host e duas sessões;
3. registrar `systemctl --failed`, listeners, RAM, disco, cgroup v2 e AppArmor;
4. registrar estados de SSH/UFW/fail2ban/XRDP/LightDM/LXD/Docker;
5. validar checksum/listagem do backup recente e cópia off-host disponível;
6. confirmar ausência de marker, `cloud-platform`, `platform-core`, paths,
   runtime paths, tmpfiles e units F1.1;
7. confirmar ausência de `/run/lock/cloud-platform-foundation-operation`; se
   existir, seguir a investigação de lock obsoleto abaixo, sem removê-lo
   automaticamente;
8. confirmar que nenhum `ansible-playbook`, package manager ou reconcile está em
   execução e que não há mudança concorrente;
9. executar suíte local e syntax check.

Comandos de validação local:

```bash
PATH="$PWD/.venv/bin:$PATH" PYTHON="$PWD/.venv/bin/python" scripts/test.sh
cd automation/ansible
../../.venv/bin/ansible-playbook playbooks/foundation.yml --syntax-check
```

## Preview aprovado e apply posterior

O check mode inicial simula o máximo possível, mas não substitui backup/rollback:

```bash
cd automation/ansible
../../.venv/bin/ansible-playbook playbooks/foundation.yml \
  --ask-become-pass --check --diff
```

O preview real foi executado em `2026-08-17T05:48:16Z`: `failed=0`,
`unreachable=0`, quatro grupos de mudanças simulados e managed surface
invariante. Evidence/state/checkpoint registram o hash sanitizado e a leitura
pós-preview. No primeiro check mode, account/directories dependentes do grupo
simulado foram deliberadamente pulados; portanto `changed=0` não era o resultado
esperado do preview.

Antes do comando de apply abaixo, revalidar backup/checksum/cópia off-host,
segunda sessão SSH, lock e ausência de concorrência. Não encadear automaticamente
ao preview:

```bash
../../.venv/bin/ansible-playbook playbooks/foundation.yml \
  --ask-become-pass --diff
```

Não copiar a saída completa se uma task futura manipular secret. F1.1 não possui
material secreto. No preview inicial, account/directories dependentes do grupo
ainda inexistente são deliberadamente pulados; a integração descartável cobre o
apply real, idempotência, invariantes e recusas de rollback.

## Validação pós-apply

1. executar novamente o playbook; resultado esperado: `changed=0`;
2. `systemd-analyze verify` nas duas slices;
3. conferir conta `platform-core` bloqueada/nologin e sem `sudo/lxd/docker`;
4. conferir paths/owners/modes e negar escrita não autorizada;
5. confirmar `/run/cloud-platform/credentials` como `root:root 0700`;
6. comparar listeners e ruleset com baseline; nenhum novo endpoint;
7. validar SSH, UFW, fail2ban, XRDP, LightDM e LXD invariantes;
8. confirmar zero units falhas e Workstation funcional;
9. reiniciar somente depois de checkpoint próprio; F1.1 não exige reboot imediato.

## Rollback

Somente se o estado criado pelo slice continuar vazio:

```bash
cd automation/ansible
../../.venv/bin/ansible-playbook playbooks/rollback-foundation.yml \
  --ask-become-pass \
  -e platform_foundation_rollback_confirm=true --diff
```

O playbook exige confirmação, alvo DEV exato, marker/proveniência exatos,
diretórios vazios, zero processos/tarefas nas slices, hashes dos arquivos e
identidade técnica bloqueada. Ele remove diretórios somente com `rmdir` atômico,
nunca recursivamente, e deixa o marker até o último passo. Qualquer divergência
aborta antes da primeira remoção. Após rollback, repetir todas as invariantes. Se
qualquer serviço futuro já usar o namespace, parar e criar um plano de
migração/backup; não forçar remoção.

### Lock obsoleto após interrupção

Apply e rollback usam o diretório exclusivo
`/run/lock/cloud-platform-foundation-operation`. O bloco `always` o remove em
sucesso ou falha normal. Uma perda abrupta da conexão/host pode deixá-lo vazio e
todo novo reconcile deve então falhar fechado. Não o remova automaticamente.
Primeiro confirme em segunda sessão que não existe processo `ansible-playbook`,
apply/rollback concorrente ou conteúdo no lock; confira marker e objetos contra
o precheck. Somente então LEANDRO pode executar interativamente:

```bash
sudo rmdir /run/lock/cloud-platform-foundation-operation
```

Se `rmdir` acusar conteúdo, parar e investigar; nunca usar remoção recursiva.

## Integração descartável

O teste completo usa `--privileged` para systemd e, portanto, só é permitido em
VM efêmera comprovadamente descartável:

```bash
FOUNDATION_TEST_PRIVILEGED_CONFIRM=DISPOSABLE_VM_ONLY \
  scripts/test_foundation_container.sh
```

O harness recusa NODE-01/hostname real, monta apenas um bundle allowlisted sem
`.git`, `.venv`, inventário DEV ou secrets, usa nomes únicos e remove container,
imagem e bundle. Ele testa check mode, apply, `changed=0`, contas/permissões,
quatro recusas fail-closed sem mudança e rollback vazio. O CI hospedado é a
execução canônica; não rode esse comando na máquina física de trabalho.

O run `31972460567` passou para o commit `edd2497d`: check mode e partial-marker
check preservaram o estado da fixture, apply teve `changed=7`, segunda
reconciliação `changed=0`, quatro recusas de rollback preservaram o estado e o
rollback/cleanup terminaram limpos. Isso não é evidência de execução na VPS real.

## Evidência

Persistir somente resultados sanitizados em `evidence/SLICE-001/`: SHA, timestamps,
status, hashes, contagens, tests PASS/FAIL e deltas. Nunca persistir senha, chave,
token, conteúdo de `authorized_keys` ou connection string.
