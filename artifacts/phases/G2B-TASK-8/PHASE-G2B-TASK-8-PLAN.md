# G2-B Task 8 — Plano da fase

## Contrato

- missão: `G2-B Task 8`
- classe operacional: `C`
- repositório: `leon337/cloud-infrastructure`
- branch protegida de origem: `codex/control-bridge-g2b`
- SHA de origem reconciliado: `fbef3d407dbd9b7947b6c100a63d098eaebe2b6a`
- branch isolada: `team/g2b-task8-20260822`
- autoridade humana final: `LEANDRO`
- integração final: `MESTRE CENTRAL`
- estado de entrada: `FAILED_ATTEMPT_3`

## Objetivo

Preservar a tentativa 3, determinar com evidência a causa de `apply_g2b exit=2`, corrigir somente uma causa comprovada, validar em ambiente descartável e entregar uma frente auditável sem executar escrita G2-B real no NODE-01 e sem iniciar Tasks 9/10.

## Escopo

1. Reconciliar GitHub vivo.
2. Preservar evidência da tentativa 3.
3. Reconstruir comando, ambiente, SHA, stdout/stderr disponível e transições de estágio.
4. Aplicar CAF.
5. Alterar código funcional somente se a causa estiver comprovada.
6. Validar apenas em boundary descartável.
7. Gerar PRF e checkpoint para auditoria central.

## Fora de escopo

- `main`;
- `mcf/mission-001-control-bridge-g1`;
- reescrita de `codex/control-bridge-g2b`;
- arquitetura ou modelo de segurança do Control Bridge;
- shell/root arbitrário;
- escrita G2-B real no NODE-01;
- Tasks 9/10;
- merge final;
- HUMAN_GATE.

## Critérios de aceite

Task 8 somente poderia receber PASS com lifecycle descartável reproduzível, permissões restritas, operação aceita e proibida comprovadas, rollback/revoke/status coerentes, testes aplicáveis verdes, ausência de shell/root arbitrário, cleanup tratado e evidência vinculada a SHA exato.

## Estratégia de investigação

`CAPTURAR → CLASSIFICAR → VERIFICAR EFEITO → CORRIGIR → VALIDAR → RETORNAR AO OBJETIVO`

Regra de parada: se a causa não puder ser determinada com segurança, registrar `BLOCKED` e não alterar código funcional por hipótese.
