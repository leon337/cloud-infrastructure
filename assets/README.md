# Assets

Os ativos visuais são separados por natureza probatória.

## Evidências operacionais reais

`tutorial/ssh/` contém screenshots sanitizados do terminal local produzidos durante a auditoria e a Missão 2/2B de 15/08/2026:

- `01-preparacao-autenticacao-local.png` — preparação da autenticação SSH;
- `02-autenticacao-validada.png` — canal root validado;
- `03-preparacao-validacao-ubuntu.png` — comando de teste da conta `ubuntu`;
- `04-login-ubuntu-nao-validado.png` — autenticação por chave não concluída e fallback para senha;
- `05-auditoria-fase-b-concluida.png` — fechamento visual da coleta.
- `06-preparacao-diagnostico-read-only-ubuntu.png` — preparação da tentativa diagnóstica com a chave antiga, antes de qualquer credencial;
- `07-preparacao-nova-chave-ubuntu.png` — preparação da geração da nova chave dedicada, antes da nova passphrase;
- `08-preparacao-acesso-root-missao-2b.png` — preparação da validação root, antes da senha;
- `09-preparacao-instalacao-chave-ubuntu.png` — pré-condições e barreira operacional antes da instalação;
- `10-preparacao-diagnostico-root-read-only.png` — preparação sanitizada do diagnóstico root.

Essas imagens não exibem senha, passphrase, chave privada, token ou clipboard com secret. Não existe captura local final adequada da instalação ou do login validado; nenhuma evidência foi fabricada para preencher essa ausência.

## Imagens conceituais

`concepts/cloud-workstation/` contém dois infográficos sobre a visão da Cloud Workstation. Eles foram encontrados na raiz do clone com nomes de exportação `ChatGPT Image ...`, revisados visualmente em 15/08/2026 e movidos para esta categoria:

- `01-visao-geral-cloud-infrastructure-workstation.png`;
- `02-estacao-de-trabalho-na-nuvem.png`.

São ilustrações, não screenshots da VPS nem evidência de implementação. A origem exata do prompt, modelo gerador e autoria não pôde ser comprovada apenas pelos arquivos; essa limitação de provenance fica registrada.
