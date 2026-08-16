# DEC-005 — Foundation declarativa e slices apenas com accounting

Status: **ACCEPTED — DESIRED STATE IMPLEMENTED, VPS APPLY PENDING**

## Contexto

Q9/Q27 exigem manifesto declarativo, automação idempotente e drift controlado.
Q25 exige reserva/quotas, mas o nó compartilha recursos com a Cloud Workstation e
ainda não possui medição de workloads. O primeiro incremento não pode introduzir
uma instalação ampla nem limites cegos que provoquem OOM.

## Alternativas

1. shell scripts imperativos;
2. Nix/NixOS como remodelagem integral;
3. OpenTofu para configuração interna do host;
4. Ansible agentless + YAML/JSON Schema + systemd/cgroup v2 nativos.

## Decisão

Usar Ansible Core 2.21.3, fixado em ambiente isolado do controller, somente com
módulos builtin em F1.1. Manifests usam JSON Schema 2020-12 e rejeitam campos
desconhecidos/secrets literais.

Criar `cloud-platform.slice` e `cloud-workloads.slice` apenas com accounting e
pesos relativos. Não usar `Delegate=`, `MemoryMax=` ou `CPUQuota=` até existir
baseline medida. Criar somente namespaces raiz e runtime directories; serviços
futuros usarão os diretórios gerenciados por systemd em suas próprias units.

## Consequências

- não há daemon Ansible na VPS;
- sudo continua autenticado e a senha não entra na automação;
- primeira aplicação requer interação humana, mas reconcile posterior é
  determinístico;
- check mode não é rollback transacional; rollback é playbook fail-closed;
- hard limits serão um slice posterior, com carga e invariância da Workstation;
- shell permanece permitido dentro de tasks apenas quando módulo seguro não
  existir e com idempotência/saída sanitizada explícitas.

## Rollback

O playbook remove somente objetos F1.1 e aborta se diretórios persistentes não
estiverem vazios. Arquivos preexistentes sem marker nunca são adotados. SSH, UFW,
XRDP, pacotes e dados atuais não fazem parte do delta.

## Revisão

Revisar se houver segundo provider/OS, necessidade forte de infra provisionada
externamente ou falha comprovada de idempotência/portabilidade do Ansible.
