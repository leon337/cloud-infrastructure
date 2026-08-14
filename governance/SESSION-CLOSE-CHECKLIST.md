# Checklist de Fechamento de Sessão

Antes de mudar de chat ou encerrar uma sessão relevante:

## Auditoria de Delta

- [ ] Registrei fatos novos no inventário?
- [ ] Registrei decisões novas em `decisions/`?
- [ ] Registrei findings/erros/testes em `findings/`?
- [ ] Registrei autorizações de LEANDRO ainda ativas?
- [ ] Registrei mudanças executadas e validações?
- [ ] Registrei testes inválidos e por que foram descartados?
- [ ] Registrei aprendizado relevante no tutorial/glossário?
- [ ] Atualizei runbook/recovery quando surgiu novo caminho de operação?
- [ ] Criei/atualizei registro em `history/`?
- [ ] Atualizei roadmap se o estado de fase mudou?
- [ ] Atualizei `state/current.yaml`?
- [ ] Atualizei `CHECKPOINT.md` por último?

## Consistência

- [ ] Consultei HEAD real antes de escrever?
- [ ] Não sobrescrevi mudanças de outra IA?
- [ ] Não há proposta marcada como decisão?
- [ ] Não há fato volátil apresentado como eterno?
- [ ] Não há secrets reais?
- [ ] Não há placeholders em dados operacionais não secretos já conhecidos sem motivo?

## Handoff

- [ ] O próximo passo é exato e executável?
- [ ] LOCAL e REMOTO estão explicitamente diferenciados?
- [ ] Gates/autorização estão claros?
- [ ] Um novo agente saberá por que o projeto existe?
- [ ] Um novo agente saberá onde começou, onde parou e o que vem depois?
- [ ] Se houver troca de chat, foi planejado teste de continuidade?

Se algum item crítico falhar, não declarar checkpoint concluído.