# 30 — Platform Discovery Checkpoint 019 — Q31

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q30.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q31 — Papel da Cloud Workstation na plataforma

**Escolha de LEANDRO: C — serviços headless totalmente independentes + Cloud Workstation opcional como cockpit e ambiente de trabalho humano.**

### Decisão

A Cloud Workstation não deve ser dependência operacional da plataforma. Capability Core, Workflow Engine, gateways, bancos, observabilidade, backups, workers e demais serviços permanentes devem continuar funcionando independentemente da sessão gráfica, login XFCE, XRDP ou presença de LEANDRO.

A Cloud Workstation permanece útil como interface humana de intervenção, diagnóstico e desenvolvimento, incluindo navegador, VS Code, terminal, Freebuff, TriView e acesso a dashboards, porém deve consumir APIs e interfaces da plataforma em vez de hospedar o estado autoritativo ou processos essenciais.

### Arquitetura conceitual

```text
                   VPS / NODE-01
                        |
        +---------------+---------------+
        |                               |
        v                               v
PLATFORM SERVICES                CLOUD WORKSTATION
    headless                       interface humana
        |                               |
Capability Core                    Firefox
Workflow Engine                    VS Code
Gateways                           Freebuff
Workers                            Terminal / TriView
Databases
Observability
```

### Princípios derivados

- fechar XRDP, fazer logout do XFCE ou interromper a sessão gráfica não deve parar a plataforma;
- serviços permanentes devem ser executados como serviços headless independentes da sessão de usuário;
- a Workstation é uma interface humana opcional, não uma fonte de verdade;
- contas técnicas e identidade de serviços devem ser separadas da sessão gráfica quando aplicável;
- futuros execution nodes podem operar sem interface gráfica;
- a Cloud Workstation pode permanecer no NODE-01 sem se tornar dependência do Capability Core;
- Freebuff permanece ferramenta humana/interativa, coerente com Q30;
- TriView pode ser acessado pela Workstation, mas seu papel continua de cockpit e não de autoridade canônica.

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
Q13 = C
Q14 = C
Q15 = C
Q16 = C
Q17 = C
Q18 = C
Q19 = C
Q20 = C
Q21 = C
Q22 = C
Q23 = C
Q24 = C
Q25 = C
Q26 = C
Q27 = C
Q28 = D
Q29 = C
Q30 = C
Q31 = C
```

## Próximo passo

**DISCOVERY_Q32**.

A próxima decisão deve definir a estratégia de uso de modelos de IA externos e, quando viável, locais, incluindo roteamento por custo/capacidade, isolamento de credenciais e ausência de dependência de um único provedor/modelo.