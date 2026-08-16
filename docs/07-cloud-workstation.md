# 07 — Cloud Workstation

Status: **DONE — FUNCTIONAL_AND_VALIDATED em 15/08/2026**.

## Arquitetura implementada

```text
Linux Mint local
  └─ SSH/publickey → VPS:22
       └─ túnel local 127.0.0.1:13389 → VPS 127.0.0.1:3389
            └─ XRDP/xorgxrdp → XFCE/LightDM
```

O XRDP não escuta em interface pública e não possui regra UFW. O certificado XRDP foi aceito somente dentro do túnel SSH autenticado; esta exceção não equivale a expor RDP diretamente à Internet.

## Componentes

- XFCE 4 + `xfce4-goodies`;
- LightDM;
- XRDP + xorgxrdp, com `xrdp` no grupo `ssl-cert`;
- Firefox 153.0.4 em pacote DEB oficial Mozilla;
- VS Code 1.133.0 do repositório oficial Microsoft;
- XFCE Terminal;
- Thunar;
- Git.

O Firefox Snap foi removido depois de falhar dentro do cgroup da sessão XRDP; a versão DEB oficial funcionou.

## Validação de produto

| Critério | Resultado |
|---|---|
| Desktop e login gráfico | PASS |
| Navegador e acesso web real | PASS |
| VS Code e abertura de projeto Git | PASS |
| Terminal gráfico e terminal integrado | PASS |
| Gerenciador de arquivos | PASS |
| Clipboard local → remoto e remoto → local | PASS |
| Múltiplas janelas e controles de janela | PASS |
| Resolução dinâmica | PASS — 1100×700 e 1280×720 |
| Desconexão/reconexão | PASS |
| Persistência de sessão | PASS |
| Logout/login | PASS |
| Funcionamento após reboot | PASS |

## Consumo medido após reboot

- CPU: 8 CPUs lógicas; load average `0.40, 0.21, 0.08` no instante;
- RAM: ~2,2 GiB usados de 23 GiB na validação final com sessão ativa;
- disco raiz: ~7,5 GiB usados de 290 GiB;
- swap: ausente;
- updates pendentes: 0.

## Operação segura

1. abrir um túnel SSH com a chave dedicada;
2. conectar Remmina/FreeRDP a `127.0.0.1:13389`;
3. autenticar no XRDP como `ubuntu`;
4. encerrar o cliente sem logout para preservar a sessão, ou usar logout para iniciar uma sessão limpa.

Detalhes e recovery: `../runbooks/acesso-e-recuperacao.md` e `../recovery/RECOVERY-PLAYBOOK.md`.
