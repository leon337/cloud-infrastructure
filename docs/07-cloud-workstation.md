# 07 — Cloud Workstation

Status: **PRIORITY_PLANNED — próxima grande entrega após acesso administrativo, recovery e segurança mínima**.

## Intenção

A VPS deve servir como computador remoto gráfico de trabalho por causa das limitações do computador local: navegador, arquivos, VS Code, terminal e ferramentas acessíveis a partir do Linux Mint físico.

Desktop e serviços coexistirão no Ubuntu; os serviços não ficam “dentro” do desktop. O projeto não dependerá de nested virtualization sem revalidação explícita do provedor.

## Ainda precisa de decisão

- ambiente gráfico;
- protocolo remoto e criptografia;
- exposição de rede e isolamento;
- consumo máximo aceitável;
- política de sessão sempre ativa;
- coexistência com workloads futuros e eventual necessidade de segunda VPS.

## Pré-requisitos

- acesso administrativo alternativo validado;
- recovery proporcional validado;
- segurança mínima necessária definida e aplicada com gates próprios;
- recursos e impacto avaliados.

## Validação de produtividade obrigatória

A etapa não termina quando o desktop apenas aparece. LEANDRO deverá testar:

- navegador, VS Code, terminal e gerenciador de arquivos;
- múltiplas janelas e copiar/colar;
- resolução e ergonomia;
- estabilidade e reconexão;
- latência percebida;
- consumo de CPU, RAM e disco.

Somente um HUMAN_GATE de LEANDRO confirmando que consegue trabalhar efetivamente conclui a etapa.

Decisão canônica: `decisions/DEC-003-cloud-workstation-prioridade-operacional.md`.
