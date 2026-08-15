# 04 — Plano Mestre

Este documento consolida o programa de capacidades. Fases futuras continuam provisórias até HUMAN_GATE específico.

## FASE 0 — Orientação e Inventário — DONE

Arquitetura, acesso inicial e inventário foram concluídos e aprovados em 14/08/2026. A fotografia foi revalidada por auditoria read-only em 15/08/2026.

## FASE 1 — Acesso administrativo, recovery e segurança mínima — IN_PROGRESS

- baseline APT: concluída sem forçar phased updates;
- validar acesso SSH atual da conta `ubuntu` por chave — **CONCLUÍDO em 15/08/2026**;
- revisar sudo e privilégio potencialmente equivalente a root via LXD;
- validar caminho de recovery proporcional;
- definir segurança mínima de SSH e firewall sem lockout;
- validar a alternativa administrativa antes de mudar root/senha — **CONCLUÍDO para o acesso; root/senha ainda preservado até os demais pré-requisitos**.

A Missão 2/2B criou uma nova chave ED25519 dedicada, adicionou sua chave pública sem remover a anterior e validou o login atual de `ubuntu` exclusivamente por `publickey`. Root/senha continua validado, temporário e preservado; UFW permanece inativo; ataques automatizados continuam confirmados; recovery independente/provedor não foi validado.

Próximo micro-passo recomendado, sujeito a novo HUMAN_GATE: revisão read-only de sudo e do privilégio potencialmente equivalente a root via LXD. Depois permanecem a validação de recovery proporcional e a definição de segurança mínima de SSH/firewall sem lockout.

## FASE 2 — Cloud Workstation gráfica — PRIORITY_PLANNED

Esta é a próxima grande entrega assim que os pré-requisitos mínimos da FASE 1 forem validados.

- decidir desktop e protocolo remoto;
- definir exposição, criptografia e recovery;
- instalar em micro-passos autorizados;
- testar navegador, VS Code, terminal e gerenciador de arquivos;
- testar múltiplas janelas, copiar/colar, resolução, estabilidade, reconexão e latência;
- medir consumo de CPU, RAM e disco;
- concluir somente após HUMAN_GATE de LEANDRO confirmando produtividade real.

## FASE 3 — Desenvolvimento remoto e estabilização — PROVISIONAL

VS Code Remote SSH quando aplicável, Git, terminal persistente, transferência/sincronização, builds remotos e recuperação da sessão gráfica.

## FASE 4 — Rede, armazenamento e manutenção — PROVISIONAL

Firewall do provedor e Ubuntu, portas, prevenção de lockout, DNS, layout de armazenamento e política recorrente de updates/logs/reboots. Alterações de disco somente após inventário e HUMAN_GATE.

## FASE 5 — Backup, snapshots e recovery — PROVISIONAL

Distinguir snapshot de backup, criar cópia independente, testar restauração e completar o Recovery Playbook. O recovery mínimo necessário ao hardening não deve esperar esta fase ampla.

## FASE 6 — Docker e Compose — PROVISIONAL

Ensinar e implantar containers, imagens, volumes, redes, portas, persistência, restart policy e logs somente após a base necessária.

## FASE 7 — Observabilidade e operação — PROVISIONAL

Saúde do host, recursos, logs, alertas e monitoramento de serviços.

## FASE 8 — Plataforma de serviços — PROVISIONAL

Reverse proxy, TLS, redes de aplicação, serviços internos e publicação controlada.

## FASE 9 — Workloads do ecossistema — PROVISIONAL

Implantação gradual de MCF, MCPs, APIs, agentes, automações, n8n, dashboards, aplicações e produtos.

## FASE 10 — Autonomia e reconstrução — PROVISIONAL

Runbooks, exercícios e capacidade de reconstrução a partir do repositório.

## Regra de mudança de ordem

A ordem provisória anterior colocava a Cloud Workstation depois de Docker e observabilidade. Ela foi substituída em 15/08/2026 por decisão explícita de LEANDRO, formalizada em `DEC-003`.
