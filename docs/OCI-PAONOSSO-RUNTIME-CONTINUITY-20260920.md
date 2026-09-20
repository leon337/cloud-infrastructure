# OCI + PÃO NOSSO — checkpoint de continuidade

Mission ID: MCF-20260920-OCI-PAONOSSO-RUNTIME-001
Observed: 2026-09-20T06:19:47-03:00
Canonical repo: leon337/cloud-infrastructure
Branch: mission/oci-paonosso-runtime-20260920

## Objetivo

Provisionar um runtime Oracle OCI Always Free para o backend de IA/WhatsApp do
PÃO NOSSO sem interromper o caminho de produção atualmente funcional.

## Estado reconciliado

- Conta Oracle Cloud criada e tenancy ativa.
- Home region observada: Brazil Southeast (Vinhedo) / sa-vinhedo-1.
- Console identifica a conta como Free Trial com fallback para recursos Always Free.
- Configuração escolhida e revisada no wizard:
  - Canonical Ubuntu 24.04 Minimal aarch64;
  - VM.Standard.A1.Flex;
  - selo Always Free-eligible;
  - 2 OCPU / 12 GB RAM / 2 Gbps;
  - boot volume padrão observado em ~46,6 GB;
  - chave pública oci_paonosso.pub carregada; chave privada permanece só no notebook.
- Networking do wizard preparado para nova VCN + subnet pública.
- Review exibiu Public IPv4 address: No; IP público efêmero deve ser atribuído
  após a instância existir, se o wizard não fizer isso.
- A criação foi submetida e retornou:
  Out of capacity for shape VM.Standard.A1.Flex in availability domain AD-1.
- Nenhuma VM foi criada.
- Nenhum endpoint Meta/WhatsApp foi alterado.

## Blocker atual

OCI_A1_AD1_OUT_OF_CAPACITY.

Este blocker é de capacidade do provider. Não é falha do projeto, da imagem,
da chave SSH ou do dimensionamento escolhido.

## Próximo passo exato

1. Reabrir/reutilizar o wizard OCI.
2. Manter A1 Flex em 2 OCPU / 12 GB e selo Always Free.
3. Tentar outro AD somente se o OCI oferecer um AD elegível; caso contrário,
   repetir mais tarde.
4. Não aceitar downgrade ou recurso pago por inferência.
5. Depois de RUNNING:
   - atribuir IPv4 público efêmero;
   - validar SSH com a chave local ~/.ssh/oci_paonosso;
   - aplicar hardening mínimo;
   - implantar o runtime do PÃO NOSSO;
   - validar health/webhook end-to-end;
   - só então considerar mudança do callback Meta.

## Regras de continuidade

- Não commitar segredos, tokens, chaves privadas, IDs sensíveis ou dados de cartão.
- Não alterar o runtime de produção enquanto o OCI não estiver validado.
- Não interpretar Free Trial como autorização para recurso pago.
- Toda retomada deve começar lendo state/oci-paonosso-runtime.yaml.
