# 36 — Platform Discovery Checkpoint 025 — Q37

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q36.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q37 — Ingress público, previews, DNS e TLS

**Escolha de LEANDRO: C — namespace DNS administrado pela plataforma + Preview Gateway + URLs automáticas + TLS automático + separação rígida DEV/PROD.**

### Decisão

Serviços permanecem privados por padrão. Quando um projeto, missão ou sandbox precisar de exposição autorizada, a publicação deverá acontecer por uma camada de Ingress/Preview Gateway administrada pela plataforma, sem exigir que agentes exponham diretamente portas do host, gerenciem certificados ou configurem manualmente reverse proxy/DNS.

A plataforma deverá oferecer um namespace de nomes para DEV/previews e atribuir URLs automaticamente a serviços autorizados. A sintaxe concreta dos domínios e a tecnologia de DNS/reverse proxy/TLS ainda não estão congeladas.

Classes conceituais de exposição:

- `INTERNAL`: sem exposição pública;
- `PROTECTED_PREVIEW`: HTTPS com controle de acesso;
- `PUBLIC_PREVIEW`: HTTPS público quando explicitamente autorizado;
- `PRODUCTION`: namespace/domínio separado e promoção sujeita às regras de HUMAN_GATE já definidas.

Princípios derivados:

- aplicações recebem nomes/identidades; não expõem portas do host diretamente;
- preview é automático, temporário e pertencente a tenant/projeto/missão/sandbox;
- TLS deve ser automático para toda exposição autorizada;
- DEV/previews e produção não compartilham o mesmo significado de autoridade;
- domínio customizado de cliente e promoção para produção são operações sensíveis e seguem políticas de autoridade;
- a camada de ingresso deve continuar compatível com a evolução single-node first → multi-node ready;
- tecnologia concreta de DNS, ingress/reverse proxy e ACME/TLS será escolhida no technology mapping.

### Princípio canônico

`PLATFORM_MANAGED_DNS_NAMESPACE_PREVIEW_GATEWAY_AUTOMATIC_URLS_TLS_STRICT_DEV_PROD_SEPARATION`

## Estado das decisões

`Q37 = C`

## Próximo passo

**DISCOVERY_Q38**.