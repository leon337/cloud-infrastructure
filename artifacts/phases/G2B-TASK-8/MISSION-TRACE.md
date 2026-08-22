# Mission Trace — G2-B Task 8

## Fluxo

1. `MESTRE` abriu a missão e fixou os boundaries.
2. `EMILY` reconciliou GitHub vivo, PR #11, SHA e evidências da tentativa 3.
3. `SOFIA` delimitou harness, role, playbook, environment e hipóteses estruturais.
4. `RICARDO` classificou o incidente e verificou que nenhuma causa funcional estava comprovada.
5. `CARMEM` materializou o PRF e o checkpoint.
6. `AUGUSTO` valida a rastreabilidade cronológica antes do gate interno.
7. `LÉO` recebe o pacote para decisão operacional de bloqueio/retorno.
8. `MESTRE` transfere a frente ao MESTRE CENTRAL sem integração.

## CAF observado

### Capturar
- terminal attempt3 em PR #11;
- runs read-only existentes;
- harness, playbook, role e configuração do candidato.

### Classificar
- falha no estágio `apply_g2b`;
- uma de duas invocações idênticas de Ansible retornou não-zero;
- diagnóstico de task/causa ausente.

### Verificar efeito
- zero marcadores de aceite;
- identidade pós-apply não validada;
- inner cleanup passou;
- outer QEMU permaneceu viva no último snapshot conhecido.

### Corrigir
- não executado: causa funcional não comprovada.

### Validar
- não existe post-fix lifecycle;
- Task 8 permanece FAIL/BLOCKED.

### Retornar ao objetivo
- impossível sem recuperar ou reproduzir diagnóstico em boundary descartável com saída preservada.

## Handoffs

`MESTRE → EMILY → SOFIA → RICARDO → CARMEM → AUGUSTO → LÉO → MESTRE`

Todos os handoffs desta frente são execução por papéis na mesma sessão; não representam processos cognitivos independentes simultâneos.
