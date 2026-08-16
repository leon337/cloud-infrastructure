# DEC-003 — Cloud Workstation como próxima grande entrega

Status: **IMPLEMENTED — objetivo entregue em 15/08/2026**.

## Contexto

As limitações do computador local tornam a estação gráfica remota uma necessidade operacional, não um objetivo eventual.

## Decisão

Assim que forem validados acesso administrativo, recovery e segurança mínima necessária, a próxima grande entrega será a Cloud Workstation gráfica. Ela precede Docker, observabilidade e a plataforma ampla de serviços.

## Critério de conclusão

Desktop visível não basta. LEANDRO deverá testar navegador, VS Code, terminal e gerenciador de arquivos; múltiplas janelas; copiar/colar; resolução; estabilidade; reconexão; latência percebida e consumo de recursos.

A etapa somente termina após HUMAN_GATE de LEANDRO confirmando produtividade real.

## Resultado

LEANDRO autorizou execução e validação end-to-end. A Cloud Workstation passou nos critérios técnicos e funcionais; a arquitetura resultante está em `DEC-004`.

## Consequências

- a fase gráfica deixa de ser `DEFERRED`;
- arquitetura, protocolo, exposição e instalação continuam sujeitos a análise e gates próprios;
- serviços futuros devem coexistir sem comprometer segurança ou recursos da workstation;
- esta decisão atualiza a prioridade definida em `DEC-002`, sem abandonar o modelo híbrido nem introduzir dependência de nested virtualization.
