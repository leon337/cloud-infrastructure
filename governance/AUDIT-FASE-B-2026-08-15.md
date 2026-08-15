# Auditoria Fase B — reconciliação de 15/08/2026

Status: **AUDITORIA CONCLUÍDA; RECONCILIAÇÃO DOCUMENTAL EXECUTADA; SEM NOVA CONEXÃO À VPS**.

## Matriz documentação × VPS real × correção

| Tema | Documentação anterior | VPS real em 15/08 | Correção documental |
|---|---|---|---|
| Fase atual | inventário/primeiros passos APT em arquivos diferentes | inventário e APT já concluídos; auditoria completa | F1 definida como acesso/recovery/segurança mínima |
| Conta `ubuntu` | existência e sudo, SSH pendente | chave compatível, login atual não concluído, senha bloqueada | estado explícito como não validado; `FND-SSH-003` |
| SSH | root/keepalive validados, risco pouco descrito | root e senha permitidos; ataques automatizados volumosos | `FND-SSH-002` e fotografia de segurança |
| Firewall | pendente | UFW inativo; nenhuma regra guest observada | fato registrado; provedor permanece não confirmado |
| LXD | grupo observado sem estado operacional consolidado | 0 instâncias; daemon ativado e recuperado; socket ativo | `FND-LXD-001`, `FND-AUDIT-001` e runbook |
| Atualizações | cinco Krb5 adiados por phasing | quadro permanece igual pelos índices locais de 14/08 | preservar fato e idade dos índices |
| Recovery/backup | VNC/Rescue conhecidos; estratégia futura | nenhum backup guest comum; recursos do provedor não revalidados | remover falsa atualidade e marcar `UNCONFIRMED` |
| Cloud Workstation | `DEFERRED` depois de serviços | nenhuma GUI testável instalada | prioridade `PRIORITY_PLANNED` após pré-requisitos; DEC-003 |
| Cloud-init | não consolidado | `degraded done`, chaves depreciadas, sem erros listados | `FND-CLOUDINIT-001` |
| CPU | observação genérica | relato de Spec rstack overflow | `FND-CPU-001`, sem conclusão prematura |

## Fatos que deixaram de ser verdadeiros

- a Fase 0 ou Etapa 0.5 não está em andamento;
- `apt update` não é o próximo passo;
- inspeção básica da conta `ubuntu` não é o próximo passo;
- Cloud Workstation não está mais `DEFERRED`;
- VNC/Rescue e recursos do provedor não podem ser descritos como atualmente validados apenas pela evidência histórica.

## Pontos não confirmados

- causa da falha atual de autenticação por chave de `ubuntu`;
- legitimidade individual dos logins aceitos observados;
- firewall, VNC, Rescue, snapshots e backups do provedor;
- explorabilidade/mitigação efetiva da observação de CPU;
- arquitetura definitiva da Cloud Workstation.

## Ponto recomendado de implementação

Após revisão desta reconciliação e novo HUMAN_GATE, executar somente um diagnóstico mínimo da autenticação SSH por chave de `ubuntu`. Depois validar sudo, privilégio LXD e recovery; só então decidir hardening mínimo. A Cloud Workstation é a próxima grande entrega quando esses pré-requisitos estiverem comprovados.

