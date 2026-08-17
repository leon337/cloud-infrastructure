# Decision Log

Decisões canônicas da infraestrutura.

- `DEC-000-repositorio-isolado.md` — infraestrutura separada do MCF.
- `DEC-001-protocolo-universal-continuidade.md` — PUC v1.0.
- `DEC-002-arquitetura-hibrida-cloud-workstation.md` — preservar modelo híbrido e não depender de nested virtualization; prioridade gráfica atualizada por DEC-003.
- `DEC-003-cloud-workstation-prioridade-operacional.md` — prioridade gráfica aprovada e entregue.
- `DEC-004-xfce-xrdp-sobre-tunel-ssh.md` — XFCE/XRDP restrito a loopback e acessado por túnel SSH.
- `DEC-005-foundation-declarativa-e-accounting.md` — Ansible/schema e slices F1.1 sem limites cegos.
- `DEC-006-technology-mapping-v1.md` — baseline tecnológica e implantação controlada por lifecycle.
- `DEC-007-docker-runtime-boundary.md` — Docker CE pinado, vazio e root-only; workloads bloqueados por F1.2c.

Novas decisões devem registrar contexto, alternativas, escolha, motivo, consequências, status e possibilidade de revisão.
