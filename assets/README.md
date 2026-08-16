# Assets

Os ativos visuais são separados por natureza probatória.

## Evidências SSH

`tutorial/ssh/` preserva a linha histórica de autenticação, auditoria e criação da nova chave. As imagens `01` a `10` versionadas foram revisadas e não exibem secrets.

Os cinco arquivos locais `06-preparacao-diagnostico-read-only-ubuntu_000.png` a `_004.png` continuam não rastreados e fora do escopo; não foram apagados, renomeados nem incluídos.

## Evidências da Cloud Workstation

`tutorial/cloud-workstation/`:

- `01-vnc-recovery-console.png` — console out-of-band VNC revalidado;
- `02-primeiro-desktop-xfce.png` — primeira sessão XFCE funcional;
- `03-multiplas-janelas-thunar-vscode.png` — Thunar e VS Code em sessão com múltiplas janelas;
- `04-vscode-terminal-integrado.png` — projeto Git e terminal integrado;
- `05-firefox-navegacao-real.png` — Firefox carregando `example.com`;
- `06-reconexao-sessao-persistida.png` — navegador restaurado após reconexão.

As capturas foram inspecionadas visualmente e não mostram senha, passphrase, chave privada, token, 2FA ou clipboard secreto.

## Imagens conceituais

`concepts/cloud-workstation/` contém dois infográficos, não evidência operacional. A provenance exata da geração não pôde ser comprovada apenas pelos arquivos.
