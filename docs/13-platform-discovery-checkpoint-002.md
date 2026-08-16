# 13 — Platform Discovery Checkpoint 002 — Q10–Q12

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua `docs/12-platform-discovery-checkpoint-001.md`, que preserva integralmente as decisões Q1–Q9.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q10 — Estratégia de dados por projeto e sandbox

**Escolha de LEANDRO: C — banco DEV persistente por projeto + bancos temporários por sandbox.**

### Decisão

Cada projeto poderá possuir um banco DEV persistente quando necessário. Missões, testes e agentes devem poder receber bancos temporários isolados, preferencialmente clonados ou reconstruídos a partir de estado conhecido, para permitir experimentação sem comprometer o banco DEV principal.

Estrutura conceitual:

```text
Projeto A
|
+-- Banco DEV persistente
|
+-- Sandbox missão 001
|   +-- banco temporário
|
+-- Sandbox missão 002
|   +-- banco temporário
|
+-- Sandbox teste
    +-- banco temporário
```

Ao destruir um sandbox, seu banco temporário pode ser destruído junto, salvo decisão explícita de preservar evidência ou estado relevante.

### Capacidades desejadas

O futuro Capability Core deverá ser capaz de evoluir para operações como:

- criar banco persistente de projeto;
- criar/clone/reconstruir banco temporário para sandbox;
- executar migrations;
- resetar banco de sandbox;
- fazer backup e restore;
- destruir banco temporário de forma segura;
- fornecer credenciais temporárias e escopadas ao ambiente autorizado.

### Princípios derivados

- isolamento de dados por projeto;
- dados de sandbox são descartáveis por padrão;
- dados DEV importantes são persistentes por decisão explícita;
- experimentos e migrations de agentes não devem comprometer o banco DEV principal;
- a arquitetura deve favorecer portabilidade futura para serviços externos de produção;
- a tecnologia concreta da camada de dados ainda não está congelada.

## Q11 — Estratégia de armazenamento de arquivos

**Escolha de LEANDRO: D — modelo híbrido: Git + filesystem temporário + object storage + volumes persistentes quando necessários.**

### Decisão

A plataforma deve tratar tipos de armazenamento conforme sua finalidade, evitando usar uma única solução para tudo.

Estrutura conceitual:

```text
PROJETO
|
+-- Git
|   +-- código
|   +-- configuração versionável
|   +-- documentação
|   +-- manifests
|
+-- Filesystem temporário
|   +-- workspace do sandbox
|   +-- dependências
|   +-- arquivos temporários
|   +-- execução de builds/testes
|
+-- Object Storage
|   +-- uploads
|   +-- imagens
|   +-- PDFs
|   +-- relatórios
|   +-- artefatos
|   +-- arquivos gerados por agentes
|
+-- Volume persistente
    +-- somente para workloads que realmente exijam filesystem persistente
```

### Princípios derivados

- Git não deve ser usado como depósito genérico de dados e uploads;
- filesystem de sandbox é descartável por padrão;
- object storage é a capacidade preferencial para arquivos persistentes orientados a aplicação;
- volumes persistentes devem existir apenas quando o workload realmente exigir semântica de filesystem;
- storage deve ser isolado e autorizado por projeto;
- credenciais de projeto/sandbox não devem permitir acesso ao storage de outros projetos;
- armazenamento não substitui backup;
- a arquitetura deve favorecer portabilidade futura para object storage/volumes gerenciados em produção;
- a tecnologia concreta de object storage e volumes ainda não está congelada.

### Capacidades desejadas

O futuro Capability Core poderá evoluir para operações como:

- criar storage/bucket escopado por projeto;
- emitir credenciais temporárias e limitadas;
- upload/download/list/delete de objetos conforme política;
- provisionar filesystem temporário de sandbox;
- provisionar volume persistente quando declarado no manifesto;
- anexar/desanexar volumes de forma controlada;
- aplicar quotas por projeto/sandbox;
- integrar storage persistente ao futuro sistema de backup e recovery.

## Q12 — Segredos, tokens e credenciais para agentes e sandboxes

**Escolha de LEANDRO: C — cofre central + credenciais escopadas/temporárias + injeção automática nos sandboxes.**

### Decisão

Segredos não devem ser administrados manualmente como parte normal do fluxo dos agentes, nem versionados em Git. A plataforma deve possuir uma camada central de secrets/identity capaz de resolver credenciais em tempo de execução e fornecê-las apenas ao projeto, missão e sandbox autorizados.

O manifesto poderá declarar **que tipo de segredo ou acesso é necessário**, mas nunca conter o valor real do segredo.

Exemplo conceitual:

```text
Manifesto
  -> declara: database_credentials, object_storage_credentials, github_read_access
  -> Capability Core valida projeto/missão/sandbox
  -> Secret/Identity Layer resolve as credenciais
  -> credenciais são injetadas no sandbox
  -> missão termina
  -> credenciais temporárias são revogadas quando suportado
```

### Limites de autoridade

Uma missão do Projeto A poderá receber acesso apenas aos recursos necessários do Projeto A. Não deve receber por padrão:

- credenciais de outros projetos;
- credenciais administrativas da VPS;
- chaves SSH privadas da infraestrutura;
- credenciais do provedor Contabo;
- segredos globais;
- tokens permanentes quando uma credencial temporária ou escopada for possível.

Princípio: **o agente deve receber capacidade de usar um recurso dentro do escopo autorizado, e não autoridade permanente sobre o recurso.**

### Capacidades desejadas

O futuro Capability Core / Secret & Identity Layer deverá poder evoluir para operações como:

- solicitar acesso a banco, storage ou serviço conforme política;
- injetar secrets no ambiente em runtime;
- emitir credenciais temporárias quando suportado;
- revogar credenciais ao término da missão;
- rotacionar segredos de maneira controlada;
- auditar qual projeto/missão/sandbox recebeu qual classe de acesso;
- impedir que valores reais de secrets sejam versionados ou expostos em manifests, logs e evidências.

### Direção futura

A arquitetura deve ser compatível com evolução para identidade dinâmica/Zero Trust mais completa, mas isso não será exigido integralmente no primeiro release.

Princípios derivados:

- secrets centralizados;
- acesso mínimo necessário;
- escopo por projeto/missão/sandbox;
- credenciais temporárias preferidas quando tecnicamente viáveis;
- injeção automática no runtime;
- zero secrets no Git;
- separação entre declaração de necessidade e valor do segredo;
- mais autonomia deve ser conquistada por melhor controle de identidade e escopo, não por entrega de credenciais administrativas amplas.

## Estado das decisões

```text
Q1  = C
Q2  = C
Q3  = C
Q4  = C
Q5  = D
Q6  = C
Q7  = C
Q8  = C
Q9  = C
Q10 = C
Q11 = D
Q12 = C
```

## Próximo passo

**DISCOVERY_Q13**.

A Discovery continua. Nenhuma escolha tecnológica final de banco, runtime, object storage, volumes, reverse proxy, secret manager, CI/CD, observabilidade, Hermes/OpenClaw/Freebuff/OpenHands ou desenho detalhado de MCP deve ser antecipada antes das decisões correspondentes.
