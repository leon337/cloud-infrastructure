# F1.2c — NODE-01 live recovery — 2026-08-28

**Classificação:** `VERIFIED_LIVE_RECOVERY`
**Host:** `vmi3506102` / NODE-01
**Escopo:** Cloud Platform Network Services F1.2c DEV/lab
**Candidato aplicado:** `baaf83908e8e83264baafc032434a4df1952450b`
**Lineage após PR #40:** `2408aed4ac8dbe692912a8d806852a45d9a97c49`
**Baseline documental de `main`:** `ce829067a9a04eceaa6eaefd9553899b2ce14da1`

## Resultado executivo

O rollout autorizado F1.2c foi concluído no NODE-01 com precheck fail-closed, checkpoint e backup pré-mudança, apply do candidato exato, `recovery check` e pós-validação independente root. O estado final do recovery é `RECOVERED`.

A configuração `/etc/cloud-platform/network-services` já existia antes do recovery e foi classificada como `EXACT_PRESENT`: metadata, shape e os sete hashes coincidiam com o candidato. O recovery corrigido preservou essa configuração em vez de reescrevê-la e registrou a variante no checkpoint para rollback simétrico.

Nenhum reboot, update, mudança SSH, alteração de `systemd-networkd`, promoção MCF ou produção externa pertenceu a este rollout.

## Correções que precederam o rollout

- PR #39: alinhou os markers Foundation/Docker ao contrato canônico real; o falso `foundation_marker_drift` vinha do harness/recovery simplificado.
- PR #40: modelou as variantes parciais `ABSENT` e `EXACT_PRESENT`, rejeitando shape/hash/metadata divergentes e preservando a baseline no rollback.
- Candidato exato da PR #40: `baaf83908e8e83264baafc032434a4df1952450b`.
- Merge da PR #40 somente na lineage `fix/f1-2c-systemd-runtime-lock`: `2408aed4ac8dbe692912a8d806852a45d9a97c49`.

## Gates de validação do candidato

PR #40 / SHA `baaf83908e8e83264baafc032434a4df1952450b`:

- contratos focados: `10/10 PASS`;
- suíte unitária local: `152/152 PASS`;
- Markdown, YAML, manifests, state/project-status, Python compile, shell syntax e `git diff --check`: `PASS`;
- GitHub-hosted static + ShellCheck run `33217692498`: `SUCCESS`;
- GitHub-hosted KVM run `33217692536`: `SUCCESS`;
- KVM `baseline_config=absent`: historical failure, precheck, apply, check, idempotência, rollback e cleanup = `PASS`;
- KVM `baseline_config=exact_present`: os mesmos gates = `PASS`.

As workflows genéricas Foundation/Docker continuaram vermelhas apenas no scanner de blobs históricos preexistentes, mesma classificação já conhecida: `FAIL — PREEXISTING_HISTORY_ONLY_GATE`. Nenhum arquivo novo da PR apareceu nos achados.

## Precheck live

Em `2026-08-28T22:52:55Z`, o launcher precheck-only do candidato exato retornou:

```text
PRECHECK_STAGE=PASS
RECOVERY_PRECHECK=PASS state=KNOWN_PARTIAL baseline_config=EXACT_PRESENT
PRECHECK_LAUNCHER=PASS
```

O precheck privilegiado anterior também confirmou zero estado Docker antes da mutação: containers `0`, images `0`, volumes `0`, custom networks `0`.

## Checkpoint e backup pré-apply

O checkpoint foi criado em `2026-08-28T22:55:37Z` e registrou:

```text
candidate_sha=baaf83908e8e83264baafc032434a4df1952450b
historical_partial_commit=c9f909945b544d22dbabc619252456f7190f7ae9
baseline_config_state=EXACT_PRESENT
```

Os hashes históricos preservados no checkpoint foram verificados:

- helper anterior: `06d0f016809a2e8d9cf0be5a258766563cc686fe40b21ec3578a99c731421060`;
- unit anterior: `dfe10b0e0046242695fe5ba03215f49aa938cf94b733bba3b1a2ba9cfad7e6d1`.

O backup pré-apply foi criado em `/var/backups/cloud-infrastructure/cloud-infrastructure-config-20260828T225537Z.tar.gz`, owner `root:adm`, mode `0640`. O sidecar `.sha256` validou `OK` em leitura root posterior.

## Estado live pós-apply

A pós-validação root independente terminou com exit code `0` e confirmou:

```text
RECOVERY_CHECK=PASS state=RECOVERED
F1_2C_POSTVERIFY=PASS baseline_config=EXACT_PRESENT state=RECOVERED
```

O state file do recovery é `root:root 0600`; o checkpoint `config-state` é `root:root 0600` e contém `EXACT_PRESENT`.

Hashes da superfície instalada:

- `/usr/local/libexec/cloud-platform-network-services`: `b69f41cd1c66000da239f39c09a46681afd5098a311065adf76b3c7aae35b9a3`;
- `/etc/systemd/system/cloud-platform-network-services.service`: `c8297e4e88572a9fee9393960f7896e1ba27d9650f5643d595388878f059a57b`;
- `/etc/sysctl.d/90-cloud-platform-network-forwarding.conf`: `a2a00688b6f566d94ad43cebd13da2f4abcec76815b9fce11dab36b137be0c39`.

Estado operacional verificado:

- `cloud-platform-network-services.service`: `active` + `enabled` e não failed;
- helper `cloud-platform-network-services check`: `PASS`;
- base `cloud-platform-network-enforcement check`: `PASS`;
- IPv4 forwarding: `1`;
- IPv6 all forwarding: `0`;
- listeners públicos gerenciados nas portas 53/3128/2375/2376: ausentes.

Superfície privada observada:

- `cp00000001` → `10.240.1.1/24`, linkdown sem endpoint anexado;
- `cp00000002` → `10.240.2.1/24`, UP;
- `cp00000003` → `10.240.3.1/24`, UP;
- `cpeg0001` → `10.240.254.1/24`, UP;
- rotas locais `10.240.1.0/24`, `10.240.2.0/24`, `10.240.3.0/24` e `10.240.254.0/24` presentes.

No postverify, o runtime esperado do F1.2c contabilizou containers `4`, images `2`, volumes `0` e custom networks `4`.

## Interpretação e boundaries

Este resultado prova a recuperação F1.2c no NODE-01 para o candidato exato acima. Não prova nem autoriza:

- convergência de `systemd-networkd` / `wait-online`;
- reboot ou atualização de kernel/pacotes;
- mudanças em SSH ou `authorized_keys`;
- G2-B real write;
- promoção para produção externa;
- qualquer novo reapply F1.2c sem novo gate humano.

A autorização usada foi one-shot e consumida pelo rollout deste SHA. O próximo diagnóstico da missão é `NETWORK_CONVERGENCE_P2`, inicialmente read-only.
